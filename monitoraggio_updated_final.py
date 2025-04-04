from dati_sismici import carica_dati, get_fonte_attuale
import streamlit as st


df = carica_dati()
fonte = get_fonte_attuale()

if fonte == "INGV":
    st.sidebar.success("✅ Dati sismici forniti da INGV (Istituto Nazionale di Geofisica e Vulcanologia)")
elif fonte == "USGS":
    st.sidebar.warning("⚠️ INGV non è temporaneamente raggiungibile. Dati attualmente forniti da USGS (U.S. Geological Survey)")
else:
    st.sidebar.error("❌ Nessuna fonte dati disponibile al momento")



import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

def show():
    st.header("📡 Monitoraggio Sismico e Meteo Avanzato")

    from dati_sismici import carica_dati, get_fonte_attuale
    df = carica_dati()
    fonte = get_fonte_attuale()
    if fonte == "INGV":
        st.sidebar.success("✅ Dati sismici forniti da INGV (Istituto Nazionale di Geofisica e Vulcanologia)")
    elif fonte == "USGS":
        st.sidebar.warning("⚠️ INGV non è temporaneamente raggiungibile. Dati attualmente forniti da USGS (U.S. Geological Survey)")
    else:
        st.sidebar.error("❌ Nessuna fonte dati disponibile al momento")

    # Geolocalizzazione
    coords = streamlit_js_eval(
        js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))', 
        key="get_geolocation"
    )

    # Meteo
    api_key = st.secrets.get("OPENWEATHER_API_KEY", "")
    city = st.text_input("📍 Inserisci una città per visualizzare il meteo", value="Napoli")
    
    if api_key and city:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
        response = requests.get(weather_url)
        if response.status_code == 200:
            data = response.json()
            st.subheader(f"☀️ Meteo a {city}")
            st.markdown(f"**Temperatura:** {data['main']['temp']}°C")
            st.markdown(f"**Condizioni:** {data['weather'][0]['description']}")
            st.markdown(f"**Umidità:** {data['main']['humidity']}%")
            st.markdown(f"**Velocità del vento:** {data['wind']['speed']} m/s")
            st.markdown(f"**Pressione atmosferica:** {data['main']['pressure']} hPa")
            
            # Visualizzazione dell'icona meteo
            icon = data['weather'][0]['icon']
            icon_url = f"http://openweathermap.org/img/wn/{icon}.png"
            st.image(icon_url)

            # Previsioni meteo
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
            forecast_response = requests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                st.subheader(f"📅 Previsioni per i prossimi 5 giorni")
                for forecast in forecast_data['list'][::8]:  # Ogni 24 ore
                    dt = datetime.utcfromtimestamp(forecast['dt'])
                    date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    temp = forecast['main']['temp']
                    description = forecast['weather'][0]['description']
                    st.write(f"{date}: {temp}°C, {description}")