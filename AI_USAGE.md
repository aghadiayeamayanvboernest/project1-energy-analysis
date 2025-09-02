# AI Usage Documentation

This document tracks the usage of AI assistance in this project.  It details the AI tools used, effective prompts, identified and fixed AI mistakes, time saved estimates, and learnings from AI-generated code.  The goal is to provide transparency and demonstrate problem-solving skills.

## AI Tools Used

*   Gemini
*   GitHub Copilot

## Most Effective Prompts & Outcomes

### Data Fetching Module (`src/data_fetcher.py`)

*   **Prompt:** "I need to create a Python function that fetches weather data from the NOAA API for multiple cities, handles rate limiting, implements exponential backoff for retries, and logs all errors. The function should return a JSON object with consistent data."
    *   **Outcome:** The AI generated a function with retry logic, error handling, and logging. It correctly implemented exponential backoff using the `time.sleep()` function. The function successfully fetched data from the NOAA API and returned a JSON object.
*   **Prompt:** "Now, create a similar function to fetch energy consumption data from the EIA API, handling potential API errors and ensuring consistent data formatting."
    *   **Outcome:** The AI created a function to fetch data from the EIA API, similar to the NOAA function. It included error handling for HTTP status codes and returned a JSON object.

### Data Processing Module (`src/data_processor.py`)

*   **Prompt:** "Write a Python function to clean and transform the raw NOAA and EIA data. This function should handle missing values, convert data types, and merge the datasets based on city and date. The output should be a pandas DataFrame ready for analysis."
    *   **Outcome:** The AI generated a function that handled missing values using imputation, converted data types (e.g., to numeric), and merged the NOAA and EIA datasets based on city and date. The output was a pandas DataFrame.

### Streamlit Dashboard (`dashboards/app.py`)

*   **Prompt:** "Create a Streamlit dashboard with a map showing energy consumption by city. The dashboard should include filters for date range and city selection. Use Plotly for the map visualization."
    *   **Outcome:** The AI generated a basic Streamlit dashboard with a map visualization using Plotly. It included date range and city selection filters.

## AI-Discovered Issues & Fixes

### Issue 1: Inconsistent Data Type Handling in Data Processing

*   **How I discovered the issue:** The initial AI-generated data processing function did not correctly handle cases where the NOAA API returned temperature values as strings instead of numbers. This caused errors during the merging and analysis steps.
*   **What the fix was:** I added explicit type conversion within the data processing function to ensure that temperature values were always treated as numeric.

    ```python
    # filepath: src/data_processor.py
    # ...existing code...
    df['tmax_f'] = pd.to_numeric(df['tmax_f'], errors='coerce')
    df['tmin_f'] = pd.to_numeric(df['tmin_f'], errors='coerce')
    # ...existing code...
    ```

*   **What I learned from debugging it:** I learned the importance of explicitly handling data types, especially when dealing with external APIs that may have inconsistent data formats.

### Issue 2: Incorrect Date Formatting in EIA API Requests

*   **How I discovered the issue:** The EIA API was returning errors because the date format in the API requests was incorrect. The AI had used a different date format than what the API expected.
*   **What the fix was:** I modified the date formatting in the `fetch_eia_data` function to match the EIA API's expected format (`YYYY-MM-DD`).

    ```python
    # filepath: src/data_fetcher.py
    # ...existing code...
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    # ...existing code...
    ```

*   **What I learned from debugging it:** I learned the importance of carefully reading API documentation and ensuring that all requests adhere to the API's specifications.

## Time Saved Estimate (Over Six Weeks)

*   **Task:** Initial project setup and file creation: ~15-20 minutes
*   **Task:** Data fetching module development: ~2-3 hours
*   **Task:** Data processing module development: ~1-2 hours
*   **Task:** Streamlit dashboard creation: ~3-4 hours
*   **Ongoing tasks (debugging, testing, refactoring):** ~10-15 hours
*   **Total Estimated Time Saved (Over Six Weeks):** ~16-24 hours

## Learning from AI-Generated Code

*   The AI was particularly helpful in generating boilerplate code for API requests, error handling, and data transformations.
*   I learned new techniques for implementing exponential backoff and handling rate limiting.
*   Debugging the AI-generated code helped me to better understand the nuances of the NOAA and EIA APIs.
*   I gained experience in identifying and fixing data type inconsistencies and API request formatting errors.
