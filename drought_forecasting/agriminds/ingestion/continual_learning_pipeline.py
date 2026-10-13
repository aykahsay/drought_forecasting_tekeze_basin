"""
Hot-Warm-Cold 2-Month Data Storage & Continual Learning Pipeline
================================================================
This script orchestrates the operational data flow for AI-DREWS:
1. HOT (Tempo Storage): In-memory / fast SQLite buffer for the trailing 60 days of data. Used by the dashboard for instant Bayesian Inference.
2. WARM (Fine-Tuning): Scheduled job that runs every 60 days to recalculate the Bayesian priors and likelihoods based on recent climate shifts.
3. COLD (Historical Archive): Flushes data older than 60 days to long-term storage (Parquet/SQLite) to keep the Hot buffer fast.
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from pathlib import Path

# Setup paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
COLD_STORAGE_FILE = DATA_DIR / "historical_archive.parquet"
HOT_STORAGE_DB = DATA_DIR / "tempo_buffer.db"

class ContinualLearningPipeline:
    def __init__(self):
        # Initialize Hot Storage (SQLite for fast dashboard reads)
        self.conn = sqlite3.connect(HOT_STORAGE_DB)
        self._init_hot_storage()

    def _init_hot_storage(self):
        """Creates the tempo buffer table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                woreda_id TEXT,
                date TEXT,
                spi_3 REAL,
                soil_moisture_percentile REAL,
                rainfall_anomaly REAL,
                nino34 REAL,
                iod REAL
            )
        ''')
        self.conn.commit()

    def ingest_to_hot_storage(self, observations: list[dict]):
        """
        [HOT] Ingests daily/weekly satellite and weather station data into the tempo buffer.
        Called by data fetchers (e.g., ERA5, NOAA APIs).
        """
        logger.info(f"Ingesting {len(observations)} new records into Hot Storage (Tempo Buffer)...")
        df = pd.DataFrame(observations)
        df.to_sql('recent_observations', self.conn, if_exists='append', index=False)
        logger.success("Ingestion complete. Dashboard Bayesian engine now using latest evidence.")

    def execute_warm_fine_tuning(self):
        """
        [WARM] Triggered every 2 months. Pulls the last 60 days of data to recalibrate
        the Bayesian Priors in the forecasting engine.
        """
        logger.info("Executing Bi-Monthly WARM Fine-Tuning Pipeline...")
        
        sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        query = f"SELECT * FROM recent_observations WHERE date >= '{sixty_days_ago}'"
        
        recent_df = pd.read_sql(query, self.conn)
        
        if recent_df.empty:
            logger.warning("No recent data found for fine-tuning. Skipping.")
            return

        logger.info(f"Pulled {len(recent_df)} records from the 2-month window.")
        logger.info("Recalculating Bayesian Priors based on recent climate shifts...")
        
        # In production, this would update the prior probabilities in ablation.py
        new_prior = recent_df['spi_3'].mean() < -1.0 # Simplified logic: if average SPI is drought, increase prior
        prior_adjustment = 0.45 if new_prior else 0.35
        
        logger.success(f"Bayesian Priors recalibrated. New baseline P1: {prior_adjustment}")
        return prior_adjustment

    def flush_hot_to_cold_storage(self):
        """
        [COLD] Moves data older than 60 days out of the SQLite tempo buffer and into 
        the historical Parquet archive to keep the dashboard lightning fast.
        """
        logger.info("Flushing old data from Hot to Cold Storage...")
        
        sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # Read old data
        query = f"SELECT * FROM recent_observations WHERE date < '{sixty_days_ago}'"
        old_df = pd.read_sql(query, self.conn)
        
        if old_df.empty:
            logger.info("No data older than 60 days to flush.")
            return

        # Append to Parquet Cold Storage
        if COLD_STORAGE_FILE.exists():
            archive_df = pd.read_parquet(COLD_STORAGE_FILE)
            combined_df = pd.concat([archive_df, old_df], ignore_index=True)
        else:
            combined_df = old_df
            
        combined_df.to_parquet(COLD_STORAGE_FILE, index=False)
        logger.success(f"Archived {len(old_df)} records to Cold Storage ({COLD_STORAGE_FILE.name}).")
        
        # Delete old data from Hot Storage
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM recent_observations WHERE date < '{sixty_days_ago}'")
        self.conn.commit()
        logger.success("Tempo Buffer flushed. Hot Storage optimized.")

if __name__ == "__main__":
    # Example Simulation of the Cron Job
    pipeline = ContinualLearningPipeline()
    
    # 1. Simulate daily ingestion
    dummy_data = [
        {"woreda_id": "sinan", "date": datetime.now().strftime('%Y-%m-%d'), "spi_3": -1.2, "soil_moisture_percentile": 22.0, "rainfall_anomaly": -15.0, "nino34": 0.8, "iod": -0.2},
        {"woreda_id": "hawzen", "date": (datetime.now() - timedelta(days=65)).strftime('%Y-%m-%d'), "spi_3": -1.8, "soil_moisture_percentile": 15.0, "rainfall_anomaly": -25.0, "nino34": 0.8, "iod": -0.2}
    ]
    pipeline.ingest_to_hot_storage(dummy_data)
    
    # 2. Run bi-monthly fine-tuning (Warm)
    pipeline.execute_warm_fine_tuning()
    
    # 3. Flush old data (Cold)
    pipeline.flush_hot_to_cold_storage()
