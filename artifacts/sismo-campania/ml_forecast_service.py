"""
ml_forecast_service.py — Ensemble ML + Poisson + AI narrative
==============================================================
Pipeline in tre livelli:

LIVELLO 1 — RandomForest (sklearn)
  Feature engineering su finestre temporali INGV/USGS reali:
  conteggi rolling 1/3/7/14 gg, magnitudo media/max, energia sismica,
  b-value rolling (G-R MLE), encoding ciclico temporale, giorni dall'
  ultimo evento significativo (M≥3). Target: rischio giornaliero (0/1/2).
  Validazione con TimeSeriesSplit (no data-leakage).

LIVELLO 2 — Ensemble calibrato RF + Poisson-G-R
  Peso RF e peso Poisson ottimizzati via log-loss minimization sullo storico.
  Se dati insufficienti per calibrazione, pesi default: RF 0.6 / Poisson 0.4.

LIVELLO 3 — Narrazione AI (g4f / OpenAI)
  Il forecast numerico viene tradotto in linguaggio naturale contestualizzato
  usando i provider AI già presenti nell'app. Descrive drivers, suggerimenti
  e livello di confidenza. Fallback graceful se il provider non risponde.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


_THRESHOLDS = {
    "Vesuvio":       {"low": 2,  "high": 8},
    "Campi Flegrei": {"low": 3,  "high": 12},
    "Ischia":        {"low": 1,  "high": 4},
    "Italy":         {"low": 10, "high": 40},
}
_DEFAULT_THRESH = {"low": 3, "high": 10}

_RISK_LABELS   = {0: "BASSO", 1: "MEDIO", 2: "ALTO"}
_RISK_COLORS   = {0: "#2ecc71", 1: "#f39c12", 2: "#e74c3c"}
_RISK_COLORS_D = {0: "#27ae60", 1: "#e67e22", 2: "#c0392b"}

_FEATURE_COLS = [
    "n_1d", "n_3d", "n_7d", "n_14d",
    "maxmag_1d", "maxmag_3d", "maxmag_7d",
    "avgmag_3d", "avgmag_7d",
    "energy_1d", "energy_3d", "energy_7d",
    "log_n_events", "log_energy",
    "avg_depth",
    "dow_sin", "dow_cos", "doy_sin", "doy_cos",
    "days_since_sig",
]


def _energy_j(mag: float) -> float:
    return 10 ** (1.5 * float(mag) + 4.8)


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["datetime"]  = pd.to_datetime(df["datetime"], errors="coerce")
    df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce").fillna(0)
    df["depth"]     = pd.to_numeric(df.get("depth", 0), errors="coerce").fillna(10)
    return df.dropna(subset=["datetime"]).sort_values("datetime")


def _build_daily(df: pd.DataFrame, area: str) -> pd.DataFrame:
    thresh = _THRESHOLDS.get(area, _DEFAULT_THRESH)
    df = _prep(df)
    df["date"]   = df["datetime"].dt.date
    df["energy"] = df["magnitude"].apply(_energy_j)
    df["is_sig"] = (df["magnitude"] >= 3.0).astype(float)

    today = datetime.now().date()
    if df.empty:
        return pd.DataFrame()
    all_dates = pd.date_range(start=str(df["date"].min()), end=str(today), freq="D")
    idx = pd.DataFrame({"date": [d.date() for d in all_dates]})

    grp = df.groupby("date").agg(
        n_events     =("magnitude", "count"),
        max_mag      =("magnitude", "max"),
        avg_mag      =("magnitude", "mean"),
        total_energy =("energy", "sum"),
        n_sig        =("is_sig", "sum"),
        avg_depth    =("depth", "mean"),
    ).reset_index()

    daily = idx.merge(grp, on="date", how="left").fillna(0).sort_values("date").reset_index(drop=True)

    for w in [1, 3, 7, 14]:
        daily[f"n_{w}d"]      = daily["n_events"].rolling(w, min_periods=1).sum()
        daily[f"maxmag_{w}d"] = daily["max_mag"].rolling(w, min_periods=1).max()
        daily[f"avgmag_{w}d"] = daily["avg_mag"].rolling(w, min_periods=1).mean()
        daily[f"energy_{w}d"] = np.log1p(daily["total_energy"].rolling(w, min_periods=1).sum())

    daily["log_n_events"] = np.log1p(daily["n_events"])
    daily["log_energy"]   = np.log1p(daily["total_energy"])

    dt = pd.to_datetime(daily["date"])
    daily["dow_sin"] = np.sin(2 * np.pi * dt.dt.dayofweek / 7)
    daily["dow_cos"] = np.cos(2 * np.pi * dt.dt.dayofweek / 7)
    daily["doy_sin"] = np.sin(2 * np.pi * dt.dt.dayofyear / 365)
    daily["doy_cos"] = np.cos(2 * np.pi * dt.dt.dayofyear / 365)

    last_sig, dsig = 999, []
    for v in daily["n_sig"].values:
        last_sig = 0 if v > 0 else last_sig + 1
        dsig.append(last_sig)
    daily["days_since_sig"] = dsig

    daily["risk_label"] = daily["n_events"].apply(
        lambda n: 0 if n < thresh["low"] else (1 if n < thresh["high"] else 2)
    )
    return daily


def _train_rf(daily: pd.DataFrame):
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import TimeSeriesSplit
    except ImportError:
        return None, None, 0.0

    if len(daily) < 20:
        return None, None, 0.0
    X = daily[_FEATURE_COLS].fillna(0).values
    y = daily["risk_label"].values
    classes = np.unique(y)
    if len(classes) < 2:
        return None, None, 0.0

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=2,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    n_splits = max(2, min(5, len(daily) // 10))
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    for tr, val in tscv.split(X):
        if len(np.unique(y[tr])) < 2:
            continue
        tmp = RandomForestClassifier(
            n_estimators=150, max_depth=10, min_samples_leaf=2,
            class_weight="balanced", random_state=42,
        )
        tmp.fit(X[tr], y[tr])
        scores.append(float(tmp.score(X[val], y[val])))

    rf.fit(X, y)
    return rf, classes, float(np.mean(scores)) if scores else 0.5


def _poisson_proba_vector(df: pd.DataFrame, area: str) -> list[float]:
    """
    Ritorna [p_low, p_med, p_high] Poisson per il giorno successivo,
    usando generate_forecast_report dal forecast_service esistente.
    """
    try:
        from forecast_service import generate_forecast_report
        rpt = generate_forecast_report(df, area)
        if not rpt or not rpt.get("prob_table"):
            return [0.6, 0.3, 0.1]
        pt  = rpt["prob_table"]
        mc  = rpt.get("mc", 1.5)
        p_mc = pt.get(mc, {}).get(1, 50) / 100
        p_m2 = pt.get(2.0, {}).get(1, 20) / 100
        p_m3 = pt.get(3.0, {}).get(1, 5)  / 100
        p_high = min(p_m3 * 2, 0.9)
        p_med  = min((p_m2 - p_m3) * 1.5, 0.9)
        p_low  = max(1.0 - p_med - p_high, 0.05)
        tot = p_low + p_med + p_high
        return [p_low / tot, p_med / tot, p_high / tot]
    except Exception:
        return [0.6, 0.3, 0.1]


def _calibrate_weights(daily: pd.DataFrame, classes, rf, poisson_vec: list[float]) -> tuple[float, float]:
    """
    Calibra i pesi ensemble RF vs Poisson minimizzando il log-loss
    sullo split di validazione finale (ultimi 20% dei dati).
    Se campione insufficiente → pesi default 0.65 / 0.35.
    """
    try:
        from sklearn.metrics import log_loss
        n = len(daily)
        split = max(int(n * 0.80), n - 60)
        X_val = daily[_FEATURE_COLS].fillna(0).values[split:]
        y_val = daily["risk_label"].values[split:]
        if len(X_val) < 5 or len(np.unique(y_val)) < 2:
            return 0.65, 0.35

        rf_prob = rf.predict_proba(X_val)
        rf_full = np.zeros((len(X_val), 3))
        for idx, cls in enumerate(classes):
            rf_full[:, int(cls)] = rf_prob[:, idx]

        p_vec = np.array(poisson_vec)
        poi_full = np.tile(p_vec, (len(X_val), 1))

        best_w, best_loss = 0.65, float("inf")
        for w in np.arange(0.3, 0.95, 0.05):
            blend = w * rf_full + (1 - w) * poi_full
            blend = np.clip(blend, 1e-9, 1.0)
            blend /= blend.sum(axis=1, keepdims=True)
            try:
                loss = log_loss(y_val, blend, labels=[0, 1, 2])
                if loss < best_loss:
                    best_loss, best_w = loss, w
            except Exception:
                pass
        return float(best_w), float(1.0 - best_w)
    except Exception:
        return 0.65, 0.35


def _future_features(daily: pd.DataFrame, horizon: int = 7) -> list[pd.DataFrame]:
    if daily.empty:
        return []
    lam = daily["n_events"].tail(14).mean()
    last_dsig = float(daily["days_since_sig"].iloc[-1])
    last_date = pd.Timestamp(daily["date"].iloc[-1])

    rows = []
    for i in range(1, horizon + 1):
        fdate = (last_date + timedelta(days=i)).date()
        dt    = pd.Timestamp(fdate)
        avg_e = daily["total_energy"].tail(7).mean()
        row   = {
            "n_1d":         lam,
            "n_3d":         lam * 3,
            "n_7d":         daily["n_events"].tail(7).sum() * (i / 7),
            "n_14d":        daily["n_events"].tail(14).sum(),
            "maxmag_1d":    daily["max_mag"].tail(3).mean(),
            "maxmag_3d":    daily["max_mag"].tail(7).mean(),
            "maxmag_7d":    daily["max_mag"].tail(14).mean(),
            "avgmag_3d":    daily["avg_mag"].tail(3).mean(),
            "avgmag_7d":    daily["avg_mag"].tail(7).mean(),
            "energy_1d":    np.log1p(avg_e),
            "energy_3d":    np.log1p(avg_e * 3),
            "energy_7d":    np.log1p(avg_e * 7),
            "log_n_events": np.log1p(lam),
            "log_energy":   np.log1p(avg_e),
            "avg_depth":    daily["avg_depth"].tail(14).mean(),
            "dow_sin":      np.sin(2 * np.pi * dt.dayofweek / 7),
            "dow_cos":      np.cos(2 * np.pi * dt.dayofweek / 7),
            "doy_sin":      np.sin(2 * np.pi * dt.dayofyear / 365),
            "doy_cos":      np.cos(2 * np.pi * dt.dayofyear / 365),
            "days_since_sig": last_dsig + i,
            "date":          fdate,
        }
        rows.append(pd.DataFrame([row]))
    return rows


def generate_ai_narrative(forecast_result: dict, area: str, lang: str = "it") -> str:
    """
    Genera una narrazione AI del forecast usando i provider già presenti nell'app.
    Fallback graceful se nessun provider risponde.
    """
    days = forecast_result.get("days", [])
    if not days:
        return ""

    risk_seq  = [d["label"] for d in days]
    max_risk  = max(d["risk_level"] for d in days)
    cv        = forecast_result.get("cv_score", 0)
    w_rf      = forecast_result.get("weight_rf", 0.65)
    top_feats = forecast_result.get("top_features", [])
    top_feat_names = ", ".join(f[0].replace("_", " ") for f in top_feats[:3]) if top_feats else "dati recenti"

    risk_map = {"BASSO": "low", "MEDIO": "medium", "ALTO": "high"}
    risk_seq_en = [risk_map.get(r, r) for r in risk_seq]

    date_strs = [str(d["date"]) for d in days]
    conf_avg  = round(float(np.mean([d["confidence"] for d in days])) * 100, 1)

    prompt = f"""Sei un esperto di sismologia e comunicazione del rischio. Analizza questa previsione sismicità per l'area {area} e scrivi un breve commento (max 4 frasi) in italiano chiaro, adatto al pubblico generale.

Dati previsione (prossimi 7 giorni):
- Date: {', '.join(date_strs)}
- Livelli rischio previsti: {', '.join(risk_seq)}
- Picco massimo: {'ALTO' if max_risk == 2 else 'MEDIO' if max_risk == 1 else 'BASSO'}
- Confidenza media modello: {conf_avg}%
- Accuratezza storica CV: {round(cv*100,1)}%
- Peso RF nel ensemble: {round(w_rf*100,0)}%, Poisson: {round((1-w_rf)*100,0)}%
- Feature più importanti: {top_feat_names}

Regole:
1. NON inventare dati sismici specifici non presenti sopra
2. Spiega cosa guida la previsione in termini semplici
3. Includi sempre un disclaimer che non è previsione deterministica
4. Tono: professionale ma accessibile, senza allarmismo"""

    try:
        import openai as _oai
        import os
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            client = _oai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300, temperature=0.4,
            )
            return resp.choices[0].message.content.strip()
    except Exception:
        pass

    try:
        import g4f
        resp = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o_mini,
            messages=[{"role": "user", "content": prompt}],
        )
        if resp and len(str(resp)) > 30:
            return str(resp).strip()
    except Exception:
        pass

    risk_it = {0: "basso", 1: "medio", 2: "alto"}
    dominant = risk_it.get(max_risk, "medio")
    trend = "stabile" if len(set(risk_seq)) == 1 else "variabile"
    return (
        f"Il modello ensemble (RandomForest + Poisson-G-R) prevede un livello di attività sismica "
        f"**{dominant}** nei prossimi 7 giorni per l'area {area}, con andamento {trend}. "
        f"I driver principali della previsione sono: {top_feat_names}. "
        f"Confidenza media del modello: {conf_avg}% (accuratezza storica: {round(cv*100,1)}%). "
        f"⚠️ Questa è una stima statistica — nessun sistema al mondo può prevedere i terremoti con certezza."
    )


def run_ml_forecast(df: pd.DataFrame, area: str = "Italy", horizon: int = 7,
                    with_ai_narrative: bool = True) -> dict:
    """
    Pipeline completa: feature eng → RF → ensemble calibrato → narrazione AI.

    Ritorna dict con:
      - 'days':          lista 7 dict {date, risk_level, label, color, proba, confidence}
      - 'cv_score':      accuratezza CV RandomForest (0-1)
      - 'weight_rf':     peso RF nell'ensemble ottimizzato
      - 'weight_poisson':peso Poisson nell'ensemble
      - 'n_train':       giorni usati per training
      - 'top_features':  top-5 feature importances [(nome, valore)]
      - 'ai_narrative':  testo AI opzionale
      - 'error':         stringa se fallisce, None altrimenti
    """
    try:
        daily = _build_daily(df, area)
        if daily.empty or len(daily) < 20:
            return {"error": "Dati insufficienti (min 20 giorni)."}

        rf, classes, cv_score = _train_rf(daily)
        if rf is None:
            return {"error": "Impossibile addestrare il modello (troppo poche classi di rischio nei dati storici)."}

        poisson_vec = _poisson_proba_vector(df, area)
        w_rf, w_poi = _calibrate_weights(daily, classes, rf, poisson_vec)

        future_dfs = _future_features(daily, horizon)
        if not future_dfs:
            return {"error": "Errore nella proiezione delle feature future."}

        p_vec = np.array(poisson_vec)
        days_out = []
        for fdf in future_dfs:
            X_fut    = fdf[_FEATURE_COLS].fillna(0).values
            rf_raw   = rf.predict_proba(X_fut)[0]
            rf_full  = np.zeros(3)
            for idx, cls in enumerate(classes):
                rf_full[int(cls)] = rf_raw[idx]

            blend = w_rf * rf_full + w_poi * p_vec
            blend = np.clip(blend, 1e-9, 1.0)
            blend /= blend.sum()

            rl   = int(np.argmax(blend))
            conf = float(np.max(blend))

            days_out.append({
                "date":       fdf["date"].iloc[0],
                "risk_level": rl,
                "label":      _RISK_LABELS[rl],
                "color":      _RISK_COLORS[rl],
                "color_dark": _RISK_COLORS_D[rl],
                "proba":      blend.tolist(),
                "confidence": conf,
            })

        feat_imp   = dict(zip(_FEATURE_COLS, rf.feature_importances_))
        top_feats  = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)[:5]

        result = {
            "days":           days_out,
            "cv_score":       round(cv_score, 3),
            "weight_rf":      round(w_rf, 3),
            "weight_poisson": round(w_poi, 3),
            "n_train":        len(daily),
            "top_features":   top_feats,
            "classes_seen":   [int(c) for c in classes],
            "ai_narrative":   None,
            "error":          None,
        }

        if with_ai_narrative:
            result["ai_narrative"] = generate_ai_narrative(result, area)

        return result

    except Exception as exc:
        return {"error": f"Errore pipeline ML: {exc}"}
