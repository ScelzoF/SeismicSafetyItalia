"""
ai_chat.py — Assistente AI per SeismicSafetyItalia
====================================================
Chat AI reale, 100% gratuita, senza API key.

Strategia dual-mode:
  1. Replit dev → proxy AI_INTEGRATIONS (localhost)
  2. Ovunque altro (Streamlit Cloud, ecc.) → g4f PollinationsAI
     • vera AI, nessuna registrazione, nessun limite mensile

g4f usa provider pubblici (Pollinations, ecc.) — zero key richieste.
"""

import os
import time
import requests
import streamlit as st
from datetime import datetime


# ── Replit proxy client ───────────────────────────────────────────────────────

def _make_replit_client():
    """Client via proxy Replit (solo in dev Replit)."""
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    if not base_url:
        return None, None
    try:
        from openai import OpenAI
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "replit-proxy")
        return OpenAI(api_key=api_key, base_url=base_url), "replit"
    except Exception:
        return None, None


# ── g4f multi-provider con retry ─────────────────────────────────────────────

# Catena di provider in ordine di qualità/affidabilità.
# Ogni entry: (nome_provider, modello_da_usare | None = default del provider)
# Se un provider fallisce 2 volte → si passa al successivo automaticamente.
_G4F_PROVIDER_CHAIN = [
    # Tier 1 — GPT-4 class, ottimizzati per italiano
    ("ItalyGPT",           "gpt-4o"),
    ("PollinationsAI",     "openai-fast"),
    ("Chatai",             "gpt-4o-mini"),
    ("Yqcloud",            "gpt-4"),
    ("WeWordle",           "gpt-4"),
    ("AnyProvider",        "gpt-4o"),
    # Tier 2 — Large open-source models (120B+)
    ("GradientNetwork",    "GPT OSS 120B"),
    ("Groq",               None),          # openai/gpt-oss-120b
    ("Nvidia",             None),          # gpt-oss-120b
    ("HuggingFace",        None),          # gpt-oss-120b
    ("OpenRouterFree",     None),          # vari modelli free
    # Tier 3 — Qwen & altri modelli avanzati
    ("Qwen_Qwen_3",        "qwen-3-32b"),
    ("Qwen_Qwen_2_5_Max",  "qwen-2.5-max"),
    ("Qwen_Qwen_2_72B",    None),
    ("MetaAI",             None),          # Llama 3
    ("DeepInfra",          None),
    ("Perplexity",         "turbo"),
    # Tier 4 — Fallback finale
    ("LMArena",            None),
    ("ApiAirforce",        None),
    ("TeachAnything",      None),
    ("Pi",                 None),
]

def _g4f_call(messages, max_tokens=450, timeout=35):
    """
    Scorre la catena di provider in ordine di priorità.
    Per ogni provider: 2 tentativi con backoff (1s, 2s).
    Al primo testo valido → ritorna subito senza provare altri.
    Lancia RuntimeError solo se TUTTI i provider falliscono.
    """
    try:
        from g4f.client import Client
        import g4f.Provider as Provider
    except ImportError:
        raise RuntimeError("g4f non installato")

    last_err = None
    for provider_name, model_override in _G4F_PROVIDER_CHAIN:
        provider_cls = getattr(Provider, provider_name, None)
        if provider_cls is None:
            continue
        for attempt in range(2):   # 2 tentativi per provider
            try:
                client = Client(provider=provider_cls)
                kwargs = {"messages": messages, "timeout": timeout}
                if model_override:
                    kwargs["model"] = model_override
                resp = client.chat.completions.create(**kwargs)
                text = (resp.choices[0].message.content or "").strip()
                if text:
                    return text, provider_name   # successo → uscita immediata
            except Exception as e:
                last_err = e
                if attempt == 0:
                    time.sleep(1.0)   # 1s prima del retry
        # provider esaurito → prossimo
    raise RuntimeError(f"Tutti i {len(_G4F_PROVIDER_CHAIN)} provider AI non disponibili. Ultimo: {last_err}")


def _pollinations_call(messages, max_tokens=450, timeout=20):
    """Fallback diretto a PollinationsAI via HTTP — nessuna dipendenza extra."""
    try:
        payload = {
            "model": "openai",
            "messages": messages,
            "max_tokens": max_tokens,
            "private": True,
        }
        resp = requests.post(
            "https://text.pollinations.ai/openai",
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if text:
                return text
        # fallback GET semplice
        prompt = " ".join(m.get("content", "") for m in messages[-2:])
        resp2 = requests.get(
            "https://text.pollinations.ai/" + requests.utils.quote(prompt[:500]),
            timeout=timeout,
        )
        if resp2.status_code == 200 and resp2.text.strip():
            return resp2.text.strip()
    except Exception:
        pass
    raise RuntimeError("PollinationsAI non raggiungibile")


def _get_client():
    """Ritorna (client, mode) con priorità: Replit proxy → g4f → PollinationsAI diretto."""
    client, mode = _make_replit_client()
    if client:
        return client, mode
    try:
        import g4f  # noqa: F401
        return True, "g4f"
    except ImportError:
        return True, "pollinations"


def _chat_complete(client, mode, messages, max_tokens=450):
    """Esegue la chiamata AI. Ritorna il testo o lancia eccezione."""
    if mode == "replit":
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_completion_tokens=max_tokens,
            stream=False,
        )
        return resp.choices[0].message.content or ""

    elif mode == "g4f":
        text, provider_used = _g4f_call(messages, max_tokens=max_tokens)
        st.session_state["_ai_provider_used"] = provider_used
        return text

    elif mode == "pollinations":
        st.session_state["_ai_provider_used"] = "PollinationsAI"
        return _pollinations_call(messages, max_tokens=max_tokens)

    raise RuntimeError("Client mode sconosciuto")


# ── Weather context helper ────────────────────────────────────────────────────

_WMO_CODES = {
    0:"Cielo sereno", 1:"Prevalentemente sereno", 2:"Parzialmente nuvoloso",
    3:"Nuvoloso", 45:"Nebbia", 48:"Nebbia ghiacciata",
    51:"Pioggerella leggera", 53:"Pioggerella moderata", 55:"Pioggerella intensa",
    61:"Pioggia leggera", 63:"Pioggia moderata", 65:"Pioggia intensa",
    71:"Neve leggera", 73:"Neve moderata", 75:"Neve intensa",
    80:"Rovesci leggeri", 81:"Rovesci moderati", 82:"Rovesci intensi",
    95:"Temporale", 96:"Temporale con grandine", 99:"Temporale con grandine intensa",
}

_CAMPANIA_CITIES = [
    ("Napoli",           40.8518, 14.2681),
    ("Salerno",          40.6824, 14.7681),
    ("Caserta",          41.0729, 14.3328),
    ("Avellino",         40.9146, 14.7914),
    ("Pozzuoli",         40.8228, 14.1247),
    ("Torre Annunziata", 40.7491, 14.4570),
    ("Ischia",           40.7310, 13.9497),
]

# Lookup completo città italiane per geocoding dinamico in chat
_ITALY_CITIES: dict[str, tuple[float, float]] = {
    # Campania
    "napoli": (40.8518, 14.2681), "naples": (40.8518, 14.2681),
    "salerno": (40.6824, 14.7681), "caserta": (41.0729, 14.3328),
    "avellino": (40.9146, 14.7914), "benevento": (41.1297, 14.7811),
    "pozzuoli": (40.8228, 14.1247), "torre annunziata": (40.7491, 14.4570),
    "ischia": (40.7310, 13.9497), "ercolano": (40.8063, 14.3540),
    "pompei": (40.7503, 14.5004), "castellammare di stabia": (40.7031, 14.4814),
    "nola": (40.9262, 14.5264), "pomigliano d'arco": (40.9117, 14.3907),
    "battipaglia": (40.6085, 14.9852), "eboli": (40.6158, 15.0553),
    # Lazio
    "roma": (41.9028, 12.4964), "rome": (41.9028, 12.4964),
    "latina": (41.4677, 12.9035), "frosinone": (41.6405, 13.3448),
    "viterbo": (42.4167, 12.1056), "rieti": (42.4040, 12.8566),
    # Puglia
    "bari": (41.1171, 16.8719), "taranto": (40.4644, 17.2470),
    "foggia": (41.4620, 15.5449), "brindisi": (40.6326, 17.9402),
    "lecce": (40.3515, 18.1750),
    # Basilicata
    "potenza": (40.6390, 15.8050), "matera": (40.6664, 16.6043),
    # Calabria
    "catanzaro": (38.9100, 16.5900), "reggio calabria": (38.1112, 15.6617),
    "cosenza": (39.3087, 16.2534), "crotone": (39.0802, 17.1295),
    "vibo valentia": (38.6756, 16.0970),
    # Sicilia
    "palermo": (38.1157, 13.3615), "catania": (37.5079, 15.0830),
    "messina": (38.1938, 15.5540), "agrigento": (37.3111, 13.5765),
    "trapani": (38.0176, 12.5365), "siracusa": (37.0694, 15.2866),
    "ragusa": (36.9275, 14.7172),
    # Campania/Calabria border
    "paola": (39.3607, 16.0340), "scalea": (39.8167, 15.7833),
    # Nord
    "milano": (45.4654, 9.1866), "milan": (45.4654, 9.1866),
    "torino": (45.0703, 7.6869), "turin": (45.0703, 7.6869),
    "genova": (44.4056, 8.9463), "genoa": (44.4056, 8.9463),
    "venezia": (45.4408, 12.3155), "venice": (45.4408, 12.3155),
    "bologna": (44.4949, 11.3426), "firenze": (43.7696, 11.2558),
    "florence": (43.7696, 11.2558), "verona": (45.4384, 10.9916),
    "brescia": (45.5416, 10.2118), "padova": (45.4064, 11.8768),
    "trieste": (45.6496, 13.7681), "trento": (46.0748, 11.1217),
    "l'aquila": (42.3498, 13.3994), "pescara": (42.4618, 14.2159),
    "ancona": (43.6158, 13.5189), "perugia": (43.1107, 12.3908),
    "amalfi": (40.6343, 14.6024), "positano": (40.6282, 14.4863),
    "sorrento": (40.6262, 14.3773), "capri": (40.5509, 14.2333),
}


def _detect_city_in_text(text: str) -> tuple[str, float, float] | None:
    """Rileva il nome di una città italiana nel testo — restituisce (nome, lat, lon)."""
    text_lower = text.lower()
    # Cerca prima le corrispondenze più lunghe (evita "bari" in "barista")
    for city_key in sorted(_ITALY_CITIES.keys(), key=len, reverse=True):
        import re as _re
        if _re.search(rf'\b{_re.escape(city_key)}\b', text_lower):
            lat, lon = _ITALY_CITIES[city_key]
            display = city_key.title()
            return display, lat, lon
    return None

def _fetch_ai_weather(lat: float = 40.85, lon: float = 14.27, city: str = "Napoli") -> str:
    """
    Fetcha meteo Open-Meteo per il punto indicato (default Napoli).
    Ritorna una stringa di contesto per l'AI. Cache 30 min in session_state.
    """
    cache_key = f"_ai_weather_{lat:.2f}_{lon:.2f}"
    ts_key = f"_ai_weather_ts_{lat:.2f}_{lon:.2f}"
    now = time.time()

    cached = st.session_state.get(cache_key)
    ts = st.session_state.get(ts_key, 0)
    if cached and (now - ts) < 1800:   # 30 min cache
        return cached

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,apparent_temperature,precipitation,"
            f"weather_code,wind_speed_10m,wind_direction_10m,relative_humidity_2m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,precipitation_probability_max"
            f"&timezone=Europe%2FRome&forecast_days=3"
        )
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return ""
        d = r.json()
        cur = d.get("current", {})
        daily = d.get("daily", {})

        wcode = cur.get("weather_code", 0)
        desc = _WMO_CODES.get(wcode, "N/D")
        temp = cur.get("temperature_2m", "N/D")
        feels = cur.get("apparent_temperature", "N/D")
        prec = cur.get("precipitation", 0)
        wind = cur.get("wind_speed_10m", "N/D")
        hum = cur.get("relative_humidity_2m", "N/D")

        lines = [
            f"METEO LIVE — {city} (Open-Meteo, aggiornato ora):",
            f"  Condizioni: {desc}",
            f"  Temperatura: {temp}°C (percepita {feels}°C)",
            f"  Precipitazioni ultima ora: {prec} mm",
            f"  Vento: {wind} km/h",
            f"  Umidità: {hum}%",
            "",
            "  PREVISIONI 3 GIORNI:",
        ]

        times = daily.get("time", [])
        for i, date in enumerate(times[:3]):
            wc = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
            tmax = daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else "N/D"
            tmin = daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else "N/D"
            psum = daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0
            pprob = daily.get("precipitation_probability_max", [])[i] if i < len(daily.get("precipitation_probability_max", [])) else 0
            dc = _WMO_CODES.get(wc, "N/D")
            lines.append(f"  {date}: {dc}, {tmin}–{tmax}°C, pioggia {psum}mm (prob {pprob}%)")

        lines.append("")
        result = "\n".join(lines)
        st.session_state[cache_key] = result
        st.session_state[ts_key] = now
        return result
    except Exception:
        return ""


# ── Context builder ───────────────────────────────────────────────────────────

def _build_context(earthquake_data, bulletin_cf, bulletin_ves, alert_level,
                   gps_data, aq_data, anomaly_cf, pattern_cf, bvalue_cf,
                   weather_ctx: str = "") -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = [
        f"CONTESTO DATI SISMICI — {now} (dati reali INGV/USGS):",
        "",
        "ALLERTA UFFICIALE INGV:",
        f"  Campi Flegrei: {alert_level.get('campi_flegrei','GIALLO')} "
        f"(fonte: {alert_level.get('source','')})",
        f"  Vesuvio: {alert_level.get('vesuvio','VERDE')}",
        f"  Ischia: {alert_level.get('ischia','VERDE')}",
        "",
    ]

    if earthquake_data is not None and not earthquake_data.empty:
        total = len(earthquake_data)
        from data_service import filter_area_earthquakes
        cf_df  = filter_area_earthquakes(earthquake_data, "campi_flegrei")
        ves_df = filter_area_earthquakes(earthquake_data, "vesuvio")
        isc_df = filter_area_earthquakes(earthquake_data, "ischia")
        lines += [
            "SISMICITÀ RECENTE (ultimi 7 giorni):",
            f"  Totale Italia: {total} eventi",
            f"  Campi Flegrei: {len(cf_df)} eventi",
            f"  Vesuvio: {len(ves_df)} eventi",
            f"  Ischia: {len(isc_df)} eventi",
        ]
        if not cf_df.empty:
            lines.append(f"  CF magnitudo max: {cf_df['magnitude'].max():.1f}, "
                         f"media: {cf_df['magnitude'].mean():.1f}")
        if not ves_df.empty:
            lines.append(f"  Ves magnitudo max: {ves_df['magnitude'].max():.1f}, "
                         f"media: {ves_df['magnitude'].mean():.1f}")
        if not isc_df.empty:
            lines.append(f"  Ischia magnitudo max: {isc_df['magnitude'].max():.1f}, "
                         f"media: {isc_df['magnitude'].mean():.1f}")
        lines.append("")

    if bulletin_cf:
        lines += [
            f"BOLLETTINO INGV OV — Campi Flegrei ({bulletin_cf.get('bulletin_date','')}):",
            f"  Temperatura fumarola Bocca Grande: {bulletin_cf.get('fumarole_temp_bocca_grande','N/D')}°C",
            f"  Flusso CO2: {bulletin_cf.get('co2_flux_td','N/D')} t/giorno",
            f"  Radon: {bulletin_cf.get('radon_bq_m3','N/D')} Bq/m³",
            f"  Sollevamento GPS: {bulletin_cf.get('gps_uplift_mm_month','N/D')} mm/mese",
            "",
        ]

    if bulletin_ves:
        lines += [
            f"BOLLETTINO INGV OV — Vesuvio ({bulletin_ves.get('bulletin_date','')}):",
            f"  CO2 background: {bulletin_ves.get('co2_background_ppm','N/D')} ppm",
            "",
        ]

    if gps_data:
        lines += [
            "GPS DEFORMAZIONE (RITE — real-time NGL):",
            f"  Velocità verticale: {gps_data.get('velocity_up_mm_yr','N/D')} mm/anno",
            f"  Ultimo dato: {gps_data.get('last_date','N/D')}",
            "",
        ]

    if aq_data:
        aq_parts = []
        for param, info in aq_data.items():
            if isinstance(info, dict):
                aq_parts.append(
                    f"{param.upper()}={info.get('value','N/D')} {info.get('unit','μg/m³')}"
                )
        if aq_parts:
            lines += [f"QUALITÀ ARIA (CF area): {', '.join(aq_parts)}", ""]

    if anomaly_cf and anomaly_cf.get("status") == "ok":
        lines += [
            "ANOMALY DETECTION (Isolation Forest):",
            f"  Anomalia rilevata: {'Sì' if anomaly_cf.get('anomaly') else 'No'}",
            f"  {anomaly_cf.get('explanation','')}",
            "",
        ]

    if pattern_cf and pattern_cf.get("pattern"):
        lines += [
            "CLASSIFICAZIONE PATTERN SISMICO (DBSCAN):",
            f"  Tipo: {pattern_cf.get('label','')}",
            f"  {pattern_cf.get('description','')}",
            "",
        ]

    if bvalue_cf and bvalue_cf.get("status") == "ok":
        lines += [
            "GUTENBERG-RICHTER b-value:",
            f"  b = {bvalue_cf.get('b_value','N/D')} (±{bvalue_cf.get('b_sigma','N/D')})",
            f"  {bvalue_cf.get('interpretation','')}",
            "",
        ]

    # Meteo live Open-Meteo
    if weather_ctx:
        lines.append(weather_ctx)

    return "\n".join(lines)


# ── System prompt (language-aware) ───────────────────────────────────────────

_LANG_NAMES = {
    "it": "italiano",
    "en": "English",
    "fr": "français",
    "es": "español",
    "de": "Deutsch",
}

_LANG_TABLE_HEADERS = {
    "it": "| AREA | ALLERTA INGV | DATI RECENTI (7 GG) | ANOMALIE RILEVATE |",
    "en": "| AREA | INGV ALERT | RECENT DATA (7 DAYS) | ANOMALIES DETECTED |",
    "fr": "| ZONE | ALERTE INGV | DONNÉES RÉCENTES (7 J) | ANOMALIES DÉTECTÉES |",
    "es": "| ÁREA | ALERTA INGV | DATOS RECIENTES (7 DÍAS) | ANOMALÍAS DETECTADAS |",
    "de": "| GEBIET | INGV-WARNUNG | AKTUELLE DATEN (7 TAGE) | ERKANNTE ANOMALIEN |",
}

_SYSTEM_PROMPT_TEMPLATE = """Sei un assistente intelligente e versatile per la Campania.
Hai due specializzazioni principali:
  1. Sismologia e vulcanologia (Vesuvio, Campi Flegrei, Ischia) — con dati INGV live
  2. Meteo in tempo reale per la Campania — con dati Open-Meteo live

Rispondi SEMPRE e SOLO in {lang_name}, qualunque sia la lingua dell'utente.

COMPORTAMENTO:
- Rispondi a QUALSIASI domanda posta dall'utente, non solo a quelle sismiche o meteo.
- Se nel contesto hai dati rilevanti (sismici o meteo), usali e citali.
- Se la domanda è su un altro argomento (storia, cultura, trasporti, cucina, ecc.), rispondi
  normalmente usando la tua conoscenza generale.
- Non costringere mai la risposta nel tema sismico/meteo se la domanda non lo richiede.
- Non dire "non dispongo di dati" se la domanda è di cultura generale: in quel caso rispondi
  con la tua conoscenza.

REGOLE PER DATI LIVE:
1. Per domande sismiche: usa i dati INGV/USGS forniti nel contesto — non inventare numeri.
2. Per domande meteo: usa i dati Open-Meteo forniti nel contesto — temperature, pioggia, vento.
3. Distingui tra indice statistico e allerta ufficiale INGV.
4. Non allarmare: l'allerta GIALLO per Campi Flegrei è la condizione normale dal 2023.
5. Risposte concise (max 200 parole) salvo richiesta di dettagli.

FORMATO TABELLA (quando usi tabelle markdown e la domanda è sismica):
{table_header}
"""

def _build_system_prompt(lang: str) -> str:
    lang_name = _LANG_NAMES.get(lang, "italiano")
    table_header = _LANG_TABLE_HEADERS.get(lang, _LANG_TABLE_HEADERS["it"])
    return _SYSTEM_PROMPT_TEMPLATE.format(lang_name=lang_name, table_header=table_header)


# ── UI principale ─────────────────────────────────────────────────────────────

def show_ai_chat(earthquake_data=None, bulletin_cf=None, bulletin_ves=None,
                 alert_level=None, gps_data=None, aq_data=None,
                 anomaly_cf=None, pattern_cf=None, bvalue_cf=None,
                 lang: str = "it"):
    """
    Interfaccia chat AI integrata in Streamlit.
    Usa i dati live passati come argomenti per rispondere in contesto.
    """
    st.subheader("🤖 Assistente AI Sismico")
    st.caption(
        "Chiedi qualsiasi cosa sulla situazione sismica in Campania — "
        "rispondo sui dati live INGV. Powered by AI gratuita, zero API key."
    )

    client, mode = _get_client()

    if not client:
        st.error(
            "⚠️ Impossibile inizializzare il motore AI. "
            "Verifica che il pacchetto `g4f` sia installato (`pip install g4f`)."
        )
        return

    # Badge provider attivo
    if mode == "replit":
        st.caption("🔧 Modalità: proxy Replit (sviluppo)")
    else:
        provider_used = st.session_state.get("_ai_provider_used", "PollinationsAI")
        st.caption(f"🌐 Modalità: {provider_used} — AI gratuita, nessuna API key")

    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # Fetch meteo live per le principali città Campania (cache 30 min ciascuna)
    weather_parts = []
    for city_name, clat, clon in _CAMPANIA_CITIES:
        ctx = _fetch_ai_weather(lat=clat, lon=clon, city=city_name)
        if ctx:
            weather_parts.append(ctx)
    weather_ctx = "\n".join(weather_parts)

    context = _build_context(
        earthquake_data, bulletin_cf, bulletin_ves, alert_level or {},
        gps_data, aq_data, anomaly_cf, pattern_cf, bvalue_cf,
        weather_ctx=weather_ctx,
    )

    # ── Domande suggerite (visibili solo quando chat vuota e nessun chip attivo) ─
    if not st.session_state.ai_messages and "_ai_pending" not in st.session_state:
        suggestions = {
            "it": ["C'è rischio sismico oggi?", "Domani piove a Napoli?",
                   "Cos'è il bradisismo?", "Allerta Campi Flegrei?",
                   "Ultime scosse INGV?"],
            "en": ["Is there seismic risk today?", "Will it rain tomorrow?",
                   "What is bradyseism?", "Campi Flegrei alert level?",
                   "Latest INGV earthquakes?"],
            "fr": ["Y a-t-il un risque sismique?", "Pleuvra-t-il demain?",
                   "Qu'est-ce que le bradyséisme?", "Niveau alerte CF?",
                   "Derniers séismes INGV?"],
            "es": ["¿Hay riesgo sísmico hoy?", "¿Lloverá mañana?",
                   "¿Qué es el bradisismo?", "¿Alerta Campi Flegrei?",
                   "¿Últimos sismos INGV?"],
        }
        sug_list = suggestions.get(lang, suggestions["it"])
        st.markdown("<p style='font-size:13px;color:#666;margin-bottom:6px;'>💡 <b>Prova a chiedere:</b></p>",
                    unsafe_allow_html=True)
        scols = st.columns(len(sug_list))
        for sc, s in zip(scols, sug_list):
            with sc:
                if st.button(s, key=f"sug_{s[:15]}", use_container_width=True):
                    st.session_state["_ai_pending"] = s
                    st.rerun()

    # ── Compressione conversazione (max 16 messaggi → riassunto automatico) ────
    def _compress_history(msgs):
        if len(msgs) <= 16:
            return msgs
        old = msgs[:-8]
        recent = msgs[-8:]
        summary = "RIASSUNTO CONVERSAZIONE PRECEDENTE:\n"
        for m in old:
            role_label = "Utente" if m["role"] == "user" else "AI"
            summary += f"  {role_label}: {m['content'][:120]}…\n"
        return [{"role": "system", "content": summary}] + recent

    # Recupera prompt da chip (click su suggerito) — già aggiunto ad ai_messages
    _chip_prompt: str | None = st.session_state.pop("_ai_pending", None)

    # Mostra storico messaggi (inclusa domanda da chip, se presente)
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Chiedi qualcosa sulla situazione sismica…")
    prompt = _chip_prompt or user_input

    if prompt:
        # Aggiungi alla storia solo se non già presente (chip lo era già)
        if not st.session_state.ai_messages or \
           st.session_state.ai_messages[-1].get("content") != prompt:
            st.session_state.ai_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

        # ── Geocoding dinamico: rileva città nel prompt e aggiunge meteo live ──
        _extra_weather = ""
        _detected = _detect_city_in_text(prompt)
        if _detected:
            _city_name, _clat, _clon = _detected
            # Non ri-fetcha se è già nelle 7 città Campania
            _already = any(c[0].lower() == _city_name.lower() for c in _CAMPANIA_CITIES)
            if not _already:
                _city_wx = _fetch_ai_weather(lat=_clat, lon=_clon, city=_city_name)
                if _city_wx:
                    _extra_weather = f"\n\n[METEO SPECIFICO RICHIESTO]\n{_city_wx}"

        sys_prompt = _build_system_prompt(lang) + "\n\n" + context + _extra_weather
        compressed = _compress_history(st.session_state.ai_messages)
        messages = [{"role": "system", "content": sys_prompt}] + compressed

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("⏳ _Sto consultando i dati INGV e generando la risposta…_")
            full_response = ""
            try:
                full_response = _chat_complete(client, mode, messages)
                placeholder.markdown(full_response)
            except Exception as e:
                full_response = (
                    "⚠️ Tutti i provider AI sono temporaneamente non raggiungibili. "
                    "Ho provato automaticamente più servizi ma tutti hanno risposto con errore. "
                    "**Riprova tra 10–30 secondi** — è un limite temporaneo del servizio gratuito."
                )
                placeholder.markdown(full_response)

        st.session_state.ai_messages.append(
            {"role": "assistant", "content": full_response}
        )

    if st.session_state.ai_messages:
        st.markdown("""
        <style>
        div[data-testid="stButton"] button[kind="secondary"]#clear_ai_chat_btn,
        div[data-testid="stButton"]:has(button) button {
            background: transparent !important;
        }
        .clear-btn-wrap button { background:#e9ecef!important;color:#495057!important;
            border:1px solid #ced4da!important;font-size:0.85rem!important; }
        </style>
        """, unsafe_allow_html=True)
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("🗑️ Cancella conversazione", key="clear_ai_chat",
                         type="secondary", use_container_width=True):
                st.session_state.ai_messages = []
                st.rerun()
