# US Weather + Energy Analysis Pipeline

This project is a data pipeline that fetches, processes, analyzes, and visualizes weather and energy consumption data for major US cities. The goal is to demonstrate a production-ready data pipeline that can provide valuable insights for energy demand forecasting.

## Features

- **Automated Data Fetching**: Daily and historical data fetching from NOAA (weather) and EIA (energy) APIs.
- **Data Processing**: Cleans, transforms, and merges data from different sources.
- **Data Quality Assurance**: Automatically checks for missing values, outliers, and data freshness.
- **In-depth Analysis**: Provides analysis on correlation, seasonal patterns, and weekday/weekend trends.
- **Interactive Dashboard**: A Streamlit dashboard with multiple visualizations to explore the data.

## Directory Structure

```
project1-energy-analysis/
├── README.md                 # This file
├── AI_USAGE.md              # AI assistance documentation
├── pyproject.toml           # Dependencies (using uv)
├── config/
│   └── config.yaml          # API keys, cities list
├── src/
│   ├── data_fetcher.py      # API interaction module
│   ├── data_processor.py    # Cleaning and transformation
│   ├── analysis.py          # Statistical analysis
│   └── pipeline.py          # Main orchestration
├── dashboards/
│   └── app.py               # Streamlit application
├── logs/
│   └── pipeline.log         # Execution logs
├── data/
│   ├── raw/                 # Original API responses
│   └── processed/           # Clean, analysis-ready data
├── tests/
│   └── test_pipeline.py     # Basic unit tests
└── video_link.md            # Link to your presentation
```

## Prerequisites

- Python 3.10+
- `uv` package manager (can be installed with `pip install uv`)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd project1-energy-analysis
    ```

2.  **Set up API Keys:**
    - Create a `.env` file in the project root.
    - Add your NOAA and EIA API keys to the `.env` file as follows:
      ```
      NOAA_TOKEN=YOUR_NOAA_TOKEN_HERE
      EIA_API_KEY=YOUR_EIA_API_KEY_HERE
      ```

3.  **Install Dependencies:**
    - Use `uv` to install the required packages:
      ```bash
      uv pip install -e .[test]
      ```

## Usage

### Running the Pipeline

-   **To fetch 90 days of historical data:**
    ```bash
    python src/pipeline.py --historical
    ```

-   **To fetch the latest daily data:**
    ```bash
    python src/pipeline.py
    ```

### Running the Dashboard

-   To start the Streamlit dashboard, run:
    ```bash
    streamlit run dashboards/app.py
    ```

## Running Tests

-   To run the test suite, use `pytest`:
    ```bash
    pytest
    ```