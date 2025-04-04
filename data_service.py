import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import streamlit as st
import json

# INGV API endpoint for Italian earthquakes
INGV_API_URL = "https://webservices.ingv.it/fdsnws/event/1/query"

# USGS API endpoint for worldwide earthquakes
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Function to fetch earthquake data from INGV (Italian Geological Service)
def fetch_ingv_data():
    # Get earthquakes from the last 7 days
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    # Format dates for the API request
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

    # Parameters for the INGV API request - using the updated format and parameters
    params = {
        "starttime": start_str,
        "endtime": end_str,
        "minmag": 1.0,  # Minimum magnitude
        "maxlat": 48.0,
        "minlat": 35.0,  # Latitude range for Italy
        "maxlon": 19.0,
        "minlon": 6.0,   # Longitude range for Italy
        "format": "geojson",  # Changed from "json" to "geojson"
        "limit": 500     # Limit the number of results
    }

    try:
        # Add proper headers for the request
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'EarthquakeMonitoringApp/1.0'
        }

        response = requests.get(INGV_API_URL, params=params, headers=headers)

        # Debug info
        st.session_state['debug_info'] = {
            'status_code': response.status_code,
            'url': response.url
        }

        # Check if response is successful
        if response.status_code != 200:
            st.error(f"INGV API Error: Status code {response.status_code}")
            return pd.DataFrame()

        # Check if response contains data
        if not response.text:
            st.error("INGV API returned empty response")
            return pd.DataFrame()

        # Try to parse JSON data
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            st.error(f"Error parsing INGV data: {e}")
            # If there's an issue with JSON parsing, return empty dataframe
            return pd.DataFrame()

        # Process the earthquakes - handle potential different formats
        earthquakes = []

        if "features" in data:
            for event in data.get("features", []):
                props = event.get("properties", {})
                geometry = event.get("geometry", {})
                coordinates = geometry.get("coordinates", [0, 0, 0]) if geometry else [0, 0, 0]

                # Handle both potential time formats
                time_val = props.get("time", "")
                if isinstance(time_val, (int, float)):
                    # If time is provided as Unix timestamp in milliseconds
                    time_str = datetime.fromtimestamp(time_val/1000).strftime("%Y-%m-%dT%H:%M:%S")
                else:
                    # If time is provided as ISO string
                    time_str = time_val

                earthquakes.append({
                    "time": time_str,
                    "magnitude": props.get("mag", 0),
                    "depth": coordinates[2] if len(coordinates) > 2 else 0,
                    "latitude": coordinates[1] if len(coordinates) > 1 else 0,
                    "longitude": coordinates[0] if len(coordinates) > 0 else 0,
                    "location": props.get("place", "Unknown"),
                    "source": "INGV"
                })

        return pd.DataFrame(earthquakes)

    except Exception as e:
        st.error(f"Error fetching INGV data: {e}")
        return pd.DataFrame()

# Function to fetch earthquake data from USGS (US Geological Survey)
def fetch_usgs_data():
    # Get earthquakes from the last 7 days with focus on the Campania region
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    # Format dates for the API request
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

    # Parameters for the USGS API request
    # Focused on Campania region (Vesuvius & Campi Flegrei)
    params = {
        "format": "geojson",
        "starttime": start_str,
        "endtime": end_str,
        "minmagnitude": 1.0,
        "latitude": 40.85,      # Approximate center of the Campania region
        "longitude": 14.25,
        "maxradiuskm": 100,     # 100km radius around the center
        "limit": 500
    }

    try:
        # Add proper headers for the request
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'EarthquakeMonitoringApp/1.0'
        }

        response = requests.get(USGS_API_URL, params=params, headers=headers)

        # Store debug info
        if 'debug_info' not in st.session_state:
            st.session_state['debug_info'] = {}
        st.session_state['debug_info']['usgs_status_code'] = response.status_code
        st.session_state['debug_info']['usgs_url'] = response.url

        # Check if response is successful
        if response.status_code != 200:
            st.error(f"USGS API Error: Status code {response.status_code}")
            return pd.DataFrame()

        # Check if response contains data
        if not response.text:
            st.error("USGS API returned empty response")
            return pd.DataFrame()

        # Try to parse JSON data
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            st.error(f"Error parsing USGS data: {e}")
            return pd.DataFrame()

        # Process the earthquakes more efficiently
        earthquakes = []
        features = data.get("features", [])
        if features:
            earthquakes = [{
                "time": datetime.fromtimestamp(feature["properties"].get("time", 0)/1000).strftime("%Y-%m-%dT%H:%M:%S"),
                "magnitude": feature["properties"].get("mag", 0),
                "depth": feature["geometry"]["coordinates"][2] if feature.get("geometry") else 0,
                "latitude": feature["geometry"]["coordinates"][1] if feature.get("geometry") else 0,
                "longitude": feature["geometry"]["coordinates"][0] if feature.get("geometry") else 0,
                "location": feature["properties"].get("place", "Unknown"),
                "source": "USGS"
            } for feature in features if feature.get("properties") and feature.get("geometry")]

        return pd.DataFrame(earthquakes)

    except Exception as e:
        st.error(f"Error fetching USGS data: {e}")
        return pd.DataFrame()

# Main function to fetch and combine earthquake data from all sources
def fetch_earthquake_data():
    try:
        # Initialize debug info if it doesn't exist
        if 'debug_info' not in st.session_state:
            st.session_state['debug_info'] = {}

        # Set fetch status in debug info
        st.session_state['debug_info']['fetch_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Fetch data from both sources
        ingv_data = fetch_ingv_data()
        usgs_data = fetch_usgs_data()

        # Track data source counts
        st.session_state['debug_info']['ingv_count'] = len(ingv_data)
        st.session_state['debug_info']['usgs_count'] = len(usgs_data)

        # Combine the data
        combined_data = pd.concat([ingv_data, usgs_data], ignore_index=True)
        st.session_state['debug_info']['combined_count'] = len(combined_data)

        if not combined_data.empty:
            # Convert time strings to datetime objects
            combined_data['datetime'] = pd.to_datetime(combined_data['time'], errors='coerce')

            # Count invalid datetimes
            invalid_dates = combined_data['datetime'].isna().sum()
            st.session_state['debug_info']['invalid_dates'] = int(invalid_dates)

            # Filter out rows with invalid datetime
            combined_data = combined_data.dropna(subset=['datetime'])

            # Sort by datetime (most recent first)
            combined_data = combined_data.sort_values(by='datetime', ascending=False)

            # Format the datetime for display
            combined_data['formatted_time'] = combined_data['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')

        st.session_state['debug_info']['fetch_status'] = 'success'
        return combined_data

    except Exception as e:
        st.error(f"Error processing earthquake data: {str(e)}")
        st.session_state['debug_info']['fetch_status'] = 'error'
        st.session_state['debug_info']['fetch_error'] = str(e)
        return pd.DataFrame()

# Filter earthquakes for specific areas of interest
def filter_area_earthquakes(df, area_name):
    if df is None or df.empty:
        return pd.DataFrame()

    # Define the geographical boundaries for each area
    area_bounds = {
        'vesuvio': {
            'lat_min': 40.75, 'lat_max': 40.85,
            'lon_min': 14.35, 'lon_max': 14.45
        },
        'campi_flegrei': {
            'lat_min': 40.80, 'lat_max': 40.90,
            'lon_min': 14.05, 'lon_max': 14.20
        },
        'ischia': {
            'lat_min': 40.70, 'lat_max': 40.80,
            'lon_min': 13.85, 'lon_max': 14.00
        }
    }

    if area_name in area_bounds:
        bounds = area_bounds[area_name]
        return df[(df['latitude'] >= bounds['lat_min']) & 
                 (df['latitude'] <= bounds['lat_max']) & 
                 (df['longitude'] >= bounds['lon_min']) & 
                 (df['longitude'] <= bounds['lon_max'])]
    else:
        # If no specific area, return all data
        return df

# Get significant earthquakes (magnitude >= 3.0) for notifications
def get_significant_earthquakes(df, min_magnitude=3.0, hours=24):
    if df is None or df.empty:
        return pd.DataFrame()

    # Get earthquakes above the minimum magnitude in the last X hours
    recent_time = datetime.now() - timedelta(hours=hours)

    return df[(df['magnitude'] >= min_magnitude) & 
              (df['datetime'] >= recent_time)]

# Calculate statistics for predictions
def calculate_earthquake_statistics(df):
    if df is None or df.empty:
        return {
            'count': 0,
            'avg_magnitude': 0,
            'max_magnitude': 0,
            'avg_depth': 0,
            'daily_counts': {}
        }

    # Group by days and count earthquakes
    df['date'] = df['datetime'].dt.date
    daily_counts = df.groupby('date').size().to_dict()

    # Format dates as strings for JSON serialization
    daily_counts = {str(k): v for k, v in daily_counts.items()}

    return {
        'count': len(df),
        'avg_magnitude': df['magnitude'].mean(),
        'max_magnitude': df['magnitude'].max(),
        'avg_depth': df['depth'].mean(),
        'daily_counts': daily_counts
    }

def fetch_earthquake_data():
    # Inizializza sorgente se non esiste
    if "source" not in st.session_state:
        st.session_state.source = None

    try:
        df = fetch_ingv_data()
        if st.session_state.source != "INGV":
            st.session_state.source = "INGV"
            st.info("✅ Dati sismici forniti da INGV (Italia)")
        return df
    except Exception as e:
        try:
            df = fetch_usgs_data()
            if st.session_state.source != "USGS":
                st.session_state.source = "USGS"
                st.warning("⚠️ Dati INGV non disponibili. Uso dati USGS (mondiali)")
            return df
        except Exception as e:
            st.error("❌ Errore nel recupero dei dati sismici da entrambe le fonti.")
            return pd.DataFrame()
