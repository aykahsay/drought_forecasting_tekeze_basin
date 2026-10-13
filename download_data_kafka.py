"""
AI-DREWS Real-Time Kafka Data Downloader & Streamer
===================================================
Executes real-time data acquisition and Kafka streaming across all datasets
before training the machine learning models.

Usage:
    python download_data_kafka.py
    python download_data_kafka.py --throttle-ms 2
    python download_data_kafka.py --days-weather 30
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root and drought_forecasting directory to Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "drought_forecasting"))

from agriminds.ingestion.realtime_kafka_pipeline import RealtimeKafkaDataPipeline
from agriminds.ingestion.kafka_stream import get_stream_manager


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="AI-DREWS Real-Time Kafka Data Downloader & Streaming Ingestion")
    parser.add_argument("--throttle-ms", type=int, default=0, help="Per-record throttle delay in ms to visualize real-time stream")
    parser.add_argument("--days-weather", type=int, default=14, help="Days of sub-hourly AWS weather station history to stream")
    parser.add_argument("--output-json", type=str, default=None, help="Optional path to save JSON ingestion summary")
    args = parser.parse_args()

    print("=" * 80)
    print("[*] AGRI-MINDS / AI-DREWS REAL-TIME KAFKA DATA INGESTION ENGINE")
    print("=" * 80)
    print("Connecting to Kafka Event Broker...")

    mgr = get_stream_manager()
    status = mgr.get_cluster_status()
    print(f"Broker Mode:      {status['broker_mode']}")
    print(f"Bootstrap Server: {status['bootstrap_servers']}")
    print(f"Topics Tracked:   {len(status['topics_available'])}")
    print("-" * 80)

    pipeline = RealtimeKafkaDataPipeline(stream_manager=mgr)

    t0 = time.time()
    summary = pipeline.run_full_pipeline()
    t_total = time.time() - t0

    print("\n" + "=" * 80)
    print("[+] REAL-TIME KAFKA INGESTION COMPLETE")
    print("=" * 80)
    print(f"Total Events Streamed:     {summary['total_events_published']}")
    print(f"Total Events Consumed:     {summary['total_events_consumed']}")
    print(f"Overall Streaming Rate:    {summary['overall_throughput_msg_per_sec']} msg/second")
    print(f"Data Validation Pass Rate: {summary['validation_pass_rate']}")
    print(f"Database Records Written:  {summary['database_records_written']}")
    print(f"Hot Tempo Buffer Records:  {summary['tempo_buffer_rows']}")
    print(f"Execution Duration:        {round(t_total, 2)} seconds")
    print("-" * 80)
    print("[*] DATASETS VERIFIED & READY FOR TRAINING:")
    for ds_name, ds_info in summary["datasets_ready_for_training"].items():
        print(f"  - {ds_name.upper():<25} -> {ds_info.get('status')}")
    print("=" * 80)

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"Ingestion report saved to {out_p}")


if __name__ == "__main__":
    main()
