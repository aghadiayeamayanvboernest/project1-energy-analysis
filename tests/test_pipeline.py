
import os
import sys
import pytest

# Adjusting path to import from src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.pipeline import run_pipeline
from src.data_fetcher import load_config # Using data_fetcher's load_config

@pytest.fixture(scope="module")
def pipeline_run():
    """Fixture to run the pipeline once for all tests in this module."""
    run_pipeline(historical=True)

def test_pipeline_creates_processed_files(pipeline_run):
    """Tests if the pipeline creates all expected processed CSV files."""
    config = load_config()
    assert config is not None, "Config could not be loaded for tests."
    
    processed_dir = os.path.join(BASE_DIR, 'data', 'processed')
    cities = [city['name'] for city in config['cities']]
    
    for city_name in cities:
        processed_filename = f'{city_name.lower().replace(" ", "_")}_processed.csv'
        processed_filepath = os.path.join(processed_dir, processed_filename)
        assert os.path.exists(processed_filepath), f"Processed file not found: {processed_filepath}"

def test_pipeline_creates_quality_report(pipeline_run):
    """Tests if the pipeline creates the data quality report."""
    reports_dir = os.path.join(BASE_DIR, 'reports')
    report_filepath = os.path.join(reports_dir, 'data_quality_report.txt')
    assert os.path.exists(report_filepath), f"Data quality report not found: {report_filepath}"
