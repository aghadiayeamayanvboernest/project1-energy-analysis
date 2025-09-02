
import os
import pandas as pd
from datetime import datetime
import logging

# --- Configuration and Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
os.makedirs(REPORTS_DIR, exist_ok=True)
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

def check_missing_values(df):
    """Checks for missing values in the DataFrame."""
    missing_summary = df.isnull().sum()
    missing_percent = (df.isnull().sum() / len(df)) * 100
    missing_df = pd.DataFrame({'missing_count': missing_summary, 'missing_percent': missing_percent})
    return missing_df[missing_df['missing_count'] > 0]

def check_outliers(df):
    """Checks for outliers in temperature and energy data."""
    outliers = {}
    
    # Temperature outliers
    temp_outliers = df[(df['tmax_f'] > 130) | (df['tmax_f'] < -50) | (df['tmin_f'] > 130) | (df['tmin_f'] < -50)]
    if not temp_outliers.empty:
        outliers['temperature_outliers'] = temp_outliers
        
    # Energy outliers (negative consumption)
    energy_outliers = df[df['energy_mwh'] < 0]
    if not energy_outliers.empty:
        outliers['energy_outliers'] = energy_outliers
        
    return outliers

def check_data_freshness(df):
    """Checks how up-to-date the data is."""
    if 'date' not in df.columns:
        return "'date' column not found."
    
    latest_date = pd.to_datetime(df['date']).max()
    days_diff = (datetime.now() - latest_date).days
    
    return {
        'latest_data_point': latest_date.strftime('%Y-%m-%d'),
        'days_since_latest_data': days_diff
    }

def generate_quality_report():
    """Generates a full data quality report from processed files."""
    logging.info("Starting data quality analysis.")
    
    all_dfs = []
    try:
        processed_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('_processed.csv')]
        if not processed_files:
            logging.error("No processed data files found. Aborting quality analysis.")
            return
            
        for f in processed_files:
            df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, f))
            all_dfs.append(df)
    except FileNotFoundError:
        logging.error(f"Processed data directory not found at {PROCESSED_DATA_DIR}. Aborting quality analysis.")
        return

    combined_df = pd.concat(all_dfs, ignore_index=True)
    logging.info(f"Loaded and combined {len(processed_files)} processed files.")

    # --- Run Checks ---
    missing_values = check_missing_values(combined_df)
    outliers = check_outliers(combined_df)
    freshness = check_data_freshness(combined_df)

    # --- Write Report ---
    report_path = os.path.join(REPORTS_DIR, 'data_quality_report.txt')
    try:
        with open(report_path, 'w') as f:
            f.write("=====================================\n")
            f.write("    Data Quality Report            \n")
            f.write("=====================================\n")
            f.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("--- 1. Data Freshness ---\n")
            f.write(f"Latest data point found: {freshness['latest_data_point']}\n")
            f.write(f"Days since latest data: {freshness['days_since_latest_data']}\n\n")

            f.write("--- 2. Missing Values ---\n")
            if missing_values.empty:
                f.write("No missing values found.\n\n")
            else:
                f.write(missing_values.to_string())
                f.write("\n\n")

            f.write("--- 3. Outliers ---\n")
            if not outliers:
                f.write("No outliers found.\n\n")
            else:
                if 'temperature_outliers' in outliers:
                    f.write("Temperature Outliers (TMAX > 130F or TMIN < -50F):\n")
                    f.write(outliers['temperature_outliers'].to_string())
                    f.write("\n\n")
                if 'energy_outliers' in outliers:
                    f.write("Energy Outliers (Negative Consumption):\n")
                    f.write(outliers['energy_outliers'].to_string())
                    f.write("\n\n")

        logging.info(f"Data quality report successfully saved to {report_path}")
    except IOError as e:
        logging.error(f"Failed to write data quality report: {e}")

from scipy.stats import pearsonr
import pandas as pd
import os
import logging

# Assuming PROCESSED_DATA_DIR is defined elsewhere, e.g., as a global constant or passed as an argument.
# For demonstration, let's define a placeholder.
PROCESSED_DATA_DIR = './data/processed'

# Ensure the directory exists for the example to run without FileNotFoundError
# In a real scenario, this directory would be managed by data processing steps.
if not os.path.exists(PROCESSED_DATA_DIR):
    os.makedirs(PROCESSED_DATA_DIR)
    # Create a dummy file to avoid empty directory error in run_full_analysis
    with open(os.path.join(PROCESSED_DATA_DIR, 'dummy_processed.csv'), 'w') as f:
        f.write('date,tmax_f,tmin_f,energy_mwh\n2023-01-01,50,30,100\n')

def calculate_correlation(df):
    """Calculates correlation between temperature and energy consumption."""
    df['temp_avg_f'] = (df['tmax_f'] + df['tmin_f']) / 2
    
    # Filter out non-numeric or infinite values
    filtered_df = df[pd.to_numeric(df['temp_avg_f'], errors='coerce').notnull()]
    filtered_df = filtered_df[pd.to_numeric(filtered_df['energy_mwh'], errors='coerce').notnull()]

    if filtered_df.empty:
        return None, None

    correlation, _ = pearsonr(filtered_df['temp_avg_f'], filtered_df['energy_mwh'])
    r_squared = correlation**2
    return correlation, r_squared

def analyze_weekend_weekday_consumption(df):
    """Analyzes the difference in energy consumption between weekdays and weekends."""
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()
    df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday'])
    
    consumption_summary = df.groupby('is_weekend')['energy_mwh'].mean().reset_index()
    consumption_summary['is_weekend'] = consumption_summary['is_weekend'].apply(lambda x: 'Weekend' if x else 'Weekday')
    return consumption_summary

def analyze_seasonal_patterns(df):
    """Analyzes energy consumption across different seasons."""
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
            
    df['season'] = df['month'].apply(get_season)
    seasonal_summary = df.groupby('season')['energy_mwh'].mean().reset_index()
    return seasonal_summary

def prepare_heatmap_data(df):
    """Prepares data for the usage patterns heatmap."""
    df['temp_avg_f'] = (df['tmax_f'] + df['tmin_f']) / 2
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()

    temp_bins = [-float('inf'), 50, 60, 70, 80, 90, float('inf')]
    temp_labels = ['<50°F', '50-60°F', '60-70°F', '70-80°F', '80-90°F', '>90°F']
    
    df['temp_range'] = pd.cut(df['temp_avg_f'], bins=temp_bins, labels=temp_labels, right=False)
    
    heatmap_data = df.groupby(['temp_range', 'day_of_week'])['energy_mwh'].mean().unstack()
    
    # Order columns by day of the week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data[days_order]
    
    return heatmap_data

def run_full_analysis():
    """Runs all analysis functions and prints the results."""
    logging.info("Starting full data analysis.")
    
    try:
        processed_files = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith('_processed.csv')]
        if not processed_files:
            logging.error("No processed data files found. Aborting analysis.")
            return
        
        all_dfs = [pd.read_csv(os.path.join(PROCESSED_DATA_DIR, f)) for f in processed_files]
        combined_df = pd.concat(all_dfs, ignore_index=True)
        logging.info(f"Loaded and combined {len(processed_files)} processed files for analysis.")
    except FileNotFoundError:
        logging.error(f"Processed data directory not found at {PROCESSED_DATA_DIR}. Aborting analysis.")
        return

    print("\n--- Correlation Analysis ---")
    correlation, r_squared = calculate_correlation(combined_df.copy())
    print(f"Overall Temperature vs. Energy Correlation: {correlation:.4f}")
    print(f"R-squared: {r_squared:.4f}")

    print("\n--- Weekday vs. Weekend Analysis ---")
    weekend_analysis = analyze_weekend_weekday_consumption(combined_df.copy())
    print(weekend_analysis.to_string(index=False))

    print("\n--- Seasonal Analysis ---")
    seasonal_analysis = analyze_seasonal_patterns(combined_df.copy())
    print(seasonal_analysis.to_string(index=False))
    
    print("\n--- Heatmap Data Preparation ---")
    heatmap_data = prepare_heatmap_data(combined_df.copy())
    print("Heatmap data prepared with shape:", heatmap_data.shape)
    print(heatmap_data.head())


if __name__ == "__main__":
    # To generate the quality report:
    # generate_quality_report()
    
    # To run the deeper analysis:
    run_full_analysis()
