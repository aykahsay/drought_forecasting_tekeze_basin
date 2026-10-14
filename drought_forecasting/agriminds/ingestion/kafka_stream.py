"""
AI-DREWS Apache Kafka Event Streaming Engine
=============================================
High-throughput, real-time event-driven streaming architecture for:
  1. `aidrews.telemetry.weather`: Automated Weather Station (AWS) and rain gauge telemetry.
  2. `aidrews.ground.kebele_reports`: Kebele Development Agent (DA) crop, pasture & soil moisture observations.
  3. `aidrews.hydrology.water_points`: Spring discharge, borehole depth, and micro-dam level events.
  4. `aidrews.satellite.tiles`: NRT satellite indices (NDVI, NDWI, surface water anomalies).
  5. `aidrews.alerts.woreda_advisory`: Real-time probabilistic early warning advisories.

Features:
  - Dual-mode architecture: Uses `kafka-python` (`KafkaProducer`/`KafkaConsumer`) when a real Kafka cluster
    is connected, with an automatic in-memory streaming ring buffer (`InMemoryKafkaBroker`) fallback.
  - Sub-millisecond latency for dashboard and alert dispatch.
  - Continuous telemetry metrics: throughput (msg/s), topic message counts, active consumers.
"""

from __future__ import annotations
import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("agriminds.kafka")

# Standard AI-DREWS Kafka Topics
TOPIC_WEATHER_TELEMETRY = "aidrews.telemetry.weather"
TOPIC_KEBELE_REPORTS = "aidrews.ground.kebele_reports"
TOPIC_HYDROLOGY_WATER_POINTS = "aidrews.hydrology.water_points"
TOPIC_SATELLITE_TILES = "aidrews.satellite.tiles"
TOPIC_WOREDA_ALERTS = "aidrews.alerts.woreda_advisory"
TOPIC_OCEAN_TELECONNECTIONS = "aidrews.climate.ocean_indices"
TOPIC_CROP_CLIMATE = "aidrews.crop.climate_records"
TOPIC_SPATIAL_NETCDF = "aidrews.spatiotemporal.netcdf"

ALL_TOPICS = [
    TOPIC_WEATHER_TELEMETRY,
    TOPIC_KEBELE_REPORTS,
    TOPIC_HYDROLOGY_WATER_POINTS,
    TOPIC_SATELLITE_TILES,
    TOPIC_WOREDA_ALERTS,
    TOPIC_OCEAN_TELECONNECTIONS,
    TOPIC_CROP_CLIMATE,
    TOPIC_SPATIAL_NETCDF,
]


class KafkaMessage:
    """Standardized event packet across AI-DREWS stream topics."""

    def __init__(
        self,
        topic: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
        timestamp: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        offset: int = 0,
        partition: int = 0,
    ):
        self.topic = topic
        self.payload = payload
        self.key = key or payload.get("location_id") or payload.get("woreda_id") or "global"
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.headers = headers or {"source": "ai-drews-node", "version": "1.0"}
        self.offset = offset
        self.partition = partition

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "key": self.key,
            "partition": self.partition,
            "offset": self.offset,
            "timestamp": self.timestamp,
            "headers": self.headers,
            "payload": self.payload,
            "value": self.payload,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class InMemoryKafkaBroker:
    """
    High-performance in-memory ring-buffer broker.
    Provides Kafka topic semantics, message retention, subscriber fan-out,
    and throughput metrics when an external Kafka daemon is offline or in development.
    """

    def __init__(self, max_retention_per_topic: int = 1000):
        self.max_retention = max_retention_per_topic
        self._buffers: Dict[str, deque] = {t: deque(maxlen=max_retention_per_topic) for t in ALL_TOPICS}
        self._subscribers: Dict[str, List[Callable[[KafkaMessage], None]]] = {t: [] for t in ALL_TOPICS}
        self._lock = threading.Lock()
        self.total_produced = 0
        self.total_consumed = 0
        self._topic_produced_counts: Dict[str, int] = {t: 0 for t in ALL_TOPICS}
        self._topic_offsets: Dict[str, int] = {t: 0 for t in ALL_TOPICS}
        # Time-windowed rolling counter: stores (second_bucket_int, count)
        self._rolling_window_sec = 60
        self._rolling_counts: deque = deque()  # stores [timestamp_sec_int, count]

    def _record_event_count(self) -> None:
        now_sec = int(time.time())
        if self._rolling_counts and self._rolling_counts[-1][0] == now_sec:
            self._rolling_counts[-1][1] += 1
        else:
            self._rolling_counts.append([now_sec, 1])
        # Purge buckets older than window
        cutoff = now_sec - self._rolling_window_sec
        while self._rolling_counts and self._rolling_counts[0][0] <= cutoff:
            self._rolling_counts.popleft()

    def publish(self, message: KafkaMessage) -> None:
        with self._lock:
            topic = message.topic
            if topic not in self._buffers:
                self._buffers[topic] = deque(maxlen=self.max_retention)
                self._subscribers[topic] = []
                self._topic_produced_counts[topic] = 0
                self._topic_offsets[topic] = 0

            # Assign per-topic local partition and offset
            message.offset = self._topic_offsets[topic]
            message.partition = 0
            self._topic_offsets[topic] += 1
            self._topic_produced_counts[topic] += 1

            self._buffers[topic].append(message)
            self.total_produced += 1
            self._record_event_count()

            callbacks = list(self._subscribers[topic])

        for cb in callbacks:
            try:
                cb(message)
                with self._lock:
                    self.total_consumed += 1
            except Exception as e:
                logger.error(f"Error in Kafka consumer callback for {message.topic}: {e}")

    def subscribe(self, topic: str, callback: Callable[[KafkaMessage], None]) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
                self._buffers[topic] = deque(maxlen=self.max_retention)
                self._topic_produced_counts[topic] = 0
                self._topic_offsets[topic] = 0
            self._subscribers[topic].append(callback)

    def get_recent(self, topic: str, limit: int = 20) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        with self._lock:
            if topic not in self._buffers:
                return []
            items = list(self._buffers[topic])[-limit:]
            return [m.to_dict() for m in reversed(items)]

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            now_sec = int(time.time())
            cutoff = now_sec - self._rolling_window_sec
            recent_msgs = sum(cnt for ts, cnt in self._rolling_counts if ts > cutoff)
            msg_rate = round(recent_msgs / float(self._rolling_window_sec), 2)

            buffered_counts = {t: len(buf) for t, buf in self._buffers.items()}
            total_topic_traffic = dict(self._topic_produced_counts)
            consumer_counts = {t: len(subs) for t, subs in self._subscribers.items()}

            return {
                "broker_type": "embedded_in_memory_kafka",
                "status": "OPERATIONAL",
                "total_produced": self.total_produced,
                "total_consumed": self.total_consumed,
                "messages_per_second": msg_rate,
                "buffered_message_counts": buffered_counts,
                "total_topic_traffic": total_topic_traffic,
                "active_subscribers": consumer_counts,
                "measurement_window_seconds": self._rolling_window_sec,
            }


class KafkaStreamManager:
    """
    Central Kafka Stream Manager for AI-DREWS.
    Handles publishing, subscription, and monitoring with seamless cluster/fallback handling.
    """

    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or "localhost:9092"
        self.embedded_broker = InMemoryKafkaBroker()
        self.use_real_kafka = False
        self._real_producer = None
        self._delivery_stats = {"queued": 0, "delivered": 0, "failed": 0}
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3
        self._connection_state = "INITIALIZING"
        self._init_connection()

    def _init_connection(self) -> None:
        """Attempt to connect to a real Apache Kafka cluster with fast socket probe."""
        import socket
        try:
            host, port_str = self.bootstrap_servers.split(":", 1) if ":" in self.bootstrap_servers else (self.bootstrap_servers, "9092")
            port = int(port_str)
            s = socket.create_connection((host, port), timeout=0.05)
            s.close()

            from kafka import KafkaProducer  # type: ignore
            self._real_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                request_timeout_ms=1000,
                max_block_ms=1000,
                acks="all",
            )
            self.use_real_kafka = True
            self._connection_state = "CONNECTED"
            self._consecutive_failures = 0
            logger.info(f"Connected to Apache Kafka cluster at {self.bootstrap_servers}")
        except Exception as e:
            self.use_real_kafka = False
            self._real_producer = None
            self._connection_state = "FALLBACK_EMBEDDED"
            logger.info(
                f"External Kafka cluster at {self.bootstrap_servers} offline ({e}). "
                "AI-DREWS embedded high-throughput event broker active with zero downtime."
            )

    def _handle_send_error(self, ex: Exception) -> None:
        self._delivery_stats["failed"] += 1
        self._consecutive_failures += 1
        logger.warning(f"Kafka asynchronous delivery failure ({ex}). Failure count: {self._consecutive_failures}")
        if self._consecutive_failures >= self._max_consecutive_failures:
            logger.error(f"Exceeded max consecutive failures ({self._max_consecutive_failures}). Tripping circuit breaker to FALLBACK_EMBEDDED.")
            self.use_real_kafka = False
            self._connection_state = "FALLBACK_EMBEDDED"

    def _handle_send_success(self, metadata: Any, msg: KafkaMessage) -> None:
        self._delivery_stats["delivered"] += 1
        self._consecutive_failures = 0
        # Capture actual broker delivery metadata
        if hasattr(metadata, "topic"):
            msg.topic = metadata.topic
        if hasattr(metadata, "partition"):
            msg.partition = metadata.partition
        if hasattr(metadata, "offset"):
            msg.offset = metadata.offset

    def publish_event(
        self,
        topic: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Publish an event to a Kafka stream topic with delivery state tracking."""
        msg = KafkaMessage(topic=topic, payload=payload, key=key, headers=headers)
        delivery_status = "PUBLISHED_LOCAL"

        if self.use_real_kafka and self._real_producer:
            try:
                self._delivery_stats["queued"] += 1
                future = self._real_producer.send(topic, key=msg.key, value=msg.to_dict())
                future.add_callback(lambda meta: self._handle_send_success(meta, msg))
                future.add_errback(lambda ex: self._handle_send_error(ex))
                delivery_status = "QUEUED_EXTERNAL"
            except Exception as e:
                self._handle_send_error(e)
                delivery_status = "EXTERNAL_WRITE_FAILED_FALLBACK"

            # Always mirror to embedded broker so in-memory subscribers and dashboard get real-time feed
            self.embedded_broker.publish(msg)
        else:
            self.embedded_broker.publish(msg)

        return {
            "status": delivery_status,
            "topic": topic,
            "key": msg.key,
            "offset": msg.offset,
            "partition": msg.partition,
            "timestamp": msg.timestamp,
            "connection_state": self._connection_state,
            "broker": "real_kafka_cluster" if self.use_real_kafka else "embedded_kafka_bus",
        }

    def stream_records(
        self,
        topic: str,
        records: List[Dict[str, Any]],
        key_field: Optional[str] = None,
        throttle_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Stream a list of event dictionaries in real time to a Kafka topic.
        Calculates throughput and tracks streaming offsets.
        """
        t0 = time.time()
        published_count = 0
        first_offset = None
        last_offset = None

        for rec in records:
            key = str(rec.get(key_field)) if key_field and key_field in rec else None
            res = self.publish_event(topic=topic, payload=rec, key=key)
            if first_offset is None:
                first_offset = res.get("offset", 0)
            last_offset = res.get("offset", 0)
            published_count += 1
            if throttle_seconds > 0:
                time.sleep(throttle_seconds)

        elapsed = max(0.001, time.time() - t0)
        rate = round(published_count / elapsed, 1)

        return {
            "topic": topic,
            "published_count": published_count,
            "elapsed_seconds": round(elapsed, 3),
            "throughput_msg_per_sec": rate,
            "first_offset": first_offset,
            "last_offset": last_offset,
            "broker_mode": "real_kafka_cluster" if self.use_real_kafka else "embedded_kafka_bus",
        }

    def subscribe(self, topic: str, callback: Callable[[KafkaMessage], None]) -> None:
        """Register a subscriber callback for a topic."""
        self.embedded_broker.subscribe(topic, callback)

    def get_topic_stream(self, topic: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent events from a topic."""
        return self.embedded_broker.get_recent(topic, limit=limit)

    def get_cluster_status(self) -> Dict[str, Any]:
        """Return connectivity, throughput, and topic health."""
        metrics = self.embedded_broker.get_metrics()
        return {
            "kafka_enabled": True,
            "connected_to_external_broker": self.use_real_kafka,
            "bootstrap_servers": self.bootstrap_servers,
            "broker_mode": "APACHE_KAFKA_CLUSTER" if self.use_real_kafka else "EMBEDDED_STREAM_BROKER",
            "topics_available": ALL_TOPICS,
            "metrics": metrics,
        }


# Singleton instance
_stream_manager: Optional[KafkaStreamManager] = None


def get_stream_manager() -> KafkaStreamManager:
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = KafkaStreamManager()
    return _stream_manager
