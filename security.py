import os as _os
import requests as _requests

_COUNTER_PATH = _os.path.join(_os.path.dirname(__file__), "data", "visit_counter.txt")
_SUPABASE_URL = _os.environ.get("SUPABASE_URL", "https://usobrbklqjwjvxesfbxk.supabase.co")
_TABLE = "visit_stats"


def _get_supabase_key():
    key = _os.environ.get("SUPABASE_KEY", "")
    if not key:
        try:
            import streamlit as _st
            key = _st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
    return key


def _supabase_headers():
    key = _get_supabase_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _supabase_read():
    try:
        r = _requests.get(
            f"{_SUPABASE_URL}/rest/v1/{_TABLE}?id=eq.1&select=count",
            headers=_supabase_headers(),
            timeout=3,
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                return int(data[0].get("count", 0))
    except Exception:
        pass
    return None


def _supabase_upsert(count):
    try:
        r = _requests.post(
            f"{_SUPABASE_URL}/rest/v1/{_TABLE}",
            headers={**_supabase_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            json={"id": 1, "count": count},
            timeout=3,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def _ensure_data_dir():
    try:
        _os.makedirs(_os.path.dirname(_COUNTER_PATH), exist_ok=True)
        return True
    except Exception:
        return False


def _file_read():
    try:
        if _os.path.exists(_COUNTER_PATH):
            with open(_COUNTER_PATH, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
    except Exception:
        pass
    return 0


def _file_write(count):
    if not _ensure_data_dir():
        return
    try:
        with open(_COUNTER_PATH, "w") as f:
            f.write(str(count))
    except Exception:
        pass


def read_visit_counter():
    """Legge il contatore visite — Supabase se disponibile, file locale come fallback."""
    val = _supabase_read()
    if val is not None:
        return val
    return _file_read()


def increment_visit_counter():
    """Incrementa il contatore e salva su Supabase + file locale."""
    current = read_visit_counter()
    new_count = current + 1
    _supabase_upsert(new_count)
    _file_write(new_count)
    return new_count
