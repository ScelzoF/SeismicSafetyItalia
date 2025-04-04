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
    if "current_source" not in st.session_state:
        st.session_state.current_source = "INGV"
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
    df["source"] = "USGS"
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
    df["source"] = "USGS"
    return df
    df["formatted_time"] = df["time"].dt.strftime("%d/%m/%Y %H:%M:%S")
    return df

def get_significant_earthquakes(df, magnitude_threshold=2.5):
    if df.empty:
        return pd.DataFrame()
    return df[df["magnitude"] >= magnitude_threshold]

    if df is None or df.empty:
        return {
            'count': 0,
            'avg_magnitude': 0,
            'max_magnitude': 0,
            'avg_depth': 0,
            'daily_counts': {}
        }


    if df is None or df.empty:
        return pd.DataFrame()

def filter_area_earthquakes(df, area):
    if df is None or df.empty:
        return pd.DataFrame()

    area_keywords = {
        'vesuvio': ['vesuvio', 'napoli', 'torre del greco', 'torre annunziata', 'portici', 'ercolano'],
        'campi_flegrei': ['pozzuoli', 'bacoli', 'campi flegrei', 'agnano', 'fuorigrotta'],
        'ischia': ['ischia'],
        'sannio': ['benevento', 'sannio', 'guardia', 'san bartolomeo', 'circello'],
        'cilento': ['cilento', 'sapri', 'vallo della lucania'],
        'irpinia': ['avellino', 'irpinia', 'lioni', 'grottaminarda'],
        'salerno': ['salerno', 'cava de tirreni', 'agropoli'],
        'caserta': ['caserta', 'sessa aurunca', 'aversa'],
    }

    keywords = area_keywords.get(area.lower(), [])
    mask = df['location'].str.lower().apply(lambda x: any(k in x for k in keywords))
    return df[mask]

def calculate_earthquake_statistics(df):
    if df is None or df.empty:
        return {
            'count': 0,
            'average_magnitude': 0,
            'max_magnitude': 0,
            'min_magnitude': 0,
            'last_event_time': None
        }

    return {
        'count': len(df),
        'average_magnitude': df["magnitude"].mean(),
        'max_magnitude': df["magnitude"].max(),
        'min_magnitude': df["magnitude"].min(),
        'last_event_time': df["time"].max()
    }

    if df is None or df.empty:
        return {
            'count': 0,
            'average_magnitude': 0,
            'max_magnitude': 0,
            'min_magnitude': 0,
            'last_event_time': None,
            'daily_counts': {}
        }

    df["date"] = df["time"].dt.date
    daily_counts = dict(Counter(df["date"]))

    return {
        'count': len(df),
        'average_magnitude': df["magnitude"].mean(),
        'max_magnitude': df["magnitude"].max(),
        'min_magnitude': df["magnitude"].min(),
        'last_event_time': df["time"].max(),
        'daily_counts': daily_counts
    }

    if df is None or df.empty:
        return {
            'count': 0,
            'average_magnitude': 0,
            'max_magnitude': 0,
            'min_magnitude': 0,
            'last_event_time': None,
            'daily_counts': {},
            'avg_depth': 0
        }

    df["date"] = df["time"].dt.date
    daily_counts = dict(Counter(df["date"]))
    avg_depth = df["depth"].mean() if "depth" in df.columns else 0

    return {
        'count': len(df),
        'average_magnitude': df["magnitude"].mean(),
        'max_magnitude': df["magnitude"].max(),
        'min_magnitude': df["magnitude"].min(),
        'last_event_time': df["time"].max(),
        'daily_counts': daily_counts,
        'avg_depth': avg_depth
    }

from collections import Counter

def calculate_earthquake_statistics(df):
    if df is None or df.empty:
        return {
            'count': 0,
            'average_magnitude': 0,
            'avg_magnitude': 0,
            'max_magnitude': 0,
            'min_magnitude': 0,
            'last_event_time': None,
            'daily_counts': {},
            'avg_depth': 0
        }

    df["date"] = df["time"].dt.date
    daily_counts = dict(Counter(df["date"]))
    avg_depth = df["depth"].mean() if "depth" in df.columns else 0
    avg_mag = df["magnitude"].mean()

    return {
        'count': len(df),
        'average_magnitude': avg_mag,
        'avg_magnitude': avg_mag,
        'max_magnitude': df["magnitude"].max(),
        'min_magnitude': df["magnitude"].min(),
        'last_event_time': df["time"].max(),
        'daily_counts': daily_counts,
        'avg_depth': avg_depth
    }


import plotly.express as px
import streamlit as st

def safe_plot_scatter(df, x_col, y_col, title):
    if df is None or df.empty or x_col not in df.columns or y_col not in df.columns:
        st.info("📊 Nessun dato disponibile per il grafico.")
        return

    fig = px.scatter(df, x=x_col, y=y_col, title=title)
    st.plotly_chart(fig)
