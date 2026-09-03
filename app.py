"""Ayush Smart Grid Monitoring dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analytics_engine as analytics
import feeder_model
import fault_study
import storage

st.set_page_config(page_title="Ayush Smart Grid", page_icon="⚡", layout="wide")
st.title("⚡ Smart Grid Monitoring System")
st.caption("Ayush Pathak · B.Tech Electrical Engineering · BIET Jhansi")

storage.initialize()

with st.sidebar:
    st.header("Controls")
    view = st.radio("Section", ["Dashboard", "Feeder Study", "Fault Study", "Analytics"])
    node = st.selectbox("Node", ["AYUSH_NODE_01", "FEEDER_A", "FEEDER_B"])
    if st.button("Generate fresh sample"):
        storage.add_sample_batch(12)
        st.rerun()

if view == "Dashboard":
    data = storage.recent_telemetry(120, node=node)
    st.subheader("Recent electrical telemetry")
    if data.empty:
        st.info("No readings yet. Generate a sample batch from the sidebar.")
    else:
        latest = data.iloc[0]
        vals = [float(latest[c]) for c in ("voltage_a", "voltage_b", "voltage_c")]
        avg_v = sum(vals) / 3
        deviation = max(abs(v - avg_v) for v in vals) / avg_v * 100
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Phase A", f"{vals[0]:.1f} V")
        c2.metric("Phase B", f"{vals[1]:.1f} V")
        c3.metric("Phase C", f"{vals[2]:.1f} V")
        c4.metric("Phase spread", f"{deviation:.2f}%")

        chart = data.sort_values("timestamp").copy()
        chart["timestamp"] = pd.to_datetime(chart["timestamp"])
        fig = go.Figure()
        for col, label in (("voltage_a","Phase A"),("voltage_b","Phase B"),("voltage_c","Phase C")):
            fig.add_trace(go.Scatter(x=chart["timestamp"], y=chart[col], mode="lines", name=label))
        fig.update_layout(title=f"Voltage history · {node}", height=360, margin=dict(l=20,r=20,t=55,b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(data.head(15), use_container_width=True, hide_index=True)

elif view == "Feeder Study":
    st.subheader("Distribution Feeder Study")
    c1,c2 = st.columns(2)
    load = c1.slider("Load level", 0.70, 1.50, 1.00, 0.05)
    pv = c2.slider("Solar output (MW)", 0.00, 1.20, 0.50, 0.05)
    result = feeder_model.run(load, pv)
    a,b,c,d = st.columns(4)
    a.metric("Demand", f"{result['demand_mw']:.2f} MW")
    b.metric("PV", f"{result['pv_mw']:.2f} MW")
    c.metric("Min voltage", f"{result['minimum_voltage_pu']:.3f} pu")
    d.metric("Peak loading", f"{result['peak_loading_pct']:.1f}%")
    left,right = st.columns(2)
    left.plotly_chart(feeder_model.voltage_plot(result["buses"]), use_container_width=True)
    right.plotly_chart(feeder_model.loading_plot(result["feeders"]), use_container_width=True)
    if st.button("Save feeder run"):
        storage.save_feeder_result(result, load, pv)
        st.success("Run saved locally.")

elif view == "Fault Study":
    st.subheader("Fault What-If Study")
    c1,c2,c3 = st.columns(3)
    fault = c1.selectbox("Fault type", ["3-phase", "line-line", "single-line-ground"])
    feeder = c2.selectbox("Feeder", ["Industrial", "Commercial", "Residential"])
    resistance = c3.slider("Fault resistance (Ω)", 0.02, 0.40, 0.08, 0.02)
    result = fault_study.calculate(fault, feeder, resistance)
    a,b,c = st.columns(3)
    a.metric("Estimated current", f"{result['fault_current_ka']:.2f} kA")
    b.metric("Clearing estimate", f"{result['clearing_ms']:.0f} ms")
    c.metric("Severity", result["severity"])
    profile = pd.DataFrame(result["voltage_profile"])
    fig = go.Figure(go.Bar(x=profile["node"], y=profile["voltage_pu"]))
    fig.update_layout(title="Simplified voltage dip profile", yaxis_title="Voltage (p.u.)", height=350)
    st.plotly_chart(fig, use_container_width=True)
    if st.button("Save fault case"):
        storage.save_fault_result(result)
        st.success("Fault case saved.")

else:
    st.subheader("Analytics")
    data = storage.recent_telemetry(360)
    if data.empty:
        st.info("Generate sample telemetry first.")
    else:
        flagged = analytics.detect(data)
        summary = analytics.summary(flagged)
        a,b,c = st.columns(3)
        a.metric("Risk level", summary["level"])
        b.metric("Readings checked", len(flagged))
        c.metric("Flags", int(flagged["anomaly"].sum()))
        st.dataframe(flagged.loc[flagged["anomaly"], ["timestamp","node_id","active_power","power_factor","anomaly_score"]].head(20), use_container_width=True, hide_index=True)
        forecast = analytics.forecast(data, hours=12)
        if not forecast.empty:
            fig = go.Figure(go.Scatter(x=forecast["time"], y=forecast["forecast_kw"], mode="lines+markers", name="Forecast"))
            fig.update_layout(title="Next 12-hour load estimate", height=350)
            st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Demo values are simulated locally. This project is intended for academic study, not live utility operation.")
