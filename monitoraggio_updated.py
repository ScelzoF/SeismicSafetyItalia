
import requests
import streamlit as st
from datetime import datetime

# API key di OpenWeather
OPENWEATHER_API_KEY = "d23fb9868855e4bcb4dcf04404d14a78"

# Funzione per ottenere i dettagli meteo attuali
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return data
    else:
        return None

# Funzione per ottenere le previsioni meteo
def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return data
    else:
        return None

# Visualizza il meteo attuale
st.title("🌞 Meteo Attuale e Previsioni")
city = st.text_input("Inserisci una città per visualizzare il meteo", "Napoli")
weather_data = get_weather(city)
forecast_data = get_forecast(city)

if weather_data:
    st.header(f"Meteo a {city}")
    st.write(f"Temperatura: {weather_data['main']['temp']}°C")
    st.write(f"Condizioni: {weather_data['weather'][0]['description']}")
    st.write(f"Umidità: {weather_data['main']['humidity']}%")
    st.write(f"Velocità del vento: {weather_data['wind']['speed']} m/s")
    st.write(f"Pressione atmosferica: {weather_data['main']['pressure']} hPa")

    # Visualizzazione della mappa meteo (icona)
    icon = weather_data['weather'][0]['icon']
    icon_url = f"http://openweathermap.org/img/wn/{icon}.png"
    st.image(icon_url)

# Visualizzazione delle previsioni meteo per 5 giorni
if forecast_data:
    st.subheader(f"Previsioni per {city} nei prossimi giorni")
    forecast_list = forecast_data['list']
    for forecast in forecast_list[::8]:  # Una previsione ogni 24 ore
        dt = datetime.utcfromtimestamp(forecast['dt'])
        date = dt.strftime("%Y-%m-%d %H:%M:%S")
        temp = forecast['main']['temp']
        description = forecast['weather'][0]['description']
        st.write(f"{date}: {temp}°C, {description}")
