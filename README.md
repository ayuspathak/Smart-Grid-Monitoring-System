# Smart Grid Monitoring System

A practical B.Tech project for monitoring simulated three-phase electrical data and studying how the same measurements can be used for power-flow checks, fault analysis, and simple predictive analytics.

This repository is a reworked student implementation based on the public smart-grid monitoring project by `yashdeep043`. The dashboard layout, wording, project structure, and parts of the analysis workflow are being developed as a separate version.

## What is included

- Three-phase voltage, current, power-factor, and frequency monitoring
- Local SQLite telemetry/history storage
- Distribution-network power-flow simulation with Pandapower when available
- A lightweight fallback model for exploring the dashboard without Pandapower
- Fault / short-circuit what-if analysis
- Isolation Forest anomaly detection
- Random Forest based load forecasting
- Streamlit dashboard
- Optional ESP32/MQTT telemetry path and local simulator

## Main files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit monitoring dashboard |
| `grid_simulation.py` | Distribution-grid model and power-flow calculations |
| `fault_analysis.py` | Fault and protection calculations |
| `ai_analytics.py` | Anomaly detection and load forecasting |
| `database.py` | SQLite storage and telemetry history |
| `esp32_simulator.py` | Generates sample sensor telemetry |
| `run_system.py` | Application launcher |
| `requirements.txt` | Python dependencies |

## Run locally

```bash
pip install -r requirements.txt
python run_system.py
```

Then open the Streamlit address printed in the terminal.

## Project notes

The electrical values used by the simulator are demonstration values. They are intended for software testing and learning, not as measurements from a live utility network or as field engineering specifications.

## Attribution

This is a modified derivative project inspired by the public repository `yashdeep043/smart-grid-monitoring`. The original project is acknowledged as the starting point for the idea and some components; this repository is being developed as a separate student implementation.

## Author

Ayush Pathak  
B.Tech Electrical Engineering, 4th Year  
BIET Jhansi
