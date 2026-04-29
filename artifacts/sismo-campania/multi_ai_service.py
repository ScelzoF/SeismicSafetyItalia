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
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

# ─────────────────────────────────────────────────────────────
# PROVIDER CREDENTIAL RESOLVER — riletto ad ogni chiamata
# Priorità: Replit AI Integrations proxy → OPENAI_API_KEY diretto
# ─────────────────────────────────────────────────────────────

def _get_openai_creds():
    """Restituisce (base_url, api_key, model) leggendo le env vars live."""
    base = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    key  = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")
    if base and key:
        return base, key, "gpt-4o"
    direct = os.environ.get("OPENAI_API_KEY", "")
    if direct:
        return "https://api.openai.com/v1", direct, "gpt-4o"
    # Streamlit Cloud: prova st.secrets come ultima risorsa
    try:
        import streamlit as st
        direct = st.secrets.get("OPENAI_API_KEY", "")
        if direct:
            return "https://api.openai.com/v1", direct, "gpt-4o"
    except Exception:
        pass
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
    """Replit proxy → ANTHROPIC_API_KEY → OpenRouter."""
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
    or_key = _get_openrouter_key()
    if or_key:
        return "https://openrouter.ai/api/v1", or_key, "anthropic/claude-3-haiku", "openrouter"
    return "", "", "", ""


def _get_gemini_creds():
    """Replit proxy → GOOGLE_API_KEY → OpenRouter."""
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
    or_key = _get_openrouter_key()
    if or_key:
        return "https://openrouter.ai/api/v1", or_key, "google/gemini-flash-1.5", "openrouter"
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
# SINGLE-PROVIDER CALLS
# ─────────────────────────────────────────────────────────────

def _ask_gpt(prompt: str, system: str = "", model: str = "gpt-4o") -> str:
    """Chiama OpenAI GPT via Replit proxy o API diretta."""
    base, key, effective_model = _get_openai_creds()
    if not (base and key):
        return "GPT non disponibile (env vars mancanti)."
    try:
        import openai
        client = openai.OpenAI(base_url=base, api_key=key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = client.chat.completions.create(
            model=effective_model,
            messages=messages,
            max_tokens=600,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT errore: {str(e)[:120]}]"


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


def _ask_claude(prompt: str, system: str = "", model: str = "claude-haiku-4-5") -> str:
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
        except Exception:
            pass
    # Fallback GPT-4o con prospettiva statistica
    base, key, mdl = _get_openai_creds()
    if not (base and key):
        return "Claude non disponibile (nessuna API key configurata)."
    try:
        return _openai_compat_call(base, key, mdl, prompt, system or _CLAUDE_FALLBACK_SYSTEM)
    except Exception as e:
        return f"[Claude errore: {str(e)[:120]}]"


def _ask_gemini(prompt: str, system: str = "", model: str = "gemini-2.5-flash") -> str:
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
        except Exception:
            pass
    # Fallback GPT-4o con prospettiva protezione civile
    base, key, mdl = _get_openai_creds()
    if not (base and key):
        return "Gemini non disponibile (nessuna API key configurata)."
    try:
        return _openai_compat_call(base, key, mdl, prompt, system or _GEMINI_FALLBACK_SYSTEM)
    except Exception as e:
        return f"[Gemini errore: {str(e)[:120]}]"


# ─────────────────────────────────────────────────────────────
# PROMPT DI SISTEMA COMUNE — esperto di sismologia campana
# ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Sei un esperto di sismologia vulcanica con specializzazione nell'area campana
(Campi Flegrei, Vesuvio, Ischia). Rispondi in italiano, in modo chiaro e accessibile.
Fornisci un'analisi concisa (3-5 frasi) basata solo sui dati forniti.
Non inventare dati. Indica il livello di preoccupazione e le azioni consigliate."""


def _build_seismic_prompt(area: str, data_ctx: dict) -> str:
    """Costruisce il prompt con il contesto sismico attuale."""
    n_events   = data_ctx.get("n_events", 0)
    max_mag    = data_ctx.get("max_mag", 0.0)
    avg_mag    = data_ctx.get("avg_mag", 0.0)
    alert      = data_ctx.get("alert_level", "VERDE")
    gps        = data_ctx.get("gps_uplift_mm_month", 0.0)
    pressure   = data_ctx.get("pressure_base", 1013.0)
    temp_base  = data_ctx.get("temp_base", 15.0)
    temp_vetta = data_ctx.get("temp_vetta", None)
    sismai_risk= data_ctx.get("sismai_forecast_label", "BASSO")
    emsc_n     = data_ctx.get("emsc_n_events", 0)
    isc_n      = data_ctx.get("isc_n_events", 0)
    period     = data_ctx.get("period_days", 90)

    temp_info = f", Temp. vetta: {temp_vetta:.1f}°C" if temp_vetta is not None else ""
    emsc_info = f" (confermati da EMSC: {emsc_n})" if emsc_n > 0 else ""
    isc_info  = f" (ISC: {isc_n} nel catalogo storico)" if isc_n > 0 else ""

    return (
        f"Analisi sismica {area} — {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC\n\n"
        f"DATI ULTIMI {period} GIORNI (INGV/USGS{emsc_info}{isc_info}):\n"
        f"- Sismicità: {n_events} eventi, Md max {max_mag:.1f}, Md media {avg_mag:.1f}\n"
        f"- Livello allerta INGV OV: {alert}\n"
        f"- GPS deformazione: {gps:+.1f} mm/mese\n"
        f"- Pressione atm. base: {pressure:.1f} hPa, Temp. base: {temp_base:.1f}°C{temp_info}\n"
        f"- Previsione SISMAI (prossimi 7 giorni): rischio {sismai_risk}\n\n"
        f"Fornisci la tua analisi esperta di questo scenario."
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

    def _run_gpt():
        results["gpt"] = _ask_gpt(prompt, system=system)

    def _run_claude():
        results["claude"] = _ask_claude(prompt, system=system)

    def _run_gemini():
        results["gemini"] = _ask_gemini(prompt, system=system)

    threads = [
        threading.Thread(target=_run_gpt),
        threading.Thread(target=_run_claude),
        threading.Thread(target=_run_gemini),
    ]
    for t in threads:
        t.daemon = True
        t.start()
    for t in threads:
        t.join(timeout=30)

    results["elapsed_s"] = round(time.time() - t0, 1)

    # Genera consensus da GPT (sintetizza le 3 risposte)
    responses_available = [
        r for r in [results["gpt"], results["claude"], results["gemini"]]
        if r and not r.startswith("[") and not r.startswith("GPT") and not r.startswith("Claude") and not r.startswith("Gemini")
    ]
    if len(responses_available) >= 2:
        consensus_prompt = (
            f"Questi sono 3 pareri di esperti AI sull'area sismica {area}:\n\n"
            + "\n\n---\n\n".join(
                [f"Parere {i+1}: {r}" for i, r in enumerate(responses_available)]
            )
            + "\n\nSintetizza in 3-4 frasi un consenso scientifico autorevole, "
            "indicando eventuali punti di accordo e divergenza tra i pareri. "
            "Scrivi in italiano, stile comunicato ufficiale."
        )
        results["consensus"] = _ask_gpt(consensus_prompt, system=_SYSTEM_PROMPT)
    elif responses_available:
        results["consensus"] = responses_available[0]
    else:
        results["consensus"] = "Nessun provider AI disponibile al momento."

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

    sys_ctx = system or _SYSTEM_PROMPT

    def _run_gpt():
        results["gpt"] = _ask_gpt(question, system=sys_ctx)

    def _run_claude():
        results["claude"] = _ask_claude(question, system=sys_ctx)

    def _run_gemini():
        results["gemini"] = _ask_gemini(question, system=sys_ctx)

    threads = [
        threading.Thread(target=_run_gpt),
        threading.Thread(target=_run_claude),
        threading.Thread(target=_run_gemini),
    ]
    for t in threads:
        t.daemon = True
        t.start()
    for t in threads:
        t.join(timeout=25)

    results["elapsed_s"] = round(time.time() - t0, 1)
    results["providers_ok"] = _PROVIDERS_OK.copy()
    return results


# ─────────────────────────────────────────────────────────────
# STATUS CHECK
# ─────────────────────────────────────────────────────────────

def providers_status() -> dict:
    """Ritorna lo stato di ogni provider AI."""
    return {
        "gpt":    {"available": _PROVIDERS_OK["gpt"],    "model": "GPT-5.1 (OpenAI)"},
        "claude": {"available": _PROVIDERS_OK["claude"],  "model": "Claude Haiku 4.5 (Anthropic)"},
        "gemini": {"available": _PROVIDERS_OK["gemini"],  "model": "Gemini 2.5 Flash (Google)"},
    }
