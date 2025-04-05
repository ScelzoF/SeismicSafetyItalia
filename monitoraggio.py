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
        st.info(fonte)
        st.dataframe(df)
    else:
        st.warning("⚠️ Nessun dato disponibile al momento.")
    return

    # Choose data source
    data_source = st.selectbox("Scegli la fonte dei dati", ["INGV", "USGS"])
    
    if data_source == "INGV":
        quakes = fetch_ingv_data()
    elif data_source == "USGS":
        quakes = fetch_usgs_data()
    else:
        st.warning("Seleziona una fonte valida.")
        return
    
    # Prepare data frame
    rows = []
    for q in quakes:
        prop = q["properties"]
        mag = prop.get("mag", 0)
        place = prop.get("place", "Sconosciuto")
        time_str = prop.get("time", "")
        try:
            time = pd.to_datetime(time_str)
        except:
            time = None
        rows.append({"Luogo": place, "Magnitudo": mag, "Data/Ora UTC": time})
    
    # Convert to dataframe
    df = pd.DataFrame(rows)

    # Display the data
    st.dataframe(df, use_container_width=True)

    # Create and display a plotly chart with unique ID
    fig = px.line(df, x="Data/Ora UTC", y="Magnitudo", title="📈 Media Magnitudo Giornaliera")
    st.plotly_chart(fig, use_container_width=True, key="unique_magnitude_chart")



# Dati sismici con fallback INGV → USGS
df, fonte = get_sismic_data(show_debug=show_debug)

if not df.empty:
    st.info(fonte)
    st.dataframe(df)
else:
    st.warning("⚠️ Nessun dato disponibile al momento.")
