#!/usr/bin/env python3

import logging
import os

# Adjusting path to import from src
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import subprocess
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

def run_pipeline(start_date=None, end_date=None, days=None, two_weeks_ahead=False):
    """
    Runs the full data pipeline.

    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format. Defaults to None.
        end_date (str, optional): End date in YYYY-MM-DD format. Defaults to None.
        days (int, optional): Number of past days to fetch data for. Defaults to None.
        two_weeks_ahead (bool, optional): If True, fetches data for the next two weeks. Defaults to False.
    """
    logging.info("========== Starting Pipeline Run ==========")

    # Construct the command to run the data_fetcher script
    fetcher_path = os.path.join(BASE_DIR, 'src', 'data_fetcher.py')
    command = ["python", fetcher_path]

    if two_weeks_ahead:
        logging.info("--- Running in TWO WEEKS AHEAD mode ---")
        command.append("--two-weeks-ahead")
    elif days:
        logging.info(f"--- Running in HISTORICAL mode for {days} days ---")
        command.extend(["--days", str(days)])
    elif start_date and end_date:
        logging.info(f"--- Running in DATE RANGE mode from {start_date} to {end_date} ---")
        command.extend(["--start-date", start_date, "--end-date", end_date])
    else:
        logging.info("--- Running in DEFAULT mode (last 90 days) ---")
        command.extend(["--days", "90"])

    # Run the data fetcher
    subprocess.run(command, check=True)

    logging.info("--- Processing Raw Data ---")
    process_all_data()

    logging.info("--- Generating Data Quality Report ---")
    generate_quality_report()

    logging.info("=========== Pipeline Run Finished ===========")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the data pipeline.")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format.")
    parser.add_argument("--days", type=int, help="Number of past days to fetch data for.")
    parser.add_argument("--two-weeks-ahead", action='store_true', help="Fetch data for the next two weeks.")
    args = parser.parse_args()

    run_pipeline(start_date=args.start_date, end_date=args.end_date, days=args.days, two_weeks_ahead=args.two_weeks_ahead)
