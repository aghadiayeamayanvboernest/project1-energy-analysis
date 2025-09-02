#!/usr/bin/env python3

import logging
import os

# Adjusting path to import from src
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.data_fetcher import fetch_historical_data
from src.data_processor import process_all_data
from src.analysis import generate_quality_report

# --- Logging Setup ---
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
log_file_path = os.path.join(LOGS_DIR, 'pipeline.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),
        logging.StreamHandler()
    ]
)

def run_pipeline(historical=True):
    """
    Runs the full data pipeline.
    
    Args:
        historical (bool): If True, runs the historical data fetch.
                           Otherwise, runs the daily fetch.
    """
    logging.info("========== Starting Pipeline Run ==========")
    
    if historical:
        logging.info("--- Running in HISTORICAL mode ---")
        fetch_historical_data(days=90)
    
    logging.info("--- Processing Raw Data ---")
    process_all_data()
    
    logging.info("--- Generating Data Quality Report ---")
    generate_quality_report()
    
    logging.info("=========== Pipeline Run Finished ===========")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the data pipeline.")
    parser.add_argument("--historical", action='store_true', help="Run the pipeline to fetch 90 days of historical data.")
    args = parser.parse_args()
    
    run_pipeline(historical=True)
