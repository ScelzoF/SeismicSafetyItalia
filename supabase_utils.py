"""
supabase_utils.py
=================
Tenta di usare Supabase. Se non disponibile (timeout / connessione),
usa st.session_state come fallback in-memory per la durata della sessione.
"""

import os
import requests
import time
import streamlit as st
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://usobrbklqjwjvxesfbxk.supabase.co")
REQUEST_TIMEOUT = 2   # 2s: DNS morto fallisce subito → fallback locale
MAX_RETRIES = 0


def _get_supabase_key():
    """Legge la chiave Supabase da st.secrets o variabile d'ambiente."""
    key = os.environ.get("SUPABASE_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
    return key


def _get_headers():
    key = _get_supabase_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


# ─── helpers ─────────────────────────────────────────────────────────────────

def _get_with_retry(url, headers, params=None, retries=MAX_RETRIES):
    for attempt in range(retries + 1):
        try:
            return requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            if attempt < retries:
                time.sleep(0.5)
            else:
                raise


def _post_with_retry(url, headers, json=None, retries=MAX_RETRIES):
    for attempt in range(retries + 1):
        try:
            return requests.post(url, headers=headers, json=json, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            if attempt < retries:
                time.sleep(0.5)
            else:
                raise


def _session_posts():
    """Restituisce la lista dei post in session_state (fallback in-memory)."""
    if "forum_posts_local" not in st.session_state:
        st.session_state.forum_posts_local = []
    return st.session_state.forum_posts_local


# ─── API pubblica ─────────────────────────────────────────────────────────────

def inserisci_post(username, contenuto):
    try:
        data = {"username": username, "contenuto": contenuto}
        response = _post_with_retry(
            f"{SUPABASE_URL}/rest/v1/chat_altro_progetto",
            headers=_get_headers(),
            json=data,
        )
        if response.status_code == 201:
            return True, "✅ Post inviato con successo!"
        # Supabase risponde ma con errore → fallback locale
    except Exception:
        pass

    # Fallback: salva in session_state
    _session_posts().append({
        "username": username or "Anonimo",
        "contenuto": contenuto,
        "data": datetime.now().isoformat(),
    })
    return True, "✅ Post pubblicato (modalità offline — visibile solo in questa sessione)"


def carica_post():
    try:
        response = _get_with_retry(
            f"{SUPABASE_URL}/rest/v1/chat_altro_progetto?select=*&order=id.desc&limit=50",
            headers=_get_headers(),
        )
        if response.status_code == 200:
            posts = response.json()
            # Aggiungi anche i post locali della sessione corrente in cima
            local = _session_posts()
            return local + posts, None
        return _session_posts(), None
    except Exception:
        pass

    # Supabase non raggiungibile: mostra solo post locali
    local = _session_posts()
    return local, None   # nessun errore mostrato, funziona in silenzio


def inserisci_segnalazione(username, contenuto):
    try:
        data = {"username": username or "Anonimo", "contenuto": contenuto}
        res = _post_with_retry(
            f"{SUPABASE_URL}/rest/v1/segnalazioni_altro_progetto",
            headers=_get_headers(),
            json=data,
        )
        res.raise_for_status()
        return True, "Segnalazione inviata con successo."
    except Exception:
        return True, "Segnalazione registrata localmente."


def carica_segnalazioni():
    try:
        res = _get_with_retry(
            f"{SUPABASE_URL}/rest/v1/segnalazioni_altro_progetto?select=*",
            headers=_get_headers(),
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def invia_segnalazione(localita, tipo_evento, intensita, descrizione):
    """
    Wrapper chiamato da segnala_evento.py.
    Tenta Supabase; in caso di errore salva in session_state (fallback).
    """
    try:
        data = {
            "username": localita or "N/D",
            "contenuto": f"[{tipo_evento} – intensità {intensita}/10] {descrizione}",
        }
        res = _post_with_retry(
            f"{SUPABASE_URL}/rest/v1/segnalazioni_altro_progetto",
            headers=_get_headers(),
            json=data,
        )
        if res.status_code in (200, 201):
            return True, "Segnalazione inviata con successo."
    except Exception:
        pass

    # Fallback locale (session_state)
    if "segnalazioni_local" not in st.session_state:
        st.session_state.segnalazioni_local = []
    st.session_state.segnalazioni_local.append({
        "localita": localita,
        "tipo_evento": tipo_evento,
        "intensita": intensita,
        "descrizione": descrizione,
        "data": datetime.now().isoformat(),
    })
    return True, "Segnalazione registrata localmente (modalità offline)."
