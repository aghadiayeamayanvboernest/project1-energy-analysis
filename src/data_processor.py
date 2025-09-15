import os
import json
import pandas as pd
import logging
import yaml
import re

# --- Configuration and Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.yaml')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
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

def tenths_c_to_f(temp_in_tenths_c):
    """Converts temperature from tenths of a degree Celsius to Fahrenheit."""
    if temp_in_tenths_c is None:
        return None
    celsius = temp_in_tenths_c / 10.0
    return (celsius * 9/5) + 32

def load_config():
    """Loads the YAML configuration file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {CONFIG_PATH}")
        return None
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return None

def process_noaa_data(file_path):
    """Loads and processes a raw NOAA JSON file into a DataFrame."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Could not read or parse NOAA file {file_path}: {e}")
        return None

    if not data.get('results'):
        logging.warning(f"No 'results' found in NOAA file: {file_path}")
        return pd.DataFrame()

    df = pd.DataFrame(data['results'])
    df['date'] = pd.to_datetime(df['date']).dt.date.astype(str)

    weather_df = df.pivot_table(index='date', columns='datatype', values='value').reset_index()
    weather_df.columns.name = None

    for col in ['TMAX', 'TMIN']:
        if col in weather_df.columns:
            weather_df[f'{col.lower()}_f'] = weather_df[col].apply(tenths_c_to_f)
            weather_df = weather_df.drop(columns=[col])
        else:
            logging.warning(f"Datatype '{col}' not found in {file_path}. Column will be missing.")

    return weather_df

def process_eia_data(file_path):
    """Loads and processes a raw EIA JSON file into a DataFrame."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Could not read or parse EIA file {file_path}: {e}")
        return None

    if not data.get('response', {}).get('data'):
        logging.warning(f"No 'data' found in EIA file: {file_path}")
        return pd.DataFrame()

    df = pd.DataFrame(data['response']['data'])
    
    energy_df = df[(df['type'] == 'D') & (df['timezone'] == 'Eastern')].copy()
    if energy_df.empty:
        logging.warning(f"No 'Demand' data for 'Eastern' timezone found in {file_path}. Trying without timezone filter.")
        energy_df = df[df['type'] == 'D'].copy()
        if not energy_df.empty and energy_df.duplicated(subset=['period']).any():
             energy_df = energy_df.groupby('period').first().reset_index()

    energy_df = energy_df[['period', 'value']]
    energy_df.rename(columns={'period': 'date', 'value': 'energy_mwh'}, inplace=True)
    energy_df['energy_mwh'] = pd.to_numeric(energy_df['energy_mwh'], errors='coerce')
    energy_df['date'] = pd.to_datetime(energy_df['date']).dt.date.astype(str)

    return energy_df

def get_date_range_from_files(raw_files):
    """Extracts the date range string from the first available file."""
    for f in raw_files:
        match = re.search(r'(\d{4}-\d{2}-\d{2}_to_\d{4}-\d{2}-\d{2})', f)
        if match:
            return match.group(1)
    return None

def process_all_data():
    """
    Processes all raw data files, merges them by city,
    and saves them to the processed data directory.
    """
    logging.info("Starting raw data processing.")
    config = load_config()
    if not config or 'cities' not in config:
        logging.error("Could not load cities from config file. Aborting.")
        return

    raw_files = os.listdir(RAW_DATA_DIR)

    for city_config in config['cities']:
        city_name = city_config['name']
        city_name_safe = city_name.replace(' ', '_')
        logging.info(f"Processing data for {city_name}...")

        # Find all files for the current city
        city_files = [f for f in raw_files if city_name_safe in f]
        if not city_files:
            logging.warning(f"No raw data files found for {city_name}. Skipping.")
            continue

        noaa_files = [f for f in city_files if 'noaa' in f]
        eia_files = [f for f in city_files if 'eia' in f]

        if not noaa_files or not eia_files:
            logging.warning(f"Missing NOAA or EIA file for {city_name}. Skipping.")
            continue

        # Process the first available NOAA and EIA files
        noaa_path = os.path.join(RAW_DATA_DIR, noaa_files[0])
        eia_path = os.path.join(RAW_DATA_DIR, eia_files[0])

        noaa_df = process_noaa_data(noaa_path)
        eia_df = process_eia_data(eia_path)

        if noaa_df.empty or eia_df.empty:
            logging.error(f"Data processing failed for {city_name} due to empty or invalid dataframes.")
            continue

        try:
            merged_df = pd.merge(noaa_df, eia_df, on='date', how='inner')
        except Exception as e:
            logging.error(f"Failed to merge data for {city_name}: {e}")
            continue

        merged_df['city'] = city_name
        merged_df['day_of_week'] = pd.to_datetime(merged_df['date']).dt.day_name()

        output_filename = f'{city_name.lower().replace(" ", "_")}_processed.csv'
        output_path = os.path.join(PROCESSED_DATA_DIR, output_filename)
        try:
            merged_df.to_csv(output_path, index=False)
            logging.info(f"Successfully saved processed data for {city_name} to {output_path}")
        except IOError as e:
            logging.error(f"Failed to write processed file for {city_name}: {e}")

    logging.info("Raw data processing complete.")

if __name__ == "__main__":
    process_all_data()