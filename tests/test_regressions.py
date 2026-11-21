"""Offline regression tests: no production requests, writes or AI calls."""

import ast
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import security


class Response:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()

    def json(self):
        return self.payload


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(security, "_config", lambda: ("https://example.invalid", {}))


def test_missing_configuration_never_uses_local_file(monkeypatch):
    monkeypatch.setattr(security, "_config", lambda: None)
    assert security.read_visit_counter() is None
    assert security.increment_visit_counter(str(uuid4())) is None


@pytest.mark.parametrize("payload", [[], {}, [{"count": -1}], [{"count": True}], [{"count": "12"}]])
def test_invalid_total_is_not_shown_as_zero(configured, monkeypatch, payload):
    monkeypatch.setattr(security.requests, "get", lambda *a, **k: Response(payload))
    assert security.read_visit_counter() is None


def test_existing_total_is_read(configured, monkeypatch):
    monkeypatch.setattr(security.requests, "get", lambda *a, **k: Response([{"count": 12345}]))
    assert security.read_visit_counter() == 12345


def test_rpc_never_posts_an_absolute_total(configured, monkeypatch):
    calls = []
    token = str(uuid4())
    def post(url, **kwargs):
        calls.append((url, kwargs["json"]))
        return Response(12346)
    monkeypatch.setattr(security.requests, "post", post)
    assert security.increment_visit_counter(token) == 12346
    assert calls == [("https://example.invalid/rest/v1/rpc/register_visit", {"p_visit_id": token})]


def test_timeout_then_retry_reuses_visit_id(configured, monkeypatch):
    seen = set()
    total = 1000
    first = True
    def post(url, **kwargs):
        nonlocal total, first
        token = kwargs["json"]["p_visit_id"]
        if token not in seen:
            total += 1
            seen.add(token)
        if first:
            first = False
            raise requests.Timeout()
        return Response(total)
    monkeypatch.setattr(security.requests, "post", post)
    token = str(uuid4())
    assert security.increment_visit_counter(token) is None
    assert security.increment_visit_counter(token) == 1001
    assert total == 1001


def test_street_map_uses_explicit_keyless_tiles():
    from map_tiles import street_map
    html = street_map([41, 14], 6).get_root().render()
    assert "https://tile.openstreetmap.org/{z}/{x}/{y}.png" in html
    assert "OpenStreetMap" in html
    for forbidden in ("cartocdn", "maptiler", "apikey", "insert your API"):
        assert forbidden not in html


@pytest.mark.parametrize("module_name,function", [
    ("data_service", "_ingv_ov_get"), ("ingv_monitor", "_ingv_get"),
])
def test_tls_errors_do_not_disable_verification(monkeypatch, module_name, function):
    module = importlib.import_module(module_name)
    calls = []
    def fail(url, **kwargs):
        calls.append(kwargs)
        raise requests.exceptions.SSLError()
    monkeypatch.setattr(module.requests, "get", fail)
    with pytest.raises(requests.exceptions.SSLError):
        getattr(module, function)("https://example.invalid", verify=False)
    assert len(calls) == 1
    assert calls[0]["verify"] is True


def test_disk_fallback_is_explicitly_stale(monkeypatch):
    import pandas as pd
    import data_service as module
    for name in ("_fetch_ingv_raw", "_fetch_usgs_raw", "_fetch_emsc_raw", "_fetch_gossip_raw"):
        monkeypatch.setattr(module, name, lambda: pd.DataFrame())
    frame = pd.DataFrame({"datetime": pd.to_datetime(["2026-01-01"]), "magnitude": [1.2]})
    monkeypatch.setattr(module, "_load_fallback", lambda: (frame, True))
    result = module.fetch_earthquake_data.__wrapped__()
    assert result.attrs["data_status"] == "stale"


def test_risk_banner_does_not_claim_an_official_alert():
    tree = ast.parse((ROOT / "visualization.py").read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_show_risk_banner")
    text = ast.get_source_segment((ROOT / "visualization.py").read_text(), fn)
    assert "allerta ufficiale INGV è GIALLO" not in text
    assert "nessuna evacuazione in corso" not in text


def test_forum_escapes_persisted_content():
    source = (ROOT / "forum.py").read_text()
    assert 'escape(str(post.get("username")' in source
    assert 'escape(str(post.get("contenuto")' in source
    assert "{post['contenuto']}" not in source
    assert 'st.session_state.forum_moderator = ModeratorAI()' in source


def test_moderation_uses_current_sdk_and_no_user_content_logging(monkeypatch):
    import chat_pubblica as module
    response = SimpleNamespace(results=[SimpleNamespace(model_dump=lambda: {
        "flagged": False, "categories": {}, "category_scores": {},
    })])
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return response
    monkeypatch.setattr(module.os, "getenv", lambda *args: "test-only-placeholder")
    monkeypatch.setattr(module.openai, "OpenAI", lambda **kwargs: SimpleNamespace(
        moderations=SimpleNamespace(create=create)
    ))
    assert module.check_with_openai("test message") == (False, None)
    assert calls[0]["model"] == "omni-moderation-latest"
    assert "openai.Moderation.create" not in (ROOT / "chat_pubblica.py").read_text()


def test_missing_alert_is_not_green():
    import multi_ai_service as module
    prompt = module._build_seismic_prompt("Campania", {})
    assert "Livello allerta INGV OV: NON DISPONIBILE" in prompt
    assert "rischio NON DISPONIBILE" in prompt


def test_all_python_sources_compile():
    for path in ROOT.glob("*.py"):
        compile(path.read_text(), str(path), "exec")


@pytest.mark.parametrize("area,sentence,expected", [
    ("campi_flegrei", "Attualmente il livello di allerta per i Campi Flegrei è <b>giallo</b>.", "GIALLO"),
    ("vesuvio", "Attualmente il livello di allerta al Vesuvio è verde.", "VERDE"),
    ("ischia", "Attualmente il livello di allerta per Ischia è arancione.", "ARANCIONE"),
    ("campi_flegrei", "Zona rossa, zona gialla. Nel 2012 allerta verde.", "NON DISPONIBILE"),
    ("ischia", "Attualmente il livello di allerta per i Campi Flegrei è rosso.", "NON DISPONIBILE"),
    ("vesuvio", "This page contains redirections, green areas and yellow maps.", "NON DISPONIBILE"),
    ("ischia", "Attualmente il livello di allerta per Ischia è verde. Attualmente il livello di allerta per Ischia è rosso.", "NON DISPONIBILE"),
])
def test_alert_parser_requires_current_area_specific_statement(area, sentence, expected):
    from alert_levels import parse_current_alert
    assert parse_current_alert(sentence, area) == expected


def test_alert_outage_never_returns_static_official_values(monkeypatch):
    import alert_levels as module
    def fail(*args, **kwargs):
        raise requests.ConnectionError()
    monkeypatch.setattr(module.requests, "get", fail)
    result = module.fetch_official_alert_levels()
    assert all(result[key] == module.UNKNOWN for key in module.OFFICIAL_URLS)


def test_alert_parser_respects_html_utf8_charset():
    from alert_levels import parse_current_alert
    html = (
        '<html><head><meta charset="utf-8"></head><body>'
        'Attualmente il livello di allerta per Ischia è verde.</body></html>'
    ).encode("utf-8")
    assert parse_current_alert(html, "ischia") == "VERDE"


def test_no_map_uses_a_keyed_provider_alias():
    for path in ROOT.glob("*.py"):
        assert 'tiles="CartoDB positron"' not in path.read_text()


def test_late_ai_workers_cannot_mutate_the_returned_result(monkeypatch):
    import multi_ai_service as module
    workers, waits = [], []
    clock = iter([0, 5, 15, 30])
    class Worker:
        def __init__(self, target):
            self.target = target
            workers.append(self)
        def start(self):
            pass
        def join(self, timeout):
            waits.append(timeout)
    monkeypatch.setattr(module.threading, "Thread", Worker)
    monkeypatch.setattr(module.time, "monotonic", lambda: next(clock))
    for name in ("_ask_gpt", "_ask_claude", "_ask_gemini"):
        monkeypatch.setattr(module, name, lambda *a, **k: "late response")
    result = module.ask_all_providers("offline test")
    for worker in workers:
        worker.target()
    assert result["gpt"] is None and result["claude"] is None and result["gemini"] is None
    assert waits == [20, 10, 0]


def test_streamlit_keeps_xsrf_and_cors_protection_enabled():
    import tomllib
    config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())
    assert config["server"]["enableXsrfProtection"] is True
    assert config["server"]["enableCORS"] is True
