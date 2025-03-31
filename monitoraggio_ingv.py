
import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

def fetch_ingv_data():
    url = "https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&orderby=time&limit=50"
    try:
        response = requests.get(url)
        data = response.json()
        earthquakes = []
        for feature in data["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            earthquakes.append({
                "luogo": props.get("place", "Italia"),
                "magnitudo": props["mag"],
                "tempo": datetime.utcfromtimestamp(props["time"] / 1000),
                "lat": coords[1],
                "lon": coords[0],
                "profondita_km": coords[2],
                "link": props.get("url", "https://terremoti.ingv.it")
            })
        return pd.DataFrame(earthquakes)
    except Exception as e:
        st.error(f"Errore nel recupero dati INGV: {e}")
        return pd.DataFrame()

def show():
    st.title("🇮🇹 Terremoti in Tempo Reale - INGV")
    st_autorefresh(interval=60000, key="ingvrefresh")
    df = fetch_ingv_data()
    if df.empty:
        st.warning("Nessun dato disponibile dal servizio INGV.")
        return
    st.map(df[["lat", "lon"]])
    st.dataframe(df.sort_values(by="tempo", ascending=False))
