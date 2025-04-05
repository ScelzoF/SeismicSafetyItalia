from fallback_wrapper import get_sismic_data

import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import plotly.express as px
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# Function to combine INGV and USGS data and remove duplicates
def combine_unique_events(ingv_data, usgs_data):
    # Combine both datasets and drop duplicates based on a unique key (e.g., 'place' and 'time')
    all_events = pd.concat([ingv_data, usgs_data])
    all_events.drop_duplicates(subset=["Luogo", "Data/Ora UTC"], keep="last", inplace=True)
    return all_events

# Function to fetch INGV data
def fetch_ingv_data():
    ingv_url = f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&starttime={datetime.utcnow().date()}T00:00:00"
    ingv_resp = requests.get(ingv_url)
    return ingv_resp.json()["features"]

# Function to fetch USGS data
def fetch_usgs_data():
    usgs_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={datetime.utcnow().date()}T00:00:00"
    usgs_resp = requests.get(usgs_url)
    return usgs_resp.json()["features"]

# Function to process and combine data from INGV and USGS

def process_data():
    show_debug = st.sidebar.checkbox('Mostra dettagli tecnici')
    with st.spinner('🔄 Recupero dati sismici...'):
        df, fonte = get_sismic_data(show_debug=show_debug)

    if not df.empty:
        if show_debug:
            st.success("✅ DEBUG: process_data è stata eseguita!")
        st.info(fonte)
        st.dataframe(df)
    else:
        st.warning("⚠️ Nessun dato disponibile al momento.")

