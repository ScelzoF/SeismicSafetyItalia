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
    assert "Sismicità: NON DISPONIBILE eventi" in prompt
    assert "GPS deformazione: NON DISPONIBILE" in prompt
    assert "Pressione atm. base: NON DISPONIBILE" in prompt


def test_ai_context_does_not_turn_missing_alert_into_green():
    source = (ROOT / "app.py").read_text()
    assert '"alert_level":          _alert_map.get(mai_area, "NON DISPONIBILE")' in source
    assert '"alert_level":          _alert_map.get(mai_area, "VERDE")' not in source


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


def test_multi_ai_rejects_unrelated_provider_pages(monkeypatch):
    import multi_ai_service as module
    unrelated = (
        "Copilot moved to a new app. Install the new Copilot app and sign in "
        "with the same account. Your history and content will be deleted."
    )
    calls = []
    def fake(prompt, system="", **kwargs):
        calls.append(kwargs.get("allow_fallback"))
        return unrelated
    for name in ("_ask_gpt", "_ask_claude", "_ask_gemini"):
        monkeypatch.setattr(module, name, fake)
    result = module.multi_ai_consensus("Campi Flegrei", {"n_events": 2, "max_mag": 1.4})
    assert calls == [False, False, False]
    assert result["n_responses"] == 0
    assert result["providers_rejected"] == ["gpt", "claude", "gemini"]
    assert all(result[key] is None for key in ("gpt", "claude", "gemini"))
    assert "Nessuna risposta pertinente" in result["consensus"]


def test_ai_answer_must_name_area_and_seismic_topic():
    from multi_ai_service import _is_relevant_ai_answer
    assert _is_relevant_ai_answer(
        "Campi Flegrei: i dati INGV mostrano sismicità recente; la magnitudo massima resta limitata.",
        "Campi Flegrei",
    )
    assert not _is_relevant_ai_answer(
        "Copilot moved to a new app. Install it and sign in with the same account.",
        "Campi Flegrei",
    )


def test_bulletin_status_is_independent_for_each_volcano(monkeypatch):
    import ingv_monitor as module
    monkeypatch.setattr(module, "_fetch_bulletin_pdf_vesuvio", lambda: {
        "bulletin_date": "Ottobre 2026", "_fetched_at": "22/11/2026 12:00",
        "_pdf_url": "https://www.ov.ingv.it/vesuvio.pdf", "seismic_events_month": 8,
    })
    monkeypatch.setattr(module, "_fetch_bulletin_pdf_ischia", lambda: {})
    monkeypatch.setattr(module, "_fetch_bulletin_pdf_cf", lambda: {
        "bulletin_date": "17 novembre 2026", "_fetched_at": "22/11/2026 12:00",
        "_pdf_url": "https://www.ov.ingv.it/flegrei.pdf",
    })
    result = module.fetch_bulletin_values_live()
    assert result["campi_flegrei"]["_live"] is True
    assert result["vesuvio"]["_live"] is True
    assert result["ischia"]["_live"] is False
    assert result["campi_flegrei"]["source"] == result["campi_flegrei"]["_source"]
    assert result["_scraped"] is True


def test_rite_uses_official_bulletin_instead_of_broken_ngl_path(monkeypatch):
    import ingv_monitor as module
    ngl_calls = []
    monkeypatch.setattr(module, "_fetch_ngl_tail", lambda *a, **k: ngl_calls.append(a) or [])
    monkeypatch.setattr(module, "fetch_bulletin_values_live", lambda: {
        "campi_flegrei": {
            "_live": True, "gps_uplift_mm_month": 10.0, "bulletin_date": "17 novembre 2026",
                "_parsed_fields": ["gps_uplift_mm_month"],
            "_source": "INGV OV — Bollettino settimanale Campi Flegrei",
            "source": "INGV OV — Bollettino settimanale Campi Flegrei",
        }
    })
    result = module.fetch_gps_rite.__wrapped__()
    assert ngl_calls == []
    assert result["source_type"] == "bulletin_live"
    assert result["source"] == "INGV OV — Bollettino settimanale Campi Flegrei"


def test_ngl_does_not_label_old_station_data_as_live():
    from datetime import datetime, timezone
    from ingv_monitor import _parse_ngl_lines
    stale = [f"NAPL 0 {2024 + i * 0.01:.6f} a b c d e f g {i * 0.001:.4f}" for i in range(20)]
    assert _parse_ngl_lines("NAPL", stale) is None
    today = datetime.now(timezone.utc).date()
    current = today.year + (today.timetuple().tm_yday - 1) / 365.25
    fresh = [f"BKNO 0 {current - i * 0.01:.6f} a b c d e f g {i * 0.001:.4f}" for i in range(20)]
    result = _parse_ngl_lines("BKNO", fresh)
    assert result is not None
    assert result["last_date"] == today.strftime("%Y-%m-%d")


def test_unverified_static_gps_and_bulletin_values_stay_hidden():
    from visualization import _format_gps_rate, _verified_bulletin_value
    assert _format_gps_rate({"source_type": "unavailable", "monthly_rate_mm": 0.0}) == "NON DISPONIBILE"
    assert _verified_bulletin_value({
        "_live": False, "_parsed_fields": [], "ground_temp_30cm": 95,
    }, "ground_temp_30cm", "°C") == "NON DISPONIBILE"
    assert _verified_bulletin_value({
        "_live": True, "_parsed_fields": ["gps_uplift_mm_month"], "gps_uplift_mm_month": 10,
    }, "gps_uplift_mm_month", " mm/mese", 1) == "10.0 mm/mese"


def test_default_bulletin_gps_rates_are_not_marked_live(monkeypatch):
    import ingv_monitor as module
    monkeypatch.setattr(module, "_fetch_ngl_tail", lambda *a, **k: [])
    monkeypatch.setattr(module, "fetch_bulletin_values_live", lambda: {
        "vesuvio": {
            "_live": True, "_parsed_fields": ["bulletin_date"],
            "gps_uplift_mm_month": -0.1, "bulletin_date": "Ottobre 2026",
        },
        "ischia": {
            "_live": True, "_parsed_fields": ["seismic_events_12m"],
            "gps_uplift_mm_month": 0.0, "bulletin_date": "Ottobre 2026",
        },
    })
    assert module.fetch_gps_vesuvio.__wrapped__()["source_type"] == "unavailable"
    assert module.fetch_gps_ischia.__wrapped__()["source_type"] == "unavailable"


def test_official_bulletin_resolver_follows_changed_navigation_and_year_slugs(monkeypatch):
    import ingv_monitor as module
    year = module.datetime.now().year
    pages = [
        '<a href="/index.php/monitoraggio-e-infrastrutture/">Monitoraggio e Infrastrutture</a>',
        '<a href="/index.php/nuovo-monitor/bollettini">Bollettini di sorveglianza</a>',
        '<a href="/index.php/nuovo-monitor/bollettini/ves-nuovo">Mensili Vesuvio</a>',
        f'<a href="/index.php/nuovo-monitor/bollettini/ves-nuovo/anno-{year}-99">{year}</a>',
    ]
    calls = []
    class FakeResponse:
        status_code = 200
        def __init__(self, text): self.text = text
    def fake_get(url, **kwargs):
        calls.append(url)
        return FakeResponse(pages.pop(0))
    monkeypatch.setattr(module, "_ingv_get", fake_get)
    category, listing = module._resolve_official_bulletin_pages.__wrapped__("vesuvio", year)
    assert category.endswith("/ves-nuovo")
    assert listing.endswith(f"/anno-{year}-99")
    assert len(calls) == 4


def test_ischia_bulletin_parser_uses_resolved_listing(monkeypatch):
    import pdfplumber
    import ingv_monitor as module
    year = module.datetime.now().year
    category = "https://www.ov.ingv.it/ischia"
    listing_url = f"{category}/anno-{year}-dynamic"
    listing = (
        f'<a href="{listing_url}/2028-bollettino-mensile-ischia-{year}-10/file">'
        'Bollettino mensile Ischia</a>'
    )
    class FakeResponse:
        status_code = 200
        def __init__(self, text="", content=b""):
            self.text, self.content = text, content
    responses = [FakeResponse(listing), FakeResponse(content=b"%PDF-" + b"x" * 50001)]
    calls = []
    def fake_get(url, **kwargs):
        calls.append(url)
        return responses.pop(0)
    class FakePdf:
        pages = [SimpleNamespace(extract_text=lambda: (
            "Nel corso del mese di ottobre 2026, ad Ischia, sono stati registrati "
            "5 terremoti (Mdmax=2.1±0.3). In totale 7 negli ultimi 12 mesi."
        ))]
        def __enter__(self): return self
        def __exit__(self, *args): return False
    monkeypatch.setattr(module, "_ingv_get", fake_get)
    monkeypatch.setattr(module, "_resolve_official_bulletin_pages", lambda area: (category, listing_url))
    monkeypatch.setattr(pdfplumber, "open", lambda data: FakePdf())
    result = module._fetch_bulletin_pdf_ischia.__wrapped__()
    assert result["bulletin_date"] == "Ottobre 2026"
    assert result["seismic_events_month"] == 5
    assert f"/anno-{year}-dynamic/" in result["_pdf_url"]
    assert len(calls) == 2


def test_ischia_bulletin_parser_reports_explicit_zero_events():
    from ingv_monitor import _parse_ischia_bulletin_text
    text = (
        "Nel corso del mese di ottobre 2026, ad Ischia, non sono stati registrati terremoti. "
        "Figura 1.3 - Numero di eventi registrati ad Ischia negli ultimi 12 mesi (in totale 2)."
    )
    result = _parse_ischia_bulletin_text(text)
    assert result["bulletin_date"] == "Ottobre 2026"
    assert result["seismic_events_month"] == 0
    assert result["seismic_events_12m"] == 2
    assert "seismic_md_max_month" not in result


def test_pdf_discovery_survives_a_changed_slug():
    from bs4 import BeautifulSoup
    from ingv_monitor import _find_latest_bulletin_file
    soup = BeautifulSoup(
        '<a href="/reports/file">PDF</a>'
        '<a href="/reports/old-name/file">Bollettino mensile Vesuvio</a>'
        '<a href="/reports/new-name/file">Bollettino mensile Ischia</a>',
        "html.parser",
    )
    assert _find_latest_bulletin_file(soup, "ischia", "https://www.ov.ingv.it/reports/2026") == (
        "https://www.ov.ingv.it/reports/new-name/file"
    )


def test_outdated_youtube_embeds_are_not_rendered():
    source = (ROOT / "visualization.py").read_text()
    assert "jb3BscOyaQU" not in source
    assert "Hllyp_GlG64" not in source
    assert "monitoraggio-sismico-e-vulcanico" in source


def test_donation_links_are_removed_from_the_site():
    source = (ROOT / "app.py").read_text().casefold()
    assert "paypal.me" not in source
    assert "sostieni sismocampania" not in source
    readme = (ROOT / "README.md").read_text().casefold()
    assert "paypal.com/donate" not in readme
    translations = (ROOT / "translations_lib.py").read_text().casefold()
    assert "support_project" not in translations


def test_streamlit_keeps_xsrf_and_cors_protection_enabled():
    import tomllib
    config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())
    assert config["server"]["enableXsrfProtection"] is True
    assert config["server"]["enableCORS"] is True
