"""Persistent visit totals. Never replace the database total with a local file."""

import logging
import os
from uuid import UUID, uuid4

import requests

_LOG = logging.getLogger(__name__)
_DEFAULT_URL = "https://usobrbklqjwjvxesfbxk.supabase.co"


def _setting(name, default=""):
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def _config():
    url = str(_setting("SUPABASE_URL", _DEFAULT_URL)).rstrip("/")
    key = _setting("SUPABASE_KEY")
    if not key or not url.startswith("https://"):
        return None
    return url, {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _valid_count(value):
    # bool is an int subclass, but is not a valid counter response.
    return value if type(value) is int and value >= 0 else None


def read_visit_counter():
    """Return a confirmed persistent total, or None when it is unavailable."""
    config = _config()
    if config is None:
        return None
    url, headers = config
    try:
        response = requests.get(
            f"{url}/rest/v1/visit_stats",
            params={"id": "eq.1", "select": "count"},
            headers=headers,
            timeout=(3, 5),
        )
        response.raise_for_status()
        rows = response.json()
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return _valid_count(rows[0].get("count"))
    except (requests.RequestException, ValueError, TypeError):
        # Do not log request objects, headers, response bodies or credentials.
        _LOG.warning("Persistent visit total temporarily unavailable")
    return None


def increment_visit_counter(visit_id=None):
    """Atomically count a session once, including retries after a timeout.

    Streamlit must retain visit_id in session_state until success. Database
    setup: sql/visit_counter.sql. No local-file fallback is allowed here.
    """
    token = str(UUID(str(visit_id))) if visit_id is not None else str(uuid4())
    config = _config()
    if config is None:
        return None
    url, headers = config
    try:
        response = requests.post(
            f"{url}/rest/v1/rpc/register_visit",
            headers=headers,
            json={"p_visit_id": token},
            timeout=(3, 5),
        )
        response.raise_for_status()
        return _valid_count(response.json())
    except (requests.RequestException, ValueError, TypeError):
        _LOG.warning("Visit registration unavailable; persistent total unchanged by client")
        return None
