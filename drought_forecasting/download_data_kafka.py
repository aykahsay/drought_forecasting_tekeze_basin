"""
AI-DREWS Real-Time Kafka Data Downloader & Streamer (Module Runner)
"""
import sys
from pathlib import Path

# Add project root and drought_forecasting directory to Python path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent if CURRENT_DIR.name == "drought_forecasting" else CURRENT_DIR
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(CURRENT_DIR))

from download_data_kafka import main

if __name__ == "__main__":
    main()
