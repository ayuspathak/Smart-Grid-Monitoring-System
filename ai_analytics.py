"""Analytics helpers for the smart-grid dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor


def _features(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["voltage_a", "voltage_b", "voltage_c", "current_a", "current_b", "current_c", "power_factor", "frequency"]
    return df[cols].astype(float).fillna(0)


def detect(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    result = df.copy()
    x = _features(result)
    model = IsolationForest(n_estimators=120, contamination=0.06, random_state=24)
    result["anomaly"] = model.fit_predict(x) == -1
    result["anomaly_score"] = model.decision_function(x).round(4)
    result["health_score"] = np.clip(100 + result["anomaly_score"] * 55, 0, 100).round(1)
    return result


def summary(flagged: pd.DataFrame) -> dict:
    if flagged.empty:
        return {"level": "NO DATA", "flags": 0}
    count = int(flagged["anomaly"].sum())
    ratio = count / max(len(flagged), 1)
    if ratio < 0.03:
        level = "NORMAL"
    elif ratio < 0.08:
        level = "WATCH"
    else:
        level = "ATTENTION"
    return {"level": level, "flags": count}


def forecast(df: pd.DataFrame, hours: int = 12) -> pd.DataFrame:
    if df.empty or "active_power" not in df.columns:
        return pd.DataFrame()
    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data = data.sort_values("timestamp")
    hourly = data.set_index("timestamp")["active_power"].resample("1h").mean().dropna().reset_index()
    if len(hourly) < 12:
        return pd.DataFrame()
    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["day"] = hourly["timestamp"].dt.dayofweek
    hourly["lag1"] = hourly["active_power"].shift(1)
    hourly = hourly.dropna()
    model = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=24)
    model.fit(hourly[["hour", "day", "lag1"]], hourly["active_power"])
    last_time = hourly.iloc[-1]["timestamp"]
    lag = float(hourly.iloc[-1]["active_power"])
    rows = []
    for step in range(1, hours + 1):
        stamp = last_time + pd.Timedelta(hours=step)
        pred = float(model.predict(pd.DataFrame([[stamp.hour, stamp.dayofweek, lag]], columns=["hour","day","lag1"]))[0])
        rows.append((stamp, pred))
        lag = pred
    return pd.DataFrame(rows, columns=["time", "forecast_kw"])
