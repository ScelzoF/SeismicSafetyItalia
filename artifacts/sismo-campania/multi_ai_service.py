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
# PROVIDER CONFIGS
# Priorità: Replit AI Integrations proxy → API key diretta
# ─────────────────────────────────────────────────────────────

_OPENAI_BASE     = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
_OPENAI_KEY      = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")
_ANTHROPIC_BASE  = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", "")
_ANTHROPIC_KEY   = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "")
_GEMINI_BASE     = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL", "")
_GEMINI_KEY      = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY", "")

# Fallback: OpenAI API key diretta (Streamlit Cloud / altro host)
_OPENAI_DIRECT_KEY = os.environ.get("OPENAI_API_KEY", "")
if not (_OPENAI_BASE and _OPENAI_KEY) and _OPENAI_DIRECT_KEY:
    _OPENAI_BASE = "https://api.openai.com/v1"
    _OPENAI_KEY  = _OPENAI_DIRECT_KEY
    _OPENAI_MODEL_OVERRIDE = "gpt-4o"
else:
    _OPENAI_MODEL_OVERRIDE = ""

_PROVIDERS_OK = {
    "gpt":    bool(_OPENAI_BASE and _OPENAI_KEY),
    "claude": bool(_ANTHROPIC_BASE and _ANTHROPIC_KEY),
    "gemini": bool(_GEMINI_BASE and _GEMINI_KEY),
}


# ─────────────────────────────────────────────────────────────
# SINGLE-PROVIDER CALLS
# ─────────────────────────────────────────────────────────────

def _ask_gpt(prompt: str, system: str = "", model: str = "gpt-5.1") -> str:
    """Chiama OpenAI GPT via Replit proxy o API diretta."""
    if not _PROVIDERS_OK["gpt"]:
        return "GPT non disponibile (env vars mancanti)."
    effective_model = _OPENAI_MODEL_OVERRIDE or model
    try:
        import openai
        client = openai.OpenAI(base_url=_OPENAI_BASE, api_key=_OPENAI_KEY)
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


def _ask_claude(prompt: str, system: str = "", model: str = "claude-haiku-4-5") -> str:
    """Chiama Anthropic Claude via Replit proxy."""
    if not _PROVIDERS_OK["claude"]:
        return "Claude non disponibile (env vars mancanti)."
    try:
        import anthropic
        client = anthropic.Anthropic(base_url=_ANTHROPIC_BASE, api_key=_ANTHROPIC_KEY)
        kwargs = {
            "model": model,
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        r = client.messages.create(**kwargs)
        return r.content[0].text.strip()
    except Exception as e:
        return f"[Claude errore: {str(e)[:120]}]"


def _ask_gemini(prompt: str, system: str = "", model: str = "gemini-2.5-flash") -> str:
    """Chiama Google Gemini via Replit proxy (HTTP diretto)."""
    if not _PROVIDERS_OK["gemini"]:
        return "Gemini non disponibile (env vars mancanti)."
    try:
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": f"[Contesto sistema]\n{system}"}]})
            contents.append({"role": "model", "parts": [{"text": "Capito, procedo."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        payload = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 600},
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_GEMINI_KEY}",
        }
        url = f"{_GEMINI_BASE}/models/{model}:generateContent"
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            d = r.json()
            parts = d.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
            return (parts[0].get("text") or "").strip()
        return f"[Gemini errore {r.status_code}: {r.text[:120]}]"
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
