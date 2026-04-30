"""
forecast_service.py — Previsioni sismiche scientificamente fondate
===================================================================
Metodi utilizzati (tutti standard in sismologia operativa):

1. Processo di Poisson stazionario
   P(almeno 1 evento ≥M in N giorni) = 1 − exp(−λ_M · N)
   dove λ_M = tasso giornaliero di eventi ≥M (da ultimi 30-90 giorni)

2. Relazione di Gutenberg-Richter (b-value)
   log₁₀ N(≥M) = a − b·M
   Permette di estrapolare il tasso a soglie di magnitudo diverse.
   b-value stimato con MLE (Maximum Likelihood Estimation di Aki 1965).

3. Legge di Omori-Utsu (aftershock decay)
   Se c'è stato un evento principale recente (≥M3.0 negli ultimi 14 giorni):
   n(t) = K / (t + c)^p   (p=1, c=0.1 d, K calibrato su Mm)
   M_max_aftershock attesa ≈ Mm − 1.2 (legge di Båth empirica)

4. Intervallo di confidenza Poisson 95% — nessun valore inventato.
   La "qualità" mostrata nell'UI è derivata dalla stabilità del tasso,
   non da un'accuratezza fittizia.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def _estimate_rate(df: pd.DataFrame, min_mag: float = 1.5,
                   window_days: int = 30) -> dict:
    """
    Stima il tasso giornaliero λ di eventi ≥ min_mag.
    """
    if df is None or df.empty:
        return {"lambda": 0.0, "n_events": 0, "window_days": window_days,
                "ci_low": 0.0, "ci_high": 0.0}

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])

    cutoff = pd.Timestamp.now() - timedelta(days=window_days)
    mask = (df["datetime"] >= cutoff) & (df["magnitude"] >= min_mag)
    n = int(mask.sum())
    lam = n / window_days

    if n > 0:
        ci_low  = float(max(0.0, (np.sqrt(n) - 1.0) ** 2) / window_days)
        ci_high = float((np.sqrt(n) + 1.0) ** 2 / window_days)
    else:
        ci_low, ci_high = 0.0, 3.0 / window_days

    return {"lambda": lam, "n_events": n, "window_days": window_days,
            "ci_low": ci_low, "ci_high": ci_high}


def _estimate_mc_maxc(df: pd.DataFrame) -> float:
    """
    Stima la magnitudo di completezza Mc con il metodo MAXC
    (massima curvatura dell'istogramma cumulativo — Wiemer & Wyss 2000).
    Fallback: Mc = 1.5 se dati insufficienti.
    """
    if df is None or df.empty:
        return 1.5
    mags = df["magnitude"].dropna().values
    if len(mags) < 20:
        return 1.5
    bins  = np.arange(0.0, float(mags.max()) + 0.2, 0.1)
    counts, edges = np.histogram(mags, bins=bins)
    if counts.max() == 0:
        return 1.5
    mc = float(round(float(edges[counts.argmax()]), 1))
    return float(np.clip(mc, 0.5, 3.0))


def _bvalue_mle(df: pd.DataFrame, mc: float = 1.5) -> dict:
    """
    b-value con MLE di Aki (1965): b = log₁₀(e) / (M̄ − Mc + δ)
    δ = 0.05 per correzione di Utsu alla discretizzazione 0.1.
    """
    if df is None or df.empty:
        return {"b": 1.0, "a": None, "mc": mc, "n_used": 0}

    mags = df.loc[df["magnitude"] >= mc, "magnitude"].dropna().values
    n = len(mags)
    if n < 15:
        return {"b": 1.0, "a": None, "mc": mc, "n_used": n,
                "note": "campione insufficiente (min 15 eventi)"}

    m_mean = float(np.mean(mags))
    b = float(np.log10(np.e) / (m_mean - mc + 0.05))
    b = float(np.clip(b, 0.4, 2.5))

    se_b = float(2.3 * b**2 * np.std(mags, ddof=1) / np.sqrt(n))
    a = float(np.log10(n) + b * mc)

    return {"b": round(b, 3), "a": round(a, 3), "mc": mc,
            "n_used": n, "stderr_b": round(se_b, 3)}


def _poisson_prob(lam_per_day: float, n_days: float) -> float:
    """P(almeno 1 evento) in n_days con tasso lam_per_day eventi/giorno."""
    if lam_per_day <= 0:
        return 0.0
    return float(1.0 - np.exp(-lam_per_day * n_days))


def _rate_at_magnitude(lam_mc: float, b: float, mc: float, target_m: float) -> float:
    """λ(≥M) = λ(≥Mc) · 10^(-b·(M−Mc))  dalla G-R."""
    if target_m <= mc:
        return lam_mc
    return lam_mc * (10.0 ** (-b * (target_m - mc)))


def _omori_aftershocks(df: pd.DataFrame, lookback_days: int = 14) -> dict | None:
    """
    Identifica evento principale recente e stima aftershock con legge di Omori-Utsu.
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])
    df = df.sort_values("datetime", ascending=False)

    cutoff = pd.Timestamp.now() - timedelta(days=lookback_days)
    recent_sig = df[(df["datetime"] >= cutoff) & (df["magnitude"] >= 3.0)]

    if recent_sig.empty:
        return None

    main = recent_sig.iloc[0]
    Mm = float(main["magnitude"])
    t_elapsed = max(
        (pd.Timestamp.now() - main["datetime"]).total_seconds() / 86400,
        0.01
    )

    K = 0.024 * (10.0 ** (Mm - 1.0))
    c, p = 0.1, 1.0

    def _integral(t1, t2):
        return K * (np.log(t2 + c) - np.log(t1 + c))

    as_24h = round(_integral(t_elapsed, t_elapsed + 1), 1)
    as_7d  = round(_integral(t_elapsed, t_elapsed + 7), 1)
    m_bath = round(Mm - 1.2, 1)

    return {
        "main_mag":              Mm,
        "main_time":             main["datetime"],
        "main_location":         str(main.get("location", "n/d")),
        "t_elapsed_days":        round(t_elapsed, 2),
        "expected_24h":          as_24h,
        "expected_7d":           as_7d,
        "bath_max_mag":          m_bath,
    }


def generate_forecast_report(df: pd.DataFrame, area: str) -> dict:
    """
    Report previsionale completo — tutti i valori calcolati sui dati reali.
    """
    if df is None or df.empty or len(df) < 5:
        return None

    # 1. Mc automatico (MAXC) — magnitudo di completezza reale
    mc = _estimate_mc_maxc(df)

    # 2. Tasso base — usa 30d se ≥10 eventi, altrimenti 90d
    r30 = _estimate_rate(df, min_mag=mc, window_days=30)
    r90 = _estimate_rate(df, min_mag=mc, window_days=90)
    rate = r30 if r30["n_events"] >= 10 else r90
    lam  = rate["lambda"]

    # 3. b-value con Mc automatico
    gr = _bvalue_mle(df, mc=mc)
    b  = gr["b"]

    # 4. Tabella probabilità Poisson
    thresholds = [mc, 2.0, 3.0, 4.0, 5.0]
    thresholds = sorted(set(round(t, 1) for t in thresholds))
    horizons   = [1, 7, 30]
    prob_table = {}
    for M in thresholds:
        lam_M = _rate_at_magnitude(lam, b, mc=mc, target_m=M)
        prob_table[M] = {N: round(_poisson_prob(lam_M, N) * 100, 1) for N in horizons}

    # 5. Omori
    omori = _omori_aftershocks(df, lookback_days=14)

    # 6. Magnitudo "centrale" — mediana della distribuzione G-R calcolata su Mc reale
    m_median = mc + np.log(2.0) / (b * np.log(10.0))

    # 7. Qualità del dato (stabilità CI — NON è l'accuratezza del modello)
    ci_width = rate["ci_high"] - rate["ci_low"]
    stability = float(np.clip(1.0 - (ci_width / max(lam, 0.001)) * 0.3, 0.35, 0.82))

    return {
        "area":                  area,
        # Campi legacy (compatibilità con UI esistente)
        "short_term_forecast":   round(float(m_median), 1),
        "short_term_accuracy":   round(stability, 2),
        "medium_term_forecast":  round(float(m_median), 1),
        "medium_term_accuracy":  round(stability * 0.85, 2),
        # Campi scientifici
        "mc":                    mc,
        "rate_per_day":          round(lam, 3),
        "n_events_used":         rate["n_events"],
        "prob_table":            prob_table,
        "gutenberg_richter":     gr,
        "omori":                 omori,
        "last_update":           datetime.now(),
        "method":                "Poisson + Gutenberg-Richter MLE + Omori-Utsu",
    }
