# Smart Grid Monitoring System

A B.Tech Electrical Engineering project by **Me** for exploring a small simulated power network through monitoring, fault studies and basic machine-learning analysis. This project is built as a compact local lab setup. Instead of depending on live utility data, it creates sample three-phase readings, stores them in SQLite, and then uses those readings for visualisation and analysis.

## What I built

- Three-phase voltage and current monitoring
- Power, power-factor and frequency tracking
- Local SQLite telemetry history
- A simplified feeder fault study
- Isolation Forest based anomaly detection
- Short-term load forecasting with Random Forest
- Interactive Streamlit dashboard
- Local telemetry simulator for testing without hardware


## Run

```bash
pip install -r requirements.txt
python run_system.py
```

Or start the dashboard directly:

```bash
streamlit run app.py
```

Use **Generate readings** in the sidebar to create another batch of sample data.

## Project idea

The data flow is deliberately simple:

**Telemetry → SQLite → Dashboard → Fault Study / ML Analysis**

The fault calculation is an educational approximation and the telemetry is simulated. The numbers should not be used for real protection settings or utility operation.

