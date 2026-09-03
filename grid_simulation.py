"""Compatibility entry point for the rebuilt feeder model.

The project now keeps the actual model in feeder_model.py. This small wrapper
is left temporarily so older local scripts fail less dramatically after the
reorganisation.
"""

from feeder_model import GridStudy, run

GridSimulator = GridStudy
run_power_flow = run

__all__ = ["GridStudy", "GridSimulator", "run"]
