import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import database as db
from ai_analytics import SmartGridAI
from fault_analysis import simulate_fault
from grid_simulation import GridSimulator

st.set_page_config(page_title="Smart Grid Monitor", page_icon="⚡", layout="wide")

db.init_db()
if "grid" not in st.session_state:
    st.session_state.grid = GridSimulator()
if "ai" not in st.session_state:
    st.session_state.ai = SmartGridAI()

st.title("⚡ Smart Grid Monitoring System")
st.caption("Student project dashboard · telemetry · distribution study · fault checks · basic analytics")

with st.sidebar:
    st.header("Controls")
    section = st.radio("Open section", ["Live Monitor", "Power Flow", "Fault Study", "Analytics"])
    refresh = st.checkbox("Refresh on run", value=False)
    st.markdown("---")
    st.info("Demo values are generated locally. Replace the simulator with ESP32/MQTT telemetry when hardware is connected.")

if section == "Live Monitor":
    df = db.get_recent_telemetry(180)
    if df.empty:
        st.warning("No telemetry available yet.")
    else:
        latest = df.iloc[0]
        voltage_avg = latest[["voltage_a", "voltage_b", "voltage_c"]].mean()
        imbalance = (latest[["voltage_a", "voltage_b", "voltage_c"]].sub(voltage_avg).abs().max() / voltage_avg) * 100
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Phase A", f"{latest.voltage_a:.1f} V")
        c2.metric("Phase B", f"{latest.voltage_b:.1f} V")
        c3.metric("Phase C", f"{latest.voltage_c:.1f} V")
        c4.metric("Voltage imbalance", f"{imbalance:.2f}%")

        chart = df.sort_values("timestamp").copy()
        chart["timestamp"] = pd.to_datetime(chart["timestamp"])
        fig = go.Figure()
        for col, name in [("voltage_a", "Phase A"), ("voltage_b", "Phase B"), ("voltage_c", "Phase C")]:
            fig.add_trace(go.Scatter(x=chart.timestamp, y=chart[col], mode="lines", name=name))
        fig.update_layout(height=350, title="Recent three-phase voltage")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["timestamp", "node_id", "voltage_a", "voltage_b", "voltage_c", "current_a", "current_b", "current_c", "active_power", "power_factor", "frequency", "status"]].head(12), use_container_width=True)

elif section == "Power Flow":
    st.subheader("Distribution Power Flow")
    left, right = st.columns(2)
    with left:
        load = st.slider("Load scaling", 0.6, 1.6, 1.0, 0.05)
    with right:
        solar = st.slider("Solar generation (MW)", 0.0, 1.5, 0.65, 0.05)

    result = st.session_state.grid.run_power_flow(load_scaling=load, solar_generation_mw=solar)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total load", f"{result['total_load_mw']:.2f} MW")
    m2.metric("Solar", f"{result['solar_gen_mw']:.2f} MW")
    m3.metric("Min voltage", f"{result['min_voltage_pu']:.3f} pu")
    m4.metric("Max line loading", f"{result['max_line_loading_pct']:.1f}%")

    a, b = st.columns(2)
    with a:
        st.plotly_chart(px.bar(result["buses"], x="Bus", y="Voltage (p.u.)", title="Bus voltage profile"), use_container_width=True)
    with b:
        st.plotly_chart(px.bar(result["lines"], x="Line", y="Loading (%)", title="Feeder loading"), use_container_width=True)

    if "fallback_reason" in result:
        st.caption(f"Fallback model used: {result['fallback_reason']}")

elif section == "Fault Study":
    st.subheader("Fault What-If Study")
    c1, c2, c3 = st.columns(3)
    fault_type = c1.selectbox("Fault type", ["3PH", "LL", "SLG"])
    location = c2.selectbox("Location", ["Industrial Feeder", "Commercial Feeder", "Residential Feeder"])
    resistance = c3.slider("Fault resistance (Ω)", 0.01, 0.50, 0.05, 0.01)
    result = simulate_fault(fault_type, location, resistance)
    m1, m2, m3 = st.columns(3)
    m1.metric("Estimated fault current", f"{result['fault_current_ka']:.3f} kA")
    m2.metric("Trip time", f"{result['trip_time_ms']:.1f} ms")
    m3.metric("Severity", result["severity"])
    profile = pd.DataFrame(result["voltage_profile"])
    st.plotly_chart(px.line(profile, x="node", y="voltage_pu", markers=True, title="Voltage profile during the study"), use_container_width=True)
    if st.button("Save study result"):
        db.log_fault_event(fault_type, location, result["fault_current_ka"], result["trip_time_ms"], result["severity"])
        st.success("Fault study saved locally.")

else:
    st.subheader("Analytics")
    df = db.get_recent_telemetry(300)
    if df.empty:
        st.warning("Not enough telemetry.")
    else:
        summary = st.session_state.ai.risk_summary(df)
        c1, c2 = st.columns(2)
        c1.metric("Current risk", summary["risk"])
        c2.metric("Flagged records", summary["anomalies"])
        checked = st.session_state.ai.detect_anomalies(df).sort_values("id", ascending=False)
        st.dataframe(checked[["timestamp", "node_id", "active_power", "power_factor", "anomaly", "anomaly_score"]].head(20), use_container_width=True)
        forecast = st.session_state.ai.forecast_next_day(df)
        if not forecast.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=forecast["Time"], y=forecast["Forecast (kW)"], mode="lines+markers", name="Forecast"))
            fig.add_trace(go.Scatter(x=forecast["Time"], y=forecast["Upper (kW)"], mode="lines", name="Upper", line=dict(dash="dot")))
            fig.add_trace(go.Scatter(x=forecast["Time"], y=forecast["Lower (kW)"], mode="lines", name="Lower", line=dict(dash="dot")))
            fig.update_layout(title="Next 24-hour load estimate", height=380)
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Ayush Pathak · B.Tech Electrical Engineering · BIET Jhansi")
