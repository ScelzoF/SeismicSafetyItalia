
import requests

SUPABASE_URL = "https://ljrjaehrttxhqejcueqj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqcmphZWhydHR4aHFlamN1ZXFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxODU4OTcsImV4cCI6MjA1ODc2MTg5N30.wfbzum88wn0b0OVw6WlMunOWvLvnfIjqnRyGeEQLghY"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def inserisci_post(username, contenuto):
    data = {
        "username": username,
        "contenuto": contenuto
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/chat_altro_progetto",
        headers=SUPABASE_HEADERS,
        json=data
    )
    if response.status_code != 201:
        return False, f"Errore {response.status_code}: {response.text}"
    return True, "Post inviato con successo"

def carica_post():
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/chat_altro_progetto?select=*",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200:
        return response.json()
    return []

def invia_segnalazione(localita, tipo_evento, intensita, descrizione):
    data = {
        "localita": localita,
        "tipo_evento": tipo_evento,
        "intensita": intensita,
        "descrizione": descrizione
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/segnalazioni_altro_progetto",
        headers=SUPABASE_HEADERS,
        json=data
    )
    if response.status_code != 201:
        return False, f"Errore {response.status_code}: {response.text}"
    return True, "Segnalazione inviata con successo"



def inserisci_segnalazione(username, contenuto):
    try:
        data = {
            "username": username or "Anonimo",
            "contenuto": contenuto,
        }
        res = requests.post(f"{SUPABASE_URL}/rest/v1/segnalazioni_altro_progetto", json=data, headers=HEADERS)
        res.raise_for_status()
        return True, "✅ Segnalazione inviata con successo."
    except Exception as e:
        return False, f"Errore invio segnalazione: {e}"

def carica_segnalazioni():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/segnalazioni_altro_progetto?select=*", headers=HEADERS)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return []
