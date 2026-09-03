"""Small ML helpers for anomaly flags and short load forecasts."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor


class SmartGridAI:
    def __init__(self):
        self.anomaly_model = None
        self.load_model = None

    def detect_anomalies(self, telemetry: pd.DataFrame) -> pd.DataFrame:
        if telemetry.empty:
            return telemetry.copy()
        features = [c for c in ["voltage_a", "voltage_b", "voltage_c", "current_a", "current_b", "current_c", "power_factor"] if c in telemetry.columns]
        x = telemetry[features].fillna(0)
        self.anomaly_model = IsolationForest(contamination=0.04, random_state=7)
        labels = self.anomaly_model.fit_predict(x)
        result = telemetry.copy()
        result["anomaly"] = labels == -1
        result["anomaly_score"] = self.anomaly_model.decision_function(x).round(4)
        return result

    def forecast_next_day(self, telemetry: pd.DataFrame, periods=24) -> pd.DataFrame:
        if telemetry.empty or "active_power" not in telemetry.columns:
            return pd.DataFrame()
        data = telemetry.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        data = data.sort_values("timestamp")
        data["hour"] = data["timestamp"].dt.hour
        data["dow"] = data["timestamp"].dt.dayofweek
        data["load_lag"] = data["active_power"].shift(1)
        data = data.dropna()
        if len(data) < 20:
            return pd.DataFrame()

        features = ["hour", "dow", "load_lag"]
        self.load_model = RandomForestRegressor(n_estimators=80, random_state=7, min_samples_leaf=2)
        self.load_model.fit(data[features], data["active_power"])
        last = data.iloc[-1]["timestamp"]
        rows = []
        lag = float(data.iloc[-1]["active_power"])
        for step in range(1, periods + 1):
            stamp = last + pd.Timedelta(hours=step)
            pred = float(self.load_model.predict(pd.DataFrame([{
                "hour": stamp.hour, "dow": stamp.dayofweek, "load_lag": lag
            }]))[0])
            rows.append((stamp, pred, pred * 0.9, pred * 1.1))
            lag = pred
        return pd.DataFrame(rows, columns=["Time", "Forecast (kW)", "Lower (kW)", "Upper (kW)"])

    def risk_summary(self, telemetry: pd.DataFrame) -> dict:
        if telemetry.empty:
            return {"risk": "No data", "anomalies": 0}
        checked = self.detect_anomalies(telemetry)
        anomalies = int(checked["anomaly"].sum())
        if anomalies == 0:
            risk = "LOW"
        elif anomalies <= 3:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        return {"risk": risk, "anomalies": anomalies}


if __name__ == "__main__":
    print("AI module ready")
