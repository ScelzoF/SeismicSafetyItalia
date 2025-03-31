
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

def fetch_usgs_data():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    try:
        response = requests.get(url)
        data = response.json()
        earthquakes = []
        for feature in data["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            earthquakes.append({
                "luogo": props["place"],
                "magnitudo": props["mag"],
                "tempo": datetime.utcfromtimestamp(props["time"] / 1000),
                "lat": coords[1],
                "lon": coords[0],
                "profondita_km": coords[2],
                "link": props["url"]
            })
        return pd.DataFrame(earthquakes)
    except Exception as e:
        st.error(f"Errore durante il recupero dei dati USGS: {e}")
        return pd.DataFrame()

def show():
    st.title("📊 Terremoti in Tempo Reale - USGS")
    st_autorefresh(interval=60000, key="usgsrefresh")
    df = fetch_usgs_data()
    if df.empty:
        st.warning("Nessun dato disponibile.")
        return
    st.map(df[["lat", "lon"]])
    st.dataframe(df.sort_values(by="tempo", ascending=False))
