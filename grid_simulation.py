"""Backward-compatible alias for the new feeder study module."""

from feeder_model import GridStudy, run

GridSimulator = GridStudy

__all__ = ["GridStudy", "GridSimulator", "run"]
