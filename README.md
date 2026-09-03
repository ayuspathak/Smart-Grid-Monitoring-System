# Smart Grid Monitoring System

A B.Tech Electrical Engineering project for looking at a small simulated distribution network from three angles: **measurement**, **electrical behaviour**, and **data analytics**.

I built the current version around a simple workflow that is easy to run and explain:

1. generate sample three-phase telemetry
2. store the readings locally
3. inspect feeder voltage/loading under different operating conditions
4. run a simple fault what-if calculation
5. flag unusual measurements with machine learning
6. make a short load forecast from the stored history

## Project structure

```text
Smart-Grid-Monitoring-System/
├── app.py                 # Streamlit dashboard
├── database.py            # SQLite storage and sample data
├── feeder_model.py        # Feeder calculations and plots
├── fault_study.py         # Simplified fault study
├── analytics_engine.py    # anomaly detection + forecasting
├── telemetry_simulator.py # local three-phase data generator
├── run_system.py          # launcher
├── requirements.txt
└── PROJECT_NOTES.md
```

## Run it

```bash
pip install -r requirements.txt
python run_system.py
```

A browser window can then be opened at the Streamlit address printed in the terminal.

You can also run the dashboard directly:

```bash
streamlit run app.py
```

## What is simulated

The telemetry and network values are generated for learning and software testing. They are not measurements from a real utility network, and the simplified fault study is not intended for relay settings or field design.

## Main ideas demonstrated

- Three-phase electrical telemetry handling
- Voltage imbalance calculation
- Feeder operating-point study
- Simple voltage-drop and loading analysis
- Fault current estimation using a simplified impedance model
- Isolation Forest anomaly detection
- Short-horizon load forecasting
- SQLite-based local history
- Interactive Streamlit visualisation

## Author

**Ayush Pathak**  
B.Tech Electrical Engineering, 4th Year  
BIET Jhansi
