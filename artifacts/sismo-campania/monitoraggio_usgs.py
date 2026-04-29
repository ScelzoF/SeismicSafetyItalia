
import pandas as pd
import requests
from datetime import datetime

def dati_sismici():
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
    resp = requests.get(url, params=params, timeout=5)
    data = resp.json()["features"]

    eventi = []
    for q in data:
        props = q["properties"]
        geo = q["geometry"]["coordinates"]
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
