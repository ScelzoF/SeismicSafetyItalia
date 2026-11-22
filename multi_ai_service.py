"""
multi_ai_service.py — Sistema Multi-AI per SeismicSafetyItalia
==============================================================
Interroga in parallelo:
  • OpenAI GPT   (Replit AI Integrations o OPENAI_API_KEY diretto)
  • Anthropic Claude (via Replit AI Integrations)
  • Google Gemini    (via Replit AI Integrations)

Produce un'analisi simica consensuale da 3 prospettive AI distinte.
"""

import os
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

# ─────────────────────────────────────────────────────────────
# CIRCUIT BREAKER OpenRouter — evita chiamate inutili se 402
# ─────────────────────────────────────────────────────────────
_OR_UNAVAILABLE_UNTIL: float = 0.0   # timestamp unix
_OR_LOCK = threading.Lock()
_OR_SKIP_SECONDS = 1800              # 30 minuti

def _openrouter_is_down() -> bool:
    return time.time() < _OR_UNAVAILABLE_UNTIL

def _mark_openrouter_down() -> None:
    global _OR_UNAVAILABLE_UNTIL
    with _OR_LOCK:
        _OR_UNAVAILABLE_UNTIL = time.time() + _OR_SKIP_SECONDS

# ─────────────────────────────────────────────────────────────
# PROVIDER CREDENTIAL RESOLVER — riletto ad ogni chiamata
# Priorità: Replit AI Integrations proxy → OPENAI_API_KEY diretto
# ─────────────────────────────────────────────────────────────

def _get_openai_creds():
    """Restituisce (base_url, api_key, model) leggendo le env vars live.
    Priorità: Replit proxy → OPENAI_API_KEY → OpenRouter (skip se circuit breaker aperto)."""
    base = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    key  = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")
    if base and key:
        return base, key, "gpt-4o"
    direct = os.environ.get("OPENAI_API_KEY", "")
    if direct:
        return "https://api.openai.com/v1", direct, "gpt-4o"
    try:
        import streamlit as st
        direct = st.secrets.get("OPENAI_API_KEY", "")
        if direct:
            return "https://api.openai.com/v1", direct, "gpt-4o"
    except Exception:
        pass
    # Fallback OpenRouter — saltato se circuit breaker aperto (402 recente)
    if not _openrouter_is_down():
        or_key = _get_openrouter_key()
        if or_key:
            return "https://openrouter.ai/api/v1", or_key, "openai/gpt-4o"
    return "", "", ""


def _get_openrouter_key() -> str:
    """Restituisce la chiave OpenRouter se disponibile."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("OPENROUTER_API_KEY", "")
    except Exception:
        return ""


def _get_claude_creds():
    """Replit proxy → ANTHROPIC_API_KEY → OpenRouter (skip se circuit breaker aperto)."""
    base = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", "")
    key  = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "")
    if base and key:
        return base, key, "claude-haiku-4-5", "native"
    direct = os.environ.get("ANTHROPIC_API_KEY", "")
    if direct:
        return "https://api.anthropic.com", direct, "claude-3-5-haiku-20241022", "native"
    try:
        import streamlit as st
        direct = st.secrets.get("ANTHROPIC_API_KEY", "")
        if direct:
            return "https://api.anthropic.com", direct, "claude-3-5-haiku-20241022", "native"
    except Exception:
        pass
    if not _openrouter_is_down():
        or_key = _get_openrouter_key()
        if or_key:
            return "https://openrouter.ai/api/v1", or_key, "anthropic/claude-3-haiku", "openrouter"
    return "", "", "", ""


def _get_gemini_creds():
    """Replit proxy → GOOGLE_API_KEY → OpenRouter (skip se circuit breaker aperto)."""
    base = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL", "")
    key  = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY", "")
    if base and key:
        return base, key, "gemini-2.5-flash", "native"
    for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        direct = os.environ.get(var, "")
        if direct:
            return "https://generativelanguage.googleapis.com/v1beta", direct, "gemini-2.0-flash", "native"
    try:
        import streamlit as st
        for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            direct = st.secrets.get(var, "")
            if direct:
                return "https://generativelanguage.googleapis.com/v1beta", direct, "gemini-2.0-flash", "native"
    except Exception:
        pass
    if not _openrouter_is_down():
        or_key = _get_openrouter_key()
        if or_key:
            return "https://openrouter.ai/api/v1", or_key, "google/gemini-2.0-flash-001", "openrouter"
    return "", "", "", ""


def _providers_status() -> dict:
    """Stato disponibilità provider — calcolato live."""
    ob, ok, _ = _get_openai_creds()
    cb, ck, _, _ = _get_claude_creds()
    gb, gk, _, _ = _get_gemini_creds()
    return {
        "gpt":    bool(ob and ok),
        "claude": bool(cb and ck),
        "gemini": bool(gb and gk),
    }


# Compatibilità con codice esterno che legge _PROVIDERS_OK
_PROVIDERS_OK = _providers_status()


# ─────────────────────────────────────────────────────────────
# FREE FALLBACK — g4f (nessuna API key richiesta)
# ─────────────────────────────────────────────────────────────

def _ask_g4f_free(prompt: str, system: str = "") -> str:
    """Fallback completamente gratuito via g4f (GPT4Free).
    Usato solo quando tutti i provider a pagamento falliscono (es. 402)."""
    try:
        from g4f.client import Client as _G4FClient
        client = _G4FClient()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            timeout=30,
        )
        text = r.choices[0].message.content or ""
        if text.strip():
            return text.strip()
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────────────────────
# SINGLE-PROVIDER CALLS
# ─────────────────────────────────────────────────────────────

def _ask_gpt(
    prompt: str,
    system: str = "",
    model: str = "gpt-4o",
    allow_fallback: bool = True,
) -> str | None:
    """Chiama OpenAI GPT via Replit proxy, API diretta o OpenRouter.
    Fallback finale: g4f (gratuito, nessuna API key)."""
    base, key, effective_model = _get_openai_creds()
    if not (base and key):
        if allow_fallback:
            return _ask_g4f_free(prompt, system) or "GPT non disponibile (env vars mancanti)."
        return None
    try:
        return _openai_compat_call(base, key, effective_model, prompt, system)
    except Exception as e:
        err = str(e)
        if "402" in err or "Payment Required" in err:
            if "openrouter" in base:
                _mark_openrouter_down()
            if not allow_fallback:
                return None
            result = _ask_g4f_free(prompt, system)
            if result:
                return result
            return "⚠️ Commento AI temporaneamente non disponibile (credito esaurito)."
        if not allow_fallback:
            return None
        return f"[GPT errore: {err[:120]}]"


_CLAUDE_FALLBACK_SYSTEM = """Sei un sismologo statistico specializzato nell'analisi probabilistica del rischio.
Analizza i dati forniti con un approccio quantitativo: concentrati su frequenza, distribuzione
delle magnitudo, trend temporali e implicazioni statistiche. Rispondi in italiano, 3-5 frasi concise."""

_GEMINI_FALLBACK_SYSTEM = """Sei un esperto di protezione civile e comunicazione del rischio sismico.
Analizza i dati forniti dal punto di vista della sicurezza pubblica: cosa significa per i residenti,
quali precauzioni sono consigliate, come interpretare i livelli di allerta. Rispondi in italiano, 3-5 frasi."""


def _openai_compat_call(base: str, key: str, model: str, prompt: str, system: str) -> str:
    """Chiamata OpenAI-compatibile (funziona con Replit proxy, OpenAI, OpenRouter)."""
    import openai
    extra = {}
    if "openrouter.ai" in base:
        extra["default_headers"] = {
            "HTTP-Referer": "https://sismocampania.streamlit.app",
            "X-Title": "SismoCampania",
        }
    client = openai.OpenAI(base_url=base, api_key=key, **extra)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    r = client.chat.completions.create(model=model, messages=messages, max_tokens=600)
    return r.choices[0].message.content.strip()


def _ask_claude(
    prompt: str,
    system: str = "",
    model: str = "claude-haiku-4-5",
    allow_fallback: bool = True,
) -> str | None:
    """Chiama Claude: nativo Anthropic → OpenRouter → GPT-4o fallback."""
    cb, ck, cm, provider = _get_claude_creds()
    if cb and ck:
        try:
            if provider == "native":
                import anthropic
                client = anthropic.Anthropic(base_url=cb, api_key=ck)
                kwargs = {"model": cm, "max_tokens": 600,
                          "messages": [{"role": "user", "content": prompt}]}
                if system:
                    kwargs["system"] = system
                r = client.messages.create(**kwargs)
                return r.content[0].text.strip()
            else:
                return _openai_compat_call(cb, ck, cm, prompt, system)
        except Exception as e:
            if not allow_fallback:
                return None
            if "402" in str(e) or "Payment Required" in str(e):
                result = _ask_g4f_free(prompt, system or _CLAUDE_FALLBACK_SYSTEM)
                if result:
                    return result
                return "⚠️ Commento AI temporaneamente non disponibile (credito esaurito)."
    if not allow_fallback:
        return None
    # Fallback GPT-4o con prospettiva statistica
    base, key, mdl = _get_openai_creds()
    if not (base and key):
        return _ask_g4f_free(prompt, system or _CLAUDE_FALLBACK_SYSTEM) or "Claude non disponibile (nessuna API key configurata)."
    try:
        return _openai_compat_call(base, key, mdl, prompt, system or _CLAUDE_FALLBACK_SYSTEM)
    except Exception as e:
        err = str(e)
        if "402" in err or "Payment Required" in err:
            result = _ask_g4f_free(prompt, system or _CLAUDE_FALLBACK_SYSTEM)
            if result:
                return result
            return "⚠️ Commento AI temporaneamente non disponibile (credito esaurito)."
        return f"[Claude errore: {err[:120]}]"


def _ask_gemini(
    prompt: str,
    system: str = "",
    model: str = "gemini-2.5-flash",
    allow_fallback: bool = True,
) -> str | None:
    """Chiama Gemini: nativo Google → OpenRouter → GPT-4o fallback."""
    gb, gk, gm, provider = _get_gemini_creds()
    if gb and gk:
        try:
            if provider == "openrouter":
                return _openai_compat_call(gb, gk, gm, prompt, system)
            # Gemini nativo via REST
            contents = []
            if system:
                contents.append({"role": "user", "parts": [{"text": f"[Sistema]\n{system}"}]})
                contents.append({"role": "model", "parts": [{"text": "Capito."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            payload = {"contents": contents, "generationConfig": {"maxOutputTokens": 600}}
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {gk}"}
            url = f"{gb}/models/{gm}:generateContent"
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                d = r.json()
                parts = d.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                return (parts[0].get("text") or "").strip()
        except Exception as e:
            if not allow_fallback:
                return None
            if "402" in str(e) or "Payment Required" in str(e):
                result = _ask_g4f_free(prompt, system or _GEMINI_FALLBACK_SYSTEM)
                if result:
                    return result
                return "⚠️ Commento AI temporaneamente non disponibile (credito esaurito)."
    if not allow_fallback:
        return None
    # Fallback GPT-4o con prospettiva protezione civile
    base, key, mdl = _get_openai_creds()
    if not (base and key):
        return _ask_g4f_free(prompt, system or _GEMINI_FALLBACK_SYSTEM) or "Gemini non disponibile (nessuna API key configurata)."
    try:
        return _openai_compat_call(base, key, mdl, prompt, system or _GEMINI_FALLBACK_SYSTEM)
    except Exception as e:
        err = str(e)
        if "402" in err or "Payment Required" in err:
            result = _ask_g4f_free(prompt, system or _GEMINI_FALLBACK_SYSTEM)
            if result:
                return result
            return "⚠️ Commento AI temporaneamente non disponibile (credito esaurito)."
        return f"[Gemini errore: {err[:120]}]"


# ─────────────────────────────────────────────────────────────
# PROMPT DI SISTEMA COMUNE — esperto di sismologia campana
# ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Sei un esperto di sismologia vulcanica con specializzazione nell'area campana
(Campi Flegrei, Vesuvio, Ischia). Rispondi in italiano, in modo chiaro e accessibile.
Fornisci un'analisi concisa (3-5 frasi) basata solo sui dati forniti.
Non inventare dati. I dati assenti sono sconosciuti, non indicano assenza di rischio.
Nomina l'area analizzata e cita almeno un indicatore presente nel contesto.
Non prevedere terremoti e non dichiarare allerte, evacuazioni o assenza di pericolo.
La risposta è sperimentale e non è un comunicato ufficiale.
Per comportamenti di sicurezza rimanda a INGV e Protezione Civile."""


def _build_seismic_prompt(area: str, data_ctx: dict) -> str:
    """Costruisce il prompt con il contesto sismico attuale."""
    def fmt(value, decimals=1, signed=False):
        if value is None:
            return "NON DISPONIBILE"
        try:
            number = float(value)
            if not math.isfinite(number):
                return "NON DISPONIBILE"
            return f"{number:+.{decimals}f}" if signed else f"{number:.{decimals}f}"
        except (TypeError, ValueError):
            return "NON DISPONIBILE"

    n_events = data_ctx.get("n_events")
    n_events_text = "NON DISPONIBILE" if n_events is None else str(n_events)
    max_mag    = fmt(data_ctx.get("max_mag"))
    avg_mag    = fmt(data_ctx.get("avg_mag"))
    alert      = data_ctx.get("alert_level") or "NON DISPONIBILE"
    gps        = fmt(data_ctx.get("gps_uplift_mm_month"), signed=True)
    pressure   = fmt(data_ctx.get("pressure_base"))
    temp_base  = fmt(data_ctx.get("temp_base"))
    temp_vetta = data_ctx.get("temp_vetta", None)
    sismai_risk= data_ctx.get("sismai_forecast_label") or "NON DISPONIBILE"
    emsc_n     = data_ctx.get("emsc_n_events")
    isc_n      = data_ctx.get("isc_n_events")
    period     = data_ctx.get("period_days", 90)

    temp_info = f", Temp. vetta: {fmt(temp_vetta)}°C"
    emsc_info = (
        f" (eventi segnalati da EMSC: {emsc_n})" if emsc_n is not None
        else " (dati EMSC: NON DISPONIBILI)"
    )
    isc_info = (
        f" (ISC: {isc_n} nel catalogo storico)" if isc_n is not None and isc_n > 0
        else " (dati ISC: NON DISPONIBILI)" if isc_n is None
        else ""
    )

    return (
        f"Analisi sismica {area} — {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC\n\n"
        f"DATI ULTIMI {period} GIORNI (INGV/USGS{emsc_info}{isc_info}):\n"
        f"- Stato del catalogo: {data_ctx.get('seismic_data_status', 'non verificato')}\n"
        f"- Sismicità: {n_events_text} eventi, Md max {max_mag}, Md media {avg_mag}\n"
        f"- Livello allerta INGV OV: {alert}\n"
        f"- GPS deformazione: {gps} mm/mese\n"
        f"- Pressione atm. base: {pressure} hPa, Temp. base: {temp_base}°C{temp_info}\n"
        f"- Previsione SISMAI (prossimi 7 giorni): rischio {sismai_risk}\n\n"
        f"Fornisci la tua analisi esperta di questo scenario."
    )


def _is_relevant_ai_answer(text: str, area: str) -> bool:
    """Reject empty, provider-error, or clearly off-topic output before display."""
    if not isinstance(text, str) or len(text.strip()) < 40:
        return False
    normalized = text.casefold()
    off_topic_markers = (
        "copilot moved to a new app",
        "install the new copilot",
        "sign in with the same account",
        "history and content will be deleted",
        "microsoft copilot",
    )
    if any(marker in normalized for marker in off_topic_markers):
        return False
    area_markers = {
        "campi flegrei": ("campi flegrei", "flegrei", "pozzuoli", "solfatara"),
        "vesuvio": ("vesuvio", "vesuviana", "vesuviano"),
        "ischia": ("ischia", "ischitano", "ischitana"),
    }
    markers = area_markers.get(area.casefold(), (area.casefold(),))
    scientific_markers = (
        "sismic", "terremot", "magnitudo", "bradisism", "vulcan",
        "eruzione", "allerta", "ingv", "gps", "eventi",
    )
    return (
        any(marker in normalized for marker in markers)
        and any(marker in normalized for marker in scientific_markers)
    )


# ─────────────────────────────────────────────────────────────
# MULTI-AI CONSENSUS — interroga 3 provider in parallelo
# ─────────────────────────────────────────────────────────────

def multi_ai_consensus(area: str, data_ctx: dict) -> dict:
    """
    Interroga GPT-5, Claude e Gemini in parallelo con lo stesso contesto sismico.
    Ritorna dict con risposte individuali + consensus + tempo di esecuzione.
    """
    prompt    = _build_seismic_prompt(area, data_ctx)
    system    = _SYSTEM_PROMPT
    t0        = time.time()
    results   = {"gpt": None, "claude": None, "gemini": None, "consensus": None,
                 "elapsed_s": 0.0, "prompt": prompt, "area": area,
                 "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")}
    provider_results = {}

    def _run_gpt():
        provider_results["gpt"] = _ask_gpt(prompt, system=system, allow_fallback=False)

    def _run_claude():
        provider_results["claude"] = _ask_claude(prompt, system=system, allow_fallback=False)

    def _run_gemini():
        provider_results["gemini"] = _ask_gemini(prompt, system=system, allow_fallback=False)

    threads = [
        threading.Thread(target=_run_gpt),
        threading.Thread(target=_run_claude),
        threading.Thread(target=_run_gemini),
    ]
    for t in threads:
        t.daemon = True
        t.start()
    deadline = time.monotonic() + 30
    for t in threads:
        t.join(timeout=max(0, deadline - time.monotonic()))
    results.update(provider_results.copy())

    results["elapsed_s"] = round(time.time() - t0, 1)

    def _clean(text: str) -> str:
        """Rimuove titoli markdown e tronca a max 5 frasi."""
        if not text:
            return text
        lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
        cleaned = " ".join(" ".join(lines).split())
        sentences = cleaned.split(". ")
        return ". ".join(sentences[:6]).strip()

    # Normalizza le risposte
    for key in ("gpt", "claude", "gemini"):
        if results[key]:
            results[key] = _clean(results[key])

    # Non sostituire provider mancanti con GPT/g4f: i pareri devono essere distinti.
    rejected = []
    for key in ("gpt", "claude", "gemini"):
        candidate = _clean(results.get(key) or "")
        if candidate and _is_relevant_ai_answer(candidate, area):
            results[key] = candidate
        else:
            if candidate:
                rejected.append(key)
            results[key] = None
    results["providers_rejected"] = rejected
    responses_available = [
        results[key] for key in ("gpt", "claude", "gemini") if results[key]
    ]
    results["n_responses"] = len(responses_available)

    if len(responses_available) >= 2:
        results["consensus"] = (
            f"Sono disponibili {len(responses_available)} risposte pertinenti separate. "
            "Confrontale qui sopra: la loro eventuale convergenza non è validazione scientifica."
        )
    elif responses_available:
        results["consensus"] = (
            "È disponibile una sola risposta pertinente: non costituisce un confronto "
            "tra provider né un consenso scientifico."
        )
    else:
        results["consensus"] = (
            "Nessuna risposta pertinente dai provider configurati. "
            "Consulta le fonti ufficiali INGV e Protezione Civile."
        )

    return results


# ─────────────────────────────────────────────────────────────
# QUICK SINGLE-QUESTION (per chat)
# ─────────────────────────────────────────────────────────────

def ask_all_providers(question: str, system: str = "") -> dict:
    """
    Risposta rapida da tutti i provider per una domanda libera.
    Usato dalla chat AI in modalità multi-AI.
    """
    t0 = time.time()
    results = {"gpt": None, "claude": None, "gemini": None}
    provider_results = {}

    sys_ctx = system or _SYSTEM_PROMPT

    def _run_gpt():
        provider_results["gpt"] = _ask_gpt(question, system=sys_ctx)

    def _run_claude():
        provider_results["claude"] = _ask_claude(question, system=sys_ctx)

    def _run_gemini():
        provider_results["gemini"] = _ask_gemini(question, system=sys_ctx)

    threads = [
        threading.Thread(target=_run_gpt),
        threading.Thread(target=_run_claude),
        threading.Thread(target=_run_gemini),
    ]
    for t in threads:
        t.daemon = True
        t.start()
    deadline = time.monotonic() + 25
    for t in threads:
        t.join(timeout=max(0, deadline - time.monotonic()))
    results.update(provider_results.copy())

    results["elapsed_s"] = round(time.time() - t0, 1)
    results["providers_ok"] = _PROVIDERS_OK.copy()
    return results


# ─────────────────────────────────────────────────────────────
# STATUS CHECK
# ─────────────────────────────────────────────────────────────

def providers_status() -> dict:
    """Ritorna quali provider hanno credenziali configurate, non la loro salute live."""
    configured = _providers_status()
    return {
        "gpt":    {"available": configured["gpt"],    "model": "OpenAI (chiave configurata)"},
        "claude": {"available": configured["claude"], "model": "Anthropic (chiave configurata)"},
        "gemini": {"available": configured["gemini"], "model": "Gemini (chiave configurata)"},
    }
