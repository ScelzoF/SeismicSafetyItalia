import requests
import pandas as pd
from datetime import datetime
import streamlit as st

# Stato attuale della sorgente (salvato in session_state)
if "current_source" not in st.session_state:
    st.session_state.current_source = "INGV"

INGV_URL = "https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&minlatitude=39.0&maxlatitude=44.0&minlongitude=12.0&maxlongitude=15.0&orderby=time&limit=100"
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

def fetch_earthquake_data():
    try:
        # Prova a usare INGV se attivo o se USGS fallisce
        if st.session_state.current_source == "INGV":
            try:
                data = fetch_from_ingv()
                if st.session_state.current_source != "INGV":
                    st.session_state.current_source = "INGV"
                    st.info("✅ Sorgente attuale: INGV (dati ufficiali italiani)")
                return data
            except Exception:
                data = fetch_from_usgs()
                st.session_state.current_source = "USGS"
                st.warning("⚠️ INGV non disponibile. Dati temporaneamente forniti da USGS.")
                return data
        else:
            try:
                data = fetch_from_ingv()
                st.session_state.current_source = "INGV"
                st.info("✅ INGV è di nuovo disponibile. Dati ufficiali ripristinati.")
                return data
            except Exception:
                data = fetch_from_usgs()
                if st.session_state.current_source != "USGS":
                    st.session_state.current_source = "USGS"
                    st.warning("⚠️ INGV ancora non disponibile. Dati da USGS.")
                return data
    except Exception as e:
        st.error(f"Errore durante il recupero dei dati sismici: {e}")
        return pd.DataFrame()

def fetch_from_ingv():
    response = requests.get(INGV_URL, timeout=5)
    response.raise_for_status()
    geojson = response.json()
    features = geojson["features"]

    data = []
    for f in features:
        prop = f["properties"]
        coords = f["geometry"]["coordinates"]
        data.append({
            "time": datetime.utcfromtimestamp(prop["time"] / 1000),
            "magnitude": prop["mag"],
            "location": prop["place"],
            "latitude": coords[1],
            "longitude": coords[0],
            "depth": coords[2]
        })
    df = df = pd.DataFrame(data)
    df["formatted_time"] = df["time"].dt.strftime("%d/%m/%Y %H:%M:%S")
    return df
    df["formatted_time"] = df["time"].dt.strftime("%d/%m/%Y %H:%M:%S")
    return df

def fetch_from_usgs():
    response = requests.get(USGS_URL, timeout=5)
    response.raise_for_status()
    geojson = response.json()
    features = geojson["features"]

    data = []
    for f in features:
        prop = f["properties"]
        coords = f["geometry"]["coordinates"]
        data.append({
            "time": datetime.utcfromtimestamp(prop["time"] / 1000),
            "magnitude": prop["mag"],
            "location": prop["place"],
            "latitude": coords[1],
            "longitude": coords[0],
            "depth": coords[2]
        })
    df = df = pd.DataFrame(data)
    df["formatted_time"] = df["time"].dt.strftime("%d/%m/%Y %H:%M:%S")
    return df
    df["formatted_time"] = df["time"].dt.strftime("%d/%m/%Y %H:%M:%S")
    return df

def get_significant_earthquakes(df, magnitude_threshold=2.5):
    if df.empty:
        return pd.DataFrame()
    return df[df["magnitude"] >= magnitude_threshold]

def calculate_earthquake_statistics(df):
    if df is None or df.empty:
        return {
            'count': 0,
            'avg_magnitude': 0,
            'max_magnitude': 0,
            'avg_depth': 0,
            'daily_counts': {}
        }
