import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import database as storage
import ai_analytics as analytics
import fault_analysis

try:
    import feeder_model
except ImportError:
    feeder_model = None

st.set_page_config(page_title="Smart Grid", page_icon="⚡", layout="wide")
st.title("⚡ Smart Grid Monitoring System")
st.caption("Ayush Pathak · B.Tech Electrical Engineering · BIET Jhansi")
storage.initialize()

with st.sidebar:
    page = st.radio("Section", ["Dashboard", "Fault Study", "Analytics"])
    node = st.selectbox("Telemetry node", ["NODE_01", "FEEDER_A", "FEEDER_B"])
    if st.button("Generate readings"):
        storage.add_sample_batch(12)
        st.rerun()

if page == "Dashboard":
    df = storage.recent_telemetry(120, node=node)
    if df.empty:
        st.info("No telemetry yet. Use the sidebar button to generate sample readings.")
    else:
        latest = df.iloc[0]
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Phase A", f"{latest.voltage_a:.1f} V")
        c2.metric("Phase B", f"{latest.voltage_b:.1f} V")
        c3.metric("Phase C", f"{latest.voltage_c:.1f} V")
        mean_v = (latest.voltage_a+latest.voltage_b+latest.voltage_c)/3
        spread = max(abs(latest.voltage_a-mean_v),abs(latest.voltage_b-mean_v),abs(latest.voltage_c-mean_v))/mean_v*100
        c4.metric("Phase spread", f"{spread:.2f}%")
        view=df.sort_values("timestamp").copy(); view["timestamp"]=pd.to_datetime(view["timestamp"])
        fig=go.Figure()
        for col,label in (("voltage_a","A"),("voltage_b","B"),("voltage_c","C")):
            fig.add_trace(go.Scatter(x=view.timestamp,y=view[col],mode="lines",name=f"Phase {label}"))
        fig.update_layout(title=f"Voltage history · {node}",height=360,margin=dict(l=20,r=20,t=55,b=20))
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(df.head(15),use_container_width=True,hide_index=True)

elif page == "Fault Study":
    st.subheader("Fault What-If Study")
    a,b,c=st.columns(3)
    kind=a.selectbox("Fault type",["3-phase","line-line","single-line-ground"])
    feeder=b.selectbox("Feeder",["Industrial","Commercial","Residential"])
    resistance=c.slider("Fault resistance (Ω)",0.02,0.40,0.08,0.02)
    result=fault_analysis.calculate(kind,feeder,resistance)
    x,y,z=st.columns(3)
    x.metric("Current",f"{result['fault_current_ka']:.2f} kA")
    y.metric("Clearing estimate",f"{result['clearing_ms']:.0f} ms")
    z.metric("Severity",result['severity'])
    profile=pd.DataFrame(result['voltage_profile'])
    fig=go.Figure(go.Bar(x=profile.node,y=profile.voltage_pu))
    fig.update_layout(title="Simplified voltage dip profile",yaxis_title="Voltage (p.u.)",height=340)
    st.plotly_chart(fig,use_container_width=True)
    if st.button("Save case"):
        storage.save_fault_result(result); st.success("Saved to local history.")

else:
    st.subheader("Telemetry Analytics")
    df=storage.recent_telemetry(360)
    if df.empty:
        st.info("Generate readings first.")
    else:
        checked=analytics.detect(df); info=analytics.summary(checked)
        a,b,c=st.columns(3)
        a.metric("Grid status",info['level']); b.metric("Records",len(checked)); c.metric("Flags",int(checked.anomaly.sum()))
        flagged=checked.loc[checked.anomaly,['timestamp','node_id','active_power','power_factor','phase_unbalance_pct','anomaly_score']]
        st.dataframe(flagged.head(20),use_container_width=True,hide_index=True)
        pred=analytics.forecast(df,12)
        if not pred.empty:
            fig=go.Figure(go.Scatter(x=pred.time,y=pred.forecast_kw,mode='lines+markers',name='Forecast'))
            fig.update_layout(title='Next 12-hour load estimate',height=350)
            st.plotly_chart(fig,use_container_width=True)

st.divider(); st.caption("Demo data is simulated locally for academic use.")
