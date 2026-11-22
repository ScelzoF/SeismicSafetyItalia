"""Streamlit execution smoke tests with all HTTP requests disabled."""

import importlib
from pathlib import Path
import sys

import pandas as pd
import pytest
import requests
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def offline(*args, **kwargs):
    raise requests.ConnectionError("offline regression test")


@pytest.fixture
def offline_app(monkeypatch):
    monkeypatch.setattr(requests, "get", offline)
    monkeypatch.setattr(requests, "post", offline)
    import security
    monkeypatch.setattr(security, "_config", lambda: None)
    # Cache state from other tests must not change the fixture.
    import streamlit as st
    st.cache_data.clear()
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=45)


@pytest.mark.parametrize("page", [
    "monitoring", "weather", "community", "emergency", "about", "oldstyle",
    "ai_assistant", "predictions",
])
def test_navigation_without_network_has_no_uncaught_exception(offline_app, page):
    app = offline_app.run()
    assert not app.exception
    if page != "monitoring":
        app.sidebar.radio[0].set_value(page).run()
    assert not app.exception
    assert any("temporaneamente non disponibili" in str(c.value) for c in app.sidebar.caption)


def test_monitoring_with_catalog_data(offline_app, monkeypatch):
    module = importlib.import_module("data_service")
    times = pd.date_range(end=pd.Timestamp.utcnow().tz_localize(None), periods=12, freq="12h")
    frame = pd.DataFrame({
        "datetime": times,
        "time": times.strftime("%Y-%m-%dT%H:%M:%S"),
        "formatted_time": times.strftime("%d/%m/%Y %H:%M:%S"),
        "magnitude": [1.0 + (i % 3) * 0.2 for i in range(12)],
        "depth": [5.0] * 12,
        "latitude": [40.83] * 12,
        "longitude": [14.14] * 12,
        "location": ["Campi Flegrei"] * 12,
        "source": ["INGV"] * 12,
    })
    frame.attrs["data_status"] = "fresh"
    monkeypatch.setattr(module, "fetch_earthquake_data", lambda: frame.copy())
    app = offline_app.run()
    assert not app.exception


def test_repeated_reruns_do_not_accumulate_keepalive_workers(offline_app):
    import threading
    app = offline_app.run()
    app.run()
    app.run()
    assert not app.exception
    assert sum(t.name == "oldstyle-keepalive" for t in threading.enumerate()) == 1


def test_unknown_emergency_level_does_not_become_an_evacuation_order(offline_app):
    app = offline_app.run()
    app.sidebar.radio[0].set_value("emergency").run()
    app.selectbox(key="sai_cosa_area_sel").set_value("🌋 Vesuvio (25 comuni zona rossa)").run()
    assert not app.exception
    rendered = " ".join(str(x.value) for x in app.markdown)
    assert "NON DISPONIBILE" in rendered
    assert "non costituisce un ordine di evacuazione" in rendered
    assert "EVACUA ORA" not in rendered
