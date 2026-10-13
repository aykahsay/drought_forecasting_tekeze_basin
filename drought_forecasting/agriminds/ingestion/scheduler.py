"""
Automated ERA5T Ingestion Scheduler (Requirement §12 / §19)
===========================================================
Uses APScheduler to run ERA5T ingestion on a configurable cron schedule.

Pipeline (Requirement §19):
    CDS API
       ↓
    ERA5T
       ↓
    Check latest available date
       ↓
    Compare with database (idempotency)
       ↓
    Download only missing data
       ↓
    Validate
       ↓
    Store
       ↓
    Generate features
       ↓
    Update drought model (future)
"""
import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from agriminds.climate.sources.era5t import ERA5TSource
from agriminds.config import get_settings
from agriminds.db.models import ERA5TIngestionLog, IngestionStatus, get_session
from agriminds.ingestion.continual_learning_pipeline import ContinualLearningPipeline


MAX_RETRY_ATTEMPTS = 3


class IngestionScheduler:
    """
    Schedules and manages automated ERA5T data ingestion.

    Features:
      - Configurable cron schedule (default: daily at 06:00 UTC)
      - Idempotency: detects already-ingested dates
      - Retry on failure (up to MAX_RETRY_ATTEMPTS)
      - Ingestion logs exposed via API
      - Recovers after interruption (replays missing dates on startup)
    """

    def __init__(self):
        self.source = ERA5TSource()
        self.settings = get_settings()
        self._scheduler: Optional[BackgroundScheduler] = None
        self.cl_pipeline = ContinualLearningPipeline()

    def start(self):
        """Start the background ingestion scheduler."""
        if not self.source.is_available():
            logger.warning(
                "ERA5T source not available (CDS API key not configured). "
                "Scheduler will not start. Set CDS_API_KEY in .env to enable."
            )
            return

        self._scheduler = BackgroundScheduler(timezone="UTC")

        trigger = CronTrigger.from_crontab(self.settings.ingestion_cron)
        self._scheduler.add_job(
            self._run_daily_ingestion,
            trigger=trigger,
            id="era5t_daily_ingest",
            name="ERA5T Daily Ingestion",
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1-hour misfire window
        )

        # Continual Learning: Hot to Cold Storage Flush (Daily at 2 AM)
        self._scheduler.add_job(
            self.cl_pipeline.flush_hot_to_cold_storage,
            trigger=CronTrigger(hour="2", minute="0"),
            id="cl_cold_flush",
            name="Hot to Cold Storage Flush",
            replace_existing=True,
        )

        # Continual Learning: Warm Fine-Tuning (Every 2 Months on the 1st)
        self._scheduler.add_job(
            self.cl_pipeline.execute_warm_fine_tuning,
            trigger=CronTrigger(day="1", month="*/2", hour="3", minute="0"),
            id="cl_warm_fine_tune",
            name="Bi-Monthly Bayesian Prior Fine-Tuning",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info(
            f"ERA5T ingestion scheduler started. "
            f"Schedule: {self.settings.ingestion_cron} UTC. "
            f"Continual Learning Pipeline (Hot-Warm-Cold) active."
        )

        # Catch up on any missing dates asynchronously in a background thread so server starts immediately
        import threading
        threading.Thread(target=self._catchup_missing, kwargs={"days_back": 7}, daemon=True).start()

    def stop(self):
        """Gracefully stop the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("Ingestion scheduler stopped.")

    def _run_daily_ingestion(self):
        """Main ingestion job — ingest yesterday's ERA5T data."""
        target = date.today() - timedelta(days=5)  # ~5-day ERA5T latency
        logger.info(f"Starting scheduled ERA5T ingestion for {target}")
        self._ingest_with_retry(target)

    def _catchup_missing(self, days_back: int = 30):
        """
        On startup, check the last N days and ingest any missing dates.
        Ensures data continuity after interruptions.
        """
        logger.info(f"Checking for missing ERA5T data in the last {days_back} days …")
        db = get_session()
        try:
            today = date.today()
            latest_available = today - timedelta(days=5)  # ERA5T latency

            for days_ago in range(days_back, 0, -1):
                target = latest_available - timedelta(days=days_ago)
                already_done = (
                    db.query(ERA5TIngestionLog)
                    .filter(
                        ERA5TIngestionLog.target_date == target.isoformat(),
                        ERA5TIngestionLog.status == IngestionStatus.COMPLETE,
                    )
                    .first()
                )
                if not already_done:
                    logger.info(f"Catching up missing date: {target}")
                    self._ingest_with_retry(target)
        finally:
            db.close()

    def _ingest_with_retry(self, target: date):
        """
        Attempt ingestion with up to MAX_RETRY_ATTEMPTS retries.
        Each retry is logged in ERA5TIngestionLog.
        """
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            result = self.source.ingest(target)
            if result.success:
                return result

            if attempt < MAX_RETRY_ATTEMPTS:
                wait = 60 * attempt  # Progressive back-off
                logger.warning(
                    f"Ingestion failed for {target} (attempt {attempt}/{MAX_RETRY_ATTEMPTS}). "
                    f"Retrying in {wait}s …"
                )
                import time
                time.sleep(wait)
            else:
                logger.error(
                    f"Ingestion permanently failed for {target} "
                    f"after {MAX_RETRY_ATTEMPTS} attempts. "
                    f"Error: {result.error}"
                )
                self._update_retry_count(target, attempt)

        return result

    def _update_retry_count(self, target: date, count: int):
        db = get_session()
        try:
            log = (
                db.query(ERA5TIngestionLog)
                .filter(ERA5TIngestionLog.target_date == target.isoformat())
                .order_by(ERA5TIngestionLog.started_at.desc())
                .first()
            )
            if log:
                log.retry_count = count
                db.commit()
        finally:
            db.close()

    def get_health(self) -> dict:
        """
        Return ingestion health summary for the API endpoint.
        Satisfies requirement §19 (expose ingestion health via API).
        """
        db = get_session()
        try:
            recent_logs = (
                db.query(ERA5TIngestionLog)
                .order_by(ERA5TIngestionLog.started_at.desc())
                .limit(30)
                .all()
            )

            total = len(recent_logs)
            completed = sum(1 for l in recent_logs if l.status == IngestionStatus.COMPLETE)
            failed = sum(1 for l in recent_logs if l.status == IngestionStatus.FAILED)
            skipped = sum(1 for l in recent_logs if l.status == IngestionStatus.SKIPPED)

            latest = (
                db.query(ERA5TIngestionLog)
                .filter(ERA5TIngestionLog.status == IngestionStatus.COMPLETE)
                .order_by(ERA5TIngestionLog.target_date.desc())
                .first()
            )

            return {
                "scheduler_running": self._scheduler is not None and self._scheduler.running if self._scheduler else False,
                "ingestion_schedule": self.settings.ingestion_cron,
                "era5t_latency": "~5 days",
                "latest_ingested_date": latest.target_date if latest else None,
                "last_ingestion_at": latest.completed_at.isoformat() if latest and latest.completed_at else None,
                "recent_30_runs": {
                    "total": total,
                    "completed": completed,
                    "failed": failed,
                    "skipped": skipped,
                    "success_rate": f"{completed/total*100:.1f}%" if total > 0 else "N/A",
                },
                "recent_log": [
                    {
                        "date": l.target_date,
                        "status": l.status.value if l.status else None,
                        "records": l.records_stored,
                        "error": l.error_message,
                        "started_at": l.started_at.isoformat() if l.started_at else None,
                    }
                    for l in recent_logs[:10]
                ],
            }
        finally:
            db.close()


# Singleton scheduler instance
_scheduler_instance: Optional[IngestionScheduler] = None


def get_scheduler() -> IngestionScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = IngestionScheduler()
    return _scheduler_instance
