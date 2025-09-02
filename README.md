# US Weather & Energy Analysis Pipeline

[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv Compatible](https://img.shields.io/badge/Compatible%20with-uv-brightgreen)](https://github.com/astral-sh/uv)

## Overview

This project is a comprehensive data pipeline designed to fetch, process, analyze, and visualize weather and energy consumption data for major US cities. It aims to provide valuable insights into the relationship between weather patterns and energy demand, enabling better energy demand forecasting and resource management. This pipeline is built with production-readiness in mind, emphasizing automation, data quality, and insightful analysis.

## Key Features

*   **Automated Data Acquisition:**
    *   Fetches historical weather data from the NOAA API.
    *   Acquires historical energy consumption data from the EIA API.
*   **Robust Data Processing:**
    *   Cleans, transforms, and merges data from NOAA and EIA.
    *   Handles missing values and outliers to ensure data integrity.
*   **Automated Data Quality Assurance:**
    *   Implements checks for data freshness, completeness, and consistency.
    *   Generates data quality reports to monitor data health.
*   **In-Depth Data Analysis:**
    *   Performs correlation analysis to quantify the relationship between weather and energy consumption.
    *   Identifies seasonal patterns and trends in energy usage.
    *   Analyzes weekday/weekend energy consumption patterns.
*   **Interactive Data Visualization:**
    *   Provides an interactive Streamlit dashboard for exploring the data.
    *   Offers multiple visualizations, including maps, time series charts, scatter plots, and heatmaps.

## Architecture

The pipeline follows a modular architecture, with each component responsible for a specific task:

1.  **Data Fetching:**  `src/data_fetcher.py` retrieves data from the NOAA and EIA APIs.
2.  **Data Processing:** `src/data_processor.py` cleans, transforms, and merges the raw data.
3.  **Data Analysis:** `src/analysis.py` performs statistical analysis and generates insights.
4.  **Pipeline Orchestration:** `src/pipeline.py` orchestrates the entire pipeline, scheduling data fetching, processing, and analysis.
5.  **Dashboard:** `dashboards/app.py` creates an interactive Streamlit dashboard for data exploration.

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

*   Python 3.10+
*   `uv` package manager (recommended for faster dependency resolution and project setup)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd project1-energy-analysis
    ```

2.  **Configure API Keys:**

    *   Create a `.env` file in the project root directory.
    *   Add your NOAA and EIA API keys to the `.env` file:

        ```
        NOAA_TOKEN=YOUR_NOAA_TOKEN_HERE
        EIA_API_KEY=YOUR_EIA_API_KEY_HERE
        ```

        **Note:** It is crucial to keep your API keys secure.  Do not commit the `.env` file to your repository.

3.  **Install Dependencies:**

    *   Use `uv` to install the project dependencies, including testing libraries:

        ```bash
        uv pip install -e .[test]
        ```

## Usage

### Running the Data Pipeline

The `src/pipeline.py` script orchestrates the data fetching, processing, and analysis steps.

*   **To run the pipeline and fetch the latest 90 days of historical data:**

    ```bash
    python src/pipeline.py
    ```

### Running the Streamlit Dashboard

The `dashboards/app.py` script launches the interactive Streamlit dashboard.

*   **To start the Streamlit dashboard:**

    ```bash
    streamlit run dashboards/app.py
    ```

    The dashboard will open in your web browser, allowing you to explore the data and visualizations.

### Running Tests

The `tests/test_pipeline.py` file contains unit tests for the data pipeline.

*   **To run the test suite:**

    ```bash
    pytest
    ```

    This will execute the unit tests and report any failures.

## Contributing

Contributions to this project are welcome! If you find a bug or have an idea for a new feature, please open an issue or submit a pull request.


## Acknowledgements

*   [NOAA](https://www.noaa.gov/) for providing weather data.
*   [EIA](https://www.eia.gov/) for providing energy consumption data.