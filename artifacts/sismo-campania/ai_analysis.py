"""
ai_analysis.py — Moduli AI/ML per SeismicSafetyItalia
=====================================================
1. Anomaly Detection (Isolation Forest) — segnala sciami anomali
2. Seismic Swarm Classifier (DBSCAN) — tipo evento: isolato/sciame/sequenza
3. Gutenberg-Richter b-value — stress tettonico
4. GPS-Seismicity correlation — indicatore composito CF
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


# ─────────────────────────────────────────────────────────────
# 1. ANOMALY DETECTION — Isolation Forest
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def detect_anomalies(df: pd.DataFrame, area: str = "") -> dict:
    """
    Rileva anomalie nella sismicità usando Isolation Forest.
    Confronta la finestra recente (3 giorni) con la baseline (30 giorni).
    Restituisce: livello anomalia, score, spiegazione.
    """
    if df is None or df.empty or len(df) < 10:
        return {"status": "insufficient_data", "anomaly": False, "score": 0.0, "explanation": "Dati insufficienti"}

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])
        df = df.sort_values("datetime")

        now = pd.Timestamp.now(tz="UTC").replace(tzinfo=None)
        cutoff_3d  = now - timedelta(days=3)
        cutoff_30d = now - timedelta(days=30)

        baseline = df[df["datetime"] >= cutoff_30d].copy()
        recent   = df[df["datetime"] >= cutoff_3d].copy()

        if len(baseline) < 8:
            return {"status": "insufficient_data", "anomaly": False, "score": 0.0,
                    "explanation": "Storico insufficiente per rilevare anomalie"}

        def _daily_features(data):
            data = data.copy()
            data["date"] = data["datetime"].dt.date
            grp = data.groupby("date").agg(
                count=("magnitude", "count"),
                max_mag=("magnitude", "max"),
                mean_mag=("magnitude", "mean"),
                mean_depth=("depth", "mean"),
            ).reset_index()
            return grp

        base_daily = _daily_features(baseline)
        if len(base_daily) < 5:
            return {"status": "insufficient_data", "anomaly": False, "score": 0.0,
                    "explanation": "Storico giornaliero insufficiente"}

        feats = ["count", "max_mag", "mean_mag", "mean_depth"]
        X = base_daily[feats].fillna(0).values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        iso = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        iso.fit(X_scaled)

        rec_daily = _daily_features(recent) if len(recent) >= 1 else pd.DataFrame()

        if rec_daily.empty:
            return {"status": "ok", "anomaly": False, "score": 0.0,
                    "explanation": "Nessun evento recente nel periodo analizzato"}

        X_rec = rec_daily[feats].fillna(0).values
        X_rec_scaled = scaler.transform(X_rec)
        scores = iso.score_samples(X_rec_scaled)
        preds  = iso.predict(X_rec_scaled)

        is_anomaly = (preds == -1).any()
        avg_score  = float(np.mean(scores))
        severity   = min(max((-avg_score - 0.1) / 0.4, 0), 1.0) if is_anomaly else 0.0

        recent_rate = len(recent) / 3 if len(recent) > 0 else 0
        base_rate   = len(baseline) / 30 if len(baseline) > 0 else 0
        rate_ratio  = recent_rate / (base_rate + 0.001)

        if not is_anomaly:
            explanation = f"Attività nella norma — {len(recent)} eventi negli ultimi 3 giorni (media: {base_rate:.1f}/giorno)"
        elif severity < 0.4:
            explanation = f"Lieve anomalia — tasso recente {rate_ratio:.1f}x rispetto alla media storica"
        elif severity < 0.7:
            explanation = f"Anomalia moderata — {len(recent)} eventi in 3 giorni vs media {base_rate*3:.0f}"
        else:
            explanation = f"⚠️ Anomalia significativa — {len(recent)} eventi in 3 giorni, tasso {rate_ratio:.1f}x la media"

        return {
            "status": "ok",
            "anomaly": bool(is_anomaly),
            "severity": float(severity),
            "score": float(avg_score),
            "rate_ratio": float(rate_ratio),
            "recent_count": len(recent),
            "baseline_daily_avg": float(base_rate),
            "explanation": explanation,
            "area": area,
        }

    except Exception as e:
        return {"status": "error", "anomaly": False, "score": 0.0,
                "explanation": f"Errore analisi: {e}"}


# ─────────────────────────────────────────────────────────────
# 2. SEISMIC SWARM CLASSIFIER — DBSCAN spaziotemporale
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def classify_seismic_pattern(df: pd.DataFrame, area: str = "") -> dict:
    """
    Classifica il pattern sismico corrente:
    - 'isolato'   → evento singolo o pochi eventi sparsi
    - 'sciame'    → tanti eventi piccoli ravvicinati (tipico bradisismo CF)
    - 'sequenza'  → evento principale + aftershock (legge di Omori)
    - 'silenzio'  → nessuna attività significativa
    """
    if df is None or df.empty or len(df) < 3:
        return {"pattern": "silenzio", "label": "Silenzio sismico", "description": "Nessuna attività significativa",
                "confidence": 1.0, "n_clusters": 0}

    try:
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler

        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])

        # Usa solo ultimi 7 giorni
        cutoff = pd.Timestamp.now(tz="UTC").replace(tzinfo=None) - timedelta(days=7)
        recent = df[df["datetime"] >= cutoff].copy()
        if len(recent) < 3:
            return {"pattern": "silenzio", "label": "Attività minima", "description": f"Solo {len(recent)} eventi negli ultimi 7 giorni",
                    "confidence": 0.9, "n_clusters": 0}

        # Feature spaziotemporale: lat, lon, tempo (ore), magnitudo
        recent["hours"] = (recent["datetime"] - recent["datetime"].min()).dt.total_seconds() / 3600
        features = recent[["latitude", "longitude", "hours", "magnitude"]].fillna(0).values
        scaler = StandardScaler()
        X = scaler.fit_transform(features)

        # DBSCAN: eps adattato all'area
        eps = 0.3 if "flegrei" in area.lower() else 0.4
        db = DBSCAN(eps=eps, min_samples=3)
        labels = db.fit_predict(X)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise    = (labels == -1).sum()
        n_total    = len(recent)

        max_mag  = recent["magnitude"].max()
        mean_mag = recent["magnitude"].mean()
        std_mag  = recent["magnitude"].std()

        # Logica classificazione
        if n_total < 5:
            pattern = "isolato"
            label   = "Evento isolato"
            desc    = f"{n_total} eventi sparsi, magnitudo max {max_mag:.1f}"
        elif n_clusters >= 2 and std_mag < 0.5 and mean_mag < 2.5:
            pattern = "sciame"
            label   = "Sciame sismico"
            desc    = f"{n_total} eventi in {n_clusters} cluster, tipico del bradisismo — magnitudo media {mean_mag:.1f}"
        elif max_mag >= 3.0 and n_total > 5:
            # Verifica legge Omori: picco all'inizio poi decadimento
            hourly = recent.groupby(recent["hours"].astype(int)).size()
            if len(hourly) > 2 and hourly.iloc[0] == hourly.max():
                pattern = "sequenza"
                label   = "Sequenza sismica"
                desc    = f"Evento principale M{max_mag:.1f} + {n_total-1} aftershock"
            else:
                pattern = "sciame"
                label   = "Sciame sismico"
                desc    = f"{n_total} eventi, magnitudo max {max_mag:.1f}"
        elif n_noise > n_total * 0.6:
            pattern = "isolato"
            label   = "Eventi sparsi"
            desc    = f"{n_total} eventi non raggruppati, attività distribuita"
        else:
            pattern = "sciame"
            label   = "Sciame sismico"
            desc    = f"{n_total} eventi in {n_clusters} cluster"

        confidence = min(0.95, 0.6 + n_total / 50)

        return {
            "pattern": pattern,
            "label": label,
            "description": desc,
            "confidence": float(confidence),
            "n_clusters": int(n_clusters),
            "n_events": int(n_total),
            "max_mag": float(max_mag),
            "mean_mag": float(mean_mag),
            "area": area,
        }

    except Exception as e:
        return {"pattern": "sconosciuto", "label": "Analisi non disponibile",
                "description": str(e), "confidence": 0.0, "n_clusters": 0}


# ─────────────────────────────────────────────────────────────
# 3. GUTENBERG-RICHTER b-VALUE
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def compute_gutenberg_richter(df: pd.DataFrame, area: str = "") -> dict:
    """
    Calcola il parametro b della relazione Gutenberg-Richter:
      log10(N) = a - b*M
    b tipico = 0.8–1.2 per sismicità normale.
    b basso (<0.7) può indicare accumulo di stress.
    b alto (>1.5) può indicare frammentazione/fluidi.
    """
    if df is None or df.empty or len(df) < 20:
        return {"b_value": None, "a_value": None, "r_squared": None,
                "interpretation": "Dati insufficienti (minimo 20 eventi)", "status": "insufficient"}

    try:
        mags = df["magnitude"].dropna().values
        mags = mags[mags >= 1.0]  # soglia minima completezza

        if len(mags) < 15:
            return {"b_value": None, "interpretation": "Troppi pochi eventi ≥ M1.0", "status": "insufficient"}

        # Magnitudo di completezza (metodo massima curvatura)
        mag_bins = np.arange(0.5, mags.max() + 0.5, 0.5)
        counts, edges = np.histogram(mags, bins=mag_bins)
        mc_idx = np.argmax(counts)
        mc = float(edges[mc_idx])

        mags_above = mags[mags >= mc]
        if len(mags_above) < 10:
            mc = float(np.percentile(mags, 20))
            mags_above = mags[mags >= mc]

        if len(mags_above) < 8:
            return {"b_value": None, "interpretation": "Campione insufficiente sopra Mc", "status": "insufficient"}

        # Stima b con massima verosimiglianza (Aki 1965)
        b_mle = np.log10(np.e) / (np.mean(mags_above) - mc + 0.05)
        sigma_b = b_mle / np.sqrt(len(mags_above))

        # R² per valutare qualità del fit
        unique_mags = np.sort(np.unique(np.round(mags_above, 1)))
        cum_counts = np.array([np.sum(mags_above >= m) for m in unique_mags])
        if len(unique_mags) > 2 and cum_counts.max() > 0:
            log_cum = np.log10(cum_counts + 1)
            p = np.polyfit(unique_mags, log_cum, 1)
            fitted = np.polyval(p, unique_mags)
            ss_res = np.sum((log_cum - fitted) ** 2)
            ss_tot = np.sum((log_cum - np.mean(log_cum)) ** 2)
            r2 = max(0.0, 1 - ss_res / (ss_tot + 1e-10))
        else:
            r2 = 0.0

        # Interpretazione
        if b_mle < 0.6:
            interp = f"⚠️ b={b_mle:.2f} basso — possibile accumulo di stress tettonico"
            level = "warning"
        elif b_mle < 0.8:
            interp = f"🔶 b={b_mle:.2f} sotto la norma — monitoraggio consigliato"
            level = "caution"
        elif b_mle <= 1.3:
            interp = f"✅ b={b_mle:.2f} — nella norma per sismicità vulcanica/tettonica"
            level = "normal"
        elif b_mle <= 1.8:
            interp = f"🔵 b={b_mle:.2f} alto — tipico di sismicità indotta da fluidi (bradisismo)"
            level = "high_fluid"
        else:
            interp = f"🔵 b={b_mle:.2f} molto alto — frammentazione intensa o sismicità superficiale"
            level = "very_high"

        return {
            "b_value": float(round(b_mle, 3)),
            "b_sigma": float(round(sigma_b, 3)),
            "mc": float(round(mc, 2)),
            "n_events": int(len(mags_above)),
            "r_squared": float(round(r2, 3)),
            "interpretation": interp,
            "level": level,
            "status": "ok",
            "area": area,
        }

    except Exception as e:
        return {"b_value": None, "interpretation": f"Errore calcolo: {e}", "status": "error"}


# ─────────────────────────────────────────────────────────────
# 4. GPS + SEISMICITY CORRELATION (Campi Flegrei)
# ─────────────────────────────────────────────────────────────

def compute_gps_seismicity_correlation(df: pd.DataFrame, gps_data: dict | None) -> dict:
    """
    Correlazione tra tasso sismico e velocità di sollevamento GPS.
    Un aumento simultaneo di entrambi è il segnale tipico di crisi bradisismica.
    """
    if df is None or df.empty:
        return {"status": "no_seismic", "alert": False, "message": "Nessun dato sismico"}

    if not gps_data:
        return {"status": "no_gps", "alert": False,
                "message": "Dati GPS non disponibili — solo sismicità monitorata"}

    try:
        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        now = pd.Timestamp.now(tz="UTC").replace(tzinfo=None)

        rate_7d  = len(df[df["datetime"] >= now - timedelta(days=7)])
        rate_30d = len(df[df["datetime"] >= now - timedelta(days=30)]) / 4

        uplift_rate = gps_data.get("velocity_up_mm_yr", 0) / 12  # mm/mese

        # Indicatore composito: sismicità + GPS entrambi elevati
        seismic_high = rate_7d > rate_30d * 1.3
        gps_high = uplift_rate > 8  # mm/mese

        if seismic_high and gps_high:
            alert = True
            msg = (f"⚠️ Segnale composito elevato: {rate_7d} eventi/settimana "
                   f"(+{(rate_7d/max(rate_30d,1)-1)*100:.0f}% vs media) "
                   f"+ sollevamento GPS {uplift_rate:.1f} mm/mese")
            level = "elevated"
        elif seismic_high:
            alert = False
            msg = (f"Sismicità in aumento ({rate_7d} eventi/settimana) "
                   f"ma GPS nella norma ({uplift_rate:.1f} mm/mese)")
            level = "seismic_only"
        elif gps_high:
            alert = False
            msg = (f"Sollevamento GPS accelerato ({uplift_rate:.1f} mm/mese) "
                   f"ma sismicità nella norma ({rate_7d} eventi/settimana)")
            level = "gps_only"
        else:
            alert = False
            msg = (f"Parametri nella norma: {rate_7d} eventi/settimana, "
                   f"sollevamento GPS {uplift_rate:.1f} mm/mese")
            level = "normal"

        return {
            "status": "ok",
            "alert": alert,
            "level": level,
            "message": msg,
            "seismic_rate_7d": rate_7d,
            "seismic_rate_30d_avg": rate_30d,
            "gps_uplift_mm_month": uplift_rate,
        }

    except Exception as e:
        return {"status": "error", "alert": False, "message": f"Errore correlazione: {e}"}
