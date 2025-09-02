
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="US Weather & Energy Analysis",
    page_icon="⚡",
    layout="wide"
)

# --- Data Loading ---
@st.cache_data
def load_data():
    """Loads processed data from the data/processed directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    
    all_dfs = []
    try:
        processed_files = [f for f in os.listdir(processed_dir) if f.endswith('_processed.csv')]
        for f in processed_files:
            df = pd.read_csv(os.path.join(processed_dir, f))
            all_dfs.append(df)
    except FileNotFoundError:
        st.error(f"Processed data directory not found at {processed_dir}. Please run the pipeline first.")
        return pd.DataFrame()

    if not all_dfs:
        st.warning("No processed data files found. Please run the data processing script.")
        return pd.DataFrame()

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    return combined_df

df = load_data()

if not df.empty:
    # --- Sidebar Filters ---
    st.sidebar.header("Dashboard Filters")

    all_cities = sorted(df['city'].unique())
    selected_cities = st.sidebar.multiselect(
        "Select Cities",
        options=all_cities,
        default=all_cities
    )

    min_date = df['date'].min().to_pydatetime()
    max_date = df['date'].max().to_pydatetime()
    
    default_start_date = max(min_date, max_date - timedelta(days=90))
    selected_date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(default_start_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # --- Filtering & Pre-calculation ---
    start_date, end_date = selected_date_range
    filtered_df = df[
        (df['city'].isin(selected_cities)) &
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date))
    ].copy()

    if 'tmax_f' in filtered_df.columns and 'tmin_f' in filtered_df.columns:
        filtered_df['temp_avg_f'] = (filtered_df['tmax_f'] + filtered_df['tmin_f']) / 2

    # --- Main Dashboard ---
    st.title("US Weather & Energy Analysis Dashboard")
    st.markdown(f"*Data last updated: {max_date.strftime('%Y-%m-%d')}*")

    # --- About Section ---
    st.header("About This Dashboard")
    st.markdown("""
    This dashboard presents an analysis of weather patterns and energy consumption across major US cities. 
    The data is sourced from NOAA for weather and EIA for energy usage.
    **Purpose:** To explore the relationship between temperature and energy demand, and to identify patterns in energy consumption.
    """)

    # --- Visualization 1: Geographic Overview ---
    st.header("Geographic Overview")
    
    city_coords = {
        'New York': {'lat': 40.7128, 'lon': -74.0060},
        'Chicago': {'lat': 41.8781, 'lon': -87.6298},
        'Houston': {'lat': 29.7604, 'lon': -95.3698},
        'Phoenix': {'lat': 33.4484, 'lon': -112.0740},
        'Seattle': {'lat': 47.6062, 'lon': -122.3321}
    }
    
    latest_data = filtered_df.loc[filtered_df.groupby('city')['date'].idxmax()].copy()
    latest_data['lat'] = latest_data['city'].map(lambda x: city_coords.get(x, {}).get('lat'))
    latest_data['lon'] = latest_data['city'].map(lambda x: city_coords.get(x, {}).get('lon'))

    def get_yesterday_energy(row):
        yesterday_data = df[(df['city'] == row['city']) & (df['date'] == row['date'] - pd.Timedelta(days=1))]
        if not yesterday_data.empty:
            return yesterday_data['energy_mwh'].values[0]
        return np.nan

    latest_data['yesterday_energy_mwh'] = latest_data.apply(get_yesterday_energy, axis=1)
    latest_data['energy_pct_change'] = ((latest_data['energy_mwh'] - latest_data['yesterday_energy_mwh']) / latest_data['yesterday_energy_mwh']) * 100
    
    if not latest_data.empty:
        fig_map = px.scatter_mapbox(
            latest_data,
            lat="lat",
            lon="lon",
            color="energy_mwh",
            size="temp_avg_f" if "temp_avg_f" in latest_data.columns else None,
            hover_name="city",
            hover_data={
                'temp_avg_f': ':.1f°F', 
                'energy_mwh': ':,.0f MWh', 
                'energy_pct_change': ':.2f%',
                'lat': False, 
                'lon': False
            },
            color_continuous_scale=px.colors.sequential.Reds,
            size_max=20, zoom=3, mapbox_style="carto-positron",
            title="Geographic Overview of Latest Data"
        )
        fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No data to display for the selected filters.")

    # --- Visualization 2: Time Series Analysis ---
    st.header("Time Series Analysis")
    
    time_series_city = st.selectbox(
        "Select City for Time Series",
        options=["All Cities"] + all_cities,
        index=0
    )

    ts_df = filtered_df.copy()
    if time_series_city != "All Cities":
        ts_df = ts_df[ts_df['city'] == time_series_city]
    else:
        agg_dict = {'energy_mwh': 'sum'}
        if 'temp_avg_f' in ts_df.columns:
            agg_dict['temp_avg_f'] = 'mean'
        ts_df = ts_df.groupby('date').agg(agg_dict).reset_index()

    if not ts_df.empty and 'temp_avg_f' in ts_df.columns:
        fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
        fig_ts.add_trace(go.Scatter(x=ts_df['date'], y=ts_df['temp_avg_f'], name="Avg Temperature", line=dict(color='#636EFA')), secondary_y=False)
        fig_ts.add_trace(go.Scatter(x=ts_df['date'], y=ts_df['energy_mwh'], name="Energy Consumption", line=dict(color='#EF553B', dash='dot')), secondary_y=True)

        weekends = ts_df[ts_df['date'].dt.dayofweek >= 5]
        for _, row in weekends.iterrows():
            fig_ts.add_vrect(x0=row['date'] - pd.Timedelta(days=0.5), x1=row['date'] + pd.Timedelta(days=0.5), fillcolor="rgba(200, 200, 200, 0.2)", layer="below", line_width=0)

        fig_ts.update_layout(title_text=f"Temperature and Energy Consumption Over Time ({time_series_city})", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_ts.update_xaxes(title_text="Date")
        fig_ts.update_yaxes(title_text="Avg Temperature (°F)", secondary_y=False)
        fig_ts.update_yaxes(title_text="Energy Consumption (MWh)", secondary_y=True)
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("Not enough data to display time series. Check if 'tmax_f' and 'tmin_f' columns exist in the source data.")

    # --- Visualization 3: Correlation Analysis ---
    st.header("Correlation Analysis")
    if not filtered_df.empty and 'temp_avg_f' in filtered_df.columns:
        fig_corr = px.scatter(
            filtered_df, 
            x="temp_avg_f", 
            y="energy_mwh", 
            color="city", 
            trendline="ols",
            title="Temperature vs. Energy Consumption", 
            labels={"temp_avg_f": "Average Temperature (°F)", "energy_mwh": "Energy Consumption (MWh)"}, 
            hover_data=['date']
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)

        try:
            results = px.get_trendline_results(fig_corr)
            r_squared = results.iloc[0]["px_fit_results"].rsquared
            
            corr_matrix = filtered_df[['temp_avg_f', 'energy_mwh']].corr()
            correlation_coefficient = corr_matrix.loc['temp_avg_f', 'energy_mwh']

            st.markdown(f"**Overall R-squared:** `{r_squared:.4f}`")
            st.markdown(f"**Correlation Coefficient:** `{correlation_coefficient:.4f}`")
        except:
            st.info("Could not calculate trendline statistics. Not enough data points.")
    else:
        st.info("Not enough data to display correlation analysis.")

    # --- Visualization 4: Usage Patterns Heatmap ---
    st.header("Usage Patterns Heatmap")
    
    heatmap_city = st.selectbox("Select City for Heatmap", options=["All Cities"] + all_cities, index=0)
    
    heatmap_df = filtered_df.copy()
    if heatmap_city != "All Cities":
        heatmap_df = heatmap_df[heatmap_df['city'] == heatmap_city]

    if not heatmap_df.empty and 'temp_avg_f' in heatmap_df.columns and 'day_of_week' in heatmap_df.columns:
        temp_bins = [-float('inf'), 50, 60, 70, 80, 90, float('inf')]
        temp_labels = ['<50°F', '50-60°F', '60-70°F', '70-80°F', '80-90°F', '>90°F']
        heatmap_df['temp_range'] = pd.cut(heatmap_df['temp_avg_f'], bins=temp_bins, labels=temp_labels, right=False)
        heatmap_data = heatmap_df.groupby(['temp_range', 'day_of_week'])['energy_mwh'].mean().unstack()
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(columns=days_order)

        fig_heatmap = px.imshow(
            heatmap_data, 
            text_auto=True, 
            aspect="auto", 
            color_continuous_scale='RdBu_r',
            title=f"Average Energy Usage by Temperature and Day of Week ({heatmap_city})", 
            labels=dict(x="Day of Week", y="Temperature Range", color="Avg. Energy (MWh)")
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Not enough data to display heatmap. Check for 'temp_avg_f' and 'day_of_week' columns.")

else:
    st.info("No data to display. Please check the data source.")
