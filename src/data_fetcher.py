import os
import logging
import time
from datetime import datetime, timedelta
import requests
import yaml
from dotenv import load_dotenv
import json

# --- Configuration and Setup ---

# Determine project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file in the project root
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Configuration paths
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.yaml')
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# --- Logging Setup ---
log_file_path = os.path.join(LOGS_DIR, 'pipeline.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),
        logging.StreamHandler()
    ]
)

# --- API Constants ---
NOAA_API_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
EIA_API_URL = "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/"

# --- Helper Functions ---

def load_config():
    """Loads the YAML configuration file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        config['api']['noaa']['token'] = os.getenv('NOAA_TOKEN')
        config['api']['eia']['api_key'] = os.getenv('EIA_API_KEY')
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {CONFIG_PATH}")
        raise
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise

def retry_request(max_retries=3, delay=5, backoff=2):
    """Decorator for retrying API requests with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    retries += 1
                    wait = delay * (backoff ** (retries - 1))
                    logging.warning(
                        f"Request failed: {e}. Retrying in {wait:.2f} seconds... ({retries}/{max_retries})"
                    )
                    if retries == max_retries:
                        logging.error("Max retries reached. Request failed.")
                        raise
                    time.sleep(wait)
        return wrapper
    return decorator

@retry_request()
def make_api_request(url, headers=None, params=None):
    """Makes a generic API request and returns the response."""
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def save_data(data, source, city_name, date_str):
    """Saves fetched data to a JSON file."""
    filename = f"{source}_{city_name.replace(' ', '_')}_{date_str}.json"
    filepath = os.path.join(RAW_DATA_DIR, filename)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Successfully saved data to {filepath}")
    except IOError as e:
        logging.error(f"Failed to save data to {filepath}: {e}")

# --- API Fetcher Functions ---

def fetch_noaa_data(station_id, start_date, end_date, token):
    """Fetches weather data (TMAX, TMIN) from NOAA CDO API."""
    headers = {'token': token}
    params = {
        'datasetid': 'GHCND',
        'stationid': station_id,
        'startdate': start_date,
        'enddate': end_date,
        'datatypeid': 'TMAX,TMIN',
        'limit': 1000
    }
    logging.info(f"Fetching NOAA data for station {station_id} from {start_date} to {end_date}")
    return make_api_request(NOAA_API_URL, headers=headers, params=params)

def fetch_eia_data(region_code, start_date, end_date, api_key):
    """Fetches daily electricity demand data from EIA API."""
    params = {
        "api_key": api_key,
        "frequency": "daily",
        "data[0]": "value",
        "facets[respondent][]": region_code,
        "start": start_date,
        "end": end_date,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "offset": 0,
        "length": 5000
    }
    logging.info(f"Fetching EIA data for region {region_code} from {start_date} to {end_date}")
    response = requests.get(EIA_API_URL, params=params)
    response.raise_for_status()
    return response.json()

# --- Main Orchestration ---

def fetch_data_for_range(start_date_str, end_date_str):
    """Orchestrates fetching data for a given date range."""
    config = load_config()
    if not config:
        return

    noaa_token = config.get('api', {}).get('noaa', {}).get('token')
    eia_api_key = config.get('api', {}).get('eia', {}).get('api_key')

    if not noaa_token or 'YOUR_TOKEN_HERE' in noaa_token:
        logging.error("NOAA token not configured properly. Aborting.")
        return
    if not eia_api_key or 'YOUR_API_KEY_HERE' in eia_api_key:
        logging.error("EIA API key not configured properly. Aborting.")
        return

    for city in config['cities']:
        city_name = city['name']
        noaa_station = city['noaa_station_id']
        eia_region = city['eia_region_code']
        date_str_for_filename = f"{start_date_str}_to_{end_date_str}"

        try:
            noaa_data = fetch_noaa_data(noaa_station, start_date_str, end_date_str, noaa_token)
            if noaa_data.get('results'):
                save_data(noaa_data, 'noaa', city_name, date_str_for_filename)
            else:
                logging.warning(f"No NOAA data returned for {city_name}. Response: {noaa_data}")
        except Exception as e:
            logging.error(f"Failed to fetch/save NOAA data for {city_name}: {e}", exc_info=True)

        try:
            eia_data = fetch_eia_data(eia_region, start_date_str, end_date_str, eia_api_key)
            if eia_data.get('response', {}).get('data'):
                 save_data(eia_data, 'eia', city_name, date_str_for_filename)
            else:
                logging.warning(f"No EIA data returned for {city_name}. Response: {eia_data}")
        except Exception as e:
            logging.error(f"Failed to fetch/save EIA data for {city_name}: {e}", exc_info=True)

def fetch_historical_data(days=90):
    """Fetches data for the last N days."""
    logging.info(f"Starting historical data fetch for the last {days} days.")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    fetch_data_for_range(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    logging.info("Historical data fetch complete.")

def fetch_two_weeks_ahead():
    """Fetches data for the next two weeks."""
    logging.info("Starting data fetch for two weeks ahead.")
    start_date = datetime.now()
    end_date = start_date + timedelta(weeks=2)
    fetch_data_for_range(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    logging.info("Two weeks ahead data fetch complete.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch historical energy and weather data.")
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format. Defaults to 90 days ago."
    )
    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format. Defaults to today."
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of past days to fetch data for. Overrides start/end dates if provided."
    )
    parser.add_argument(
        "--two-weeks-ahead",
        action="store_true",
        help="Fetch data for the next two weeks."
    )
    args = parser.parse_args()

    if args.days:
        fetch_historical_data(days=args.days)
    elif args.two_weeks_ahead:
        fetch_two_weeks_ahead()
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        start_date_str = args.start_date if args.start_date else start_date.strftime('%Y-%m-%d')
        end_date_str = args.end_date if args.end_date else end_date.strftime('%Y-%m-%d')

        fetch_data_for_range(start_date_str, end_date_str)