
import requests
from bs4 import BeautifulSoup

def get_ilmeteo_forecast(city="Napoli"):
    city_url = city.strip().replace(" ", "-")
    url = f"https://www.ilmeteo.it/meteo/{city_url}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return [{"giorno": "Errore", "descrizione": str(e), "temperatura": "N/A"}]

    soup = BeautifulSoup(response.text, "html.parser")
    forecast = []

    for card in soup.select(".scroll-day"):
        giorno = card.select_one(".day-name")
        descrizione = card.select_one(".day-weather")
        temp = card.select_one(".day-temp")

        if giorno and descrizione and temp:
            forecast.append({
                "giorno": giorno.get_text(strip=True),
                "descrizione": descrizione.get_text(strip=True),
                "temperatura": temp.get_text(strip=True)
            })

    return forecast
