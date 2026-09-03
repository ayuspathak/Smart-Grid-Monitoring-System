# Project Notes

## Idea

The project is meant to be a compact smart-grid lab environment rather than a utility-grade monitoring platform. The data path is deliberately simple so that each stage can be tested on its own.

**Telemetry → storage → feeder study → fault study → analytics → dashboard**

## Design choices

- SQLite keeps the demo self-contained.
- The telemetry generator uses small changes in load and phase values instead of perfectly constant readings.
- The feeder model has separate operating controls for demand and rooftop PV.
- Fault calculations are kept intentionally simplified and are labelled as such in the UI.
- The ML layer uses anomaly detection plus a short load forecast; neither is presented as a protection or dispatch system.

## Author

Ayush Pathak  
B.Tech Electrical Engineering, 4th Year  
BIET Jhansi
