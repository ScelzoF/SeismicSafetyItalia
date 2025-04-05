
import pandas as pd
import requests
from datetime import datetime
import streamlit as st

@st.cache_data(ttl=5, show_spinner=False)
def fetch_ingv_data():
    try:
        url = "https://webservices.ingv.it/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "starttime": datetime.utcnow().date().isoformat() + "T00:00:00"
        }
        resp = requests.get(url, params=params, timeout=4)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        eventi = []
        for q in features:
            props = q.get("properties", {})
            geo = q.get("geometry", {}).get("coordinates", [0, 0, 0])
            eventi.append({
                "time": props.get("time"),
                "magnitude": props.get("mag", 0),
                "depth": geo[2] if len(geo) > 2 else 0,
                "latitude": geo[1] if len(geo) > 1 else 0,
                "longitude": geo[0] if len(geo) > 0 else 0,
                "location": props.get("place", "Sconosciuto"),
                "source": "INGV"
            })
        return pd.DataFrame(eventi)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=5, show_spinner=False)
def fetch_usgs_data():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "starttime": datetime.utcnow().date().isoformat() + "T00:00:00",
            "minmagnitude": 1.0,
            "latitude": 40.85,
            "longitude": 14.25,
            "maxradiuskm": 100,
            "limit": 500
        }
        resp = requests.get(url, params=params, timeout=4)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        eventi = []
        for q in features:
            props = q.get("properties", {})
            geo = q.get("geometry", {}).get("coordinates", [0, 0, 0])
            eventi.append({
                "time": props.get("time"),
                "magnitude": props.get("mag", 0),
                "depth": geo[2] if len(geo) > 2 else 0,
                "latitude": geo[1] if len(geo) > 1 else 0,
                "longitude": geo[0] if len(geo) > 0 else 0,
                "location": props.get("place", "Sconosciuto"),
                "source": "USGS"
            })
        return pd.DataFrame(eventi)
    except Exception:
        return pd.DataFrame()

def get_sismic_data():
    try:
        df = fetch_ingv_data()
        if df.empty:
            raise ValueError("Dati INGV non validi o vuoti.")
        return df, "Fonte: INGV"
    except Exception:
        try:
            df = fetch_usgs_data()
            if df.empty:
                raise ValueError("Dati USGS non validi o vuoti.")
            return df, "Fonte temporanea: USGS (INGV non disponibile)"
        except Exception:
            return pd.DataFrame(), "⚠️ Errore nel recupero dati da INGV e USGS."
