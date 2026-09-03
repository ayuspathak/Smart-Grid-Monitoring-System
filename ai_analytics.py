"""Machine-learning utilities used by the Ayush smart-grid dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor


def _numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "voltage_a", "voltage_b", "voltage_c",
        "current_a", "current_b", "current_c",
        "active_power", "power_factor", "frequency",
    ]
    return df[columns].astype(float).interpolate().bfill().ffill()


def detect(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    result = df.copy()
    model = IsolationForest(
        n_estimators=140,
        max_samples="auto",
        contamination=0.05,
        random_state=42,
    )
    features = _numeric_features(result)
    labels = model.fit_predict(features)
    result["anomaly"] = labels == -1
    result["anomaly_score"] = model.decision_function(features).round(4)

    va = result[["voltage_a", "voltage_b", "voltage_c"]].mean(axis=1)
    result["phase_unbalance_pct"] = (
        result[["voltage_a", "voltage_b", "voltage_c"]]
        .sub(va, axis=0).abs().max(axis=1).div(va).mul(100)
    ).round(2)
    return result


def summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"level": "NO DATA", "flags": 0}
    flags = int(df["anomaly"].sum())
    rate = flags / len(df)
    level = "NORMAL" if rate < 0.03 else "WATCH" if rate < 0.08 else "ATTENTION"
    return {"level": level, "flags": flags}


def forecast(df: pd.DataFrame, hours: int = 12) -> pd.DataFrame:
    if df.empty or "active_power" not in df.columns:
        return pd.DataFrame()
    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    hourly = (
        data.sort_values("timestamp")
        .set_index("timestamp")["active_power"]
        .resample("1h").mean().dropna().reset_index()
    )
    if len(hourly) < 14:
        return pd.DataFrame()

    hourly["hour"] = hourly["timestamp"].dt.hour
    hourly["dow"] = hourly["timestamp"].dt.dayofweek
    hourly["lag_1"] = hourly["active_power"].shift(1)
    hourly["lag_2"] = hourly["active_power"].shift(2)
    hourly = hourly.dropna()

    model = RandomForestRegressor(
        n_estimators=120, min_samples_leaf=2, random_state=42
    )
    model.fit(hourly[["hour", "dow", "lag_1", "lag_2"]], hourly["active_power"])

    last_time = hourly.iloc[-1]["timestamp"]
    lag1 = float(hourly.iloc[-1]["active_power"])
    lag2 = float(hourly.iloc[-2]["active_power"])
    rows = []
    for step in range(1, hours + 1):
        stamp = last_time + pd.Timedelta(hours=step)
        row = pd.DataFrame([{
            "hour": stamp.hour,
            "dow": stamp.dayofweek,
            "lag_1": lag1,
            "lag_2": lag2,
        }])
        pred = float(model.predict(row)[0])
        rows.append((stamp, round(pred, 3)))
        lag2, lag1 = lag1, pred
    return pd.DataFrame(rows, columns=["time", "forecast_kw"])
