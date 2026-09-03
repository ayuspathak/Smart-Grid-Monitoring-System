"""Machine-learning utilities for the smart-grid dashboard."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor

def _features(df):
    cols=["voltage_a","voltage_b","voltage_c","current_a","current_b","current_c","active_power","power_factor","frequency"]
    return df[cols].astype(float).interpolate().bfill().ffill()

def detect(df):
    if df.empty: return df.copy()
    result=df.copy(); x=_features(result)
    model=IsolationForest(n_estimators=140, contamination=0.05, random_state=42)
    result["anomaly"]=model.fit_predict(x)==-1
    result["anomaly_score"]=model.decision_function(x).round(4)
    mean_v=result[["voltage_a","voltage_b","voltage_c"]].mean(axis=1)
    result["phase_unbalance_pct"]=(result[["voltage_a","voltage_b","voltage_c"]].sub(mean_v,axis=0).abs().max(axis=1).div(mean_v).mul(100)).round(2)
    return result

def summary(df):
    if df.empty: return {"level":"NO DATA","flags":0}
    flags=int(df["anomaly"].sum()); rate=flags/len(df)
    return {"level":"NORMAL" if rate<.03 else "WATCH" if rate<.08 else "ATTENTION","flags":flags}

def forecast(df,hours=12):
    if df.empty or "active_power" not in df.columns: return pd.DataFrame()
    data=df.copy(); data["timestamp"]=pd.to_datetime(data["timestamp"])
    hourly=data.sort_values("timestamp").set_index("timestamp")["active_power"].resample("1h").mean().dropna().reset_index()
    if len(hourly)<14: return pd.DataFrame()
    hourly["hour"]=hourly.timestamp.dt.hour; hourly["dow"]=hourly.timestamp.dt.dayofweek
    hourly["lag1"]=hourly.active_power.shift(1); hourly["lag2"]=hourly.active_power.shift(2); hourly=hourly.dropna()
    model=RandomForestRegressor(n_estimators=120,min_samples_leaf=2,random_state=42)
    model.fit(hourly[["hour","dow","lag1","lag2"]],hourly.active_power)
    last=hourly.iloc[-1]; lag1=float(last.active_power); lag2=float(hourly.iloc[-2].active_power); rows=[]
    for step in range(1,hours+1):
        stamp=last.timestamp+pd.Timedelta(hours=step)
        pred=float(model.predict(pd.DataFrame([[stamp.hour,stamp.dayofweek,lag1,lag2]],columns=["hour","dow","lag1","lag2"]))[0])
        rows.append((stamp,round(pred,3))); lag2,lag1=lag1,pred
    return pd.DataFrame(rows,columns=["time","forecast_kw"])
