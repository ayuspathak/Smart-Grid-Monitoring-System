"""Compatibility layer for older local imports."""

from feeder_model import GridStudy, run

GridSimulator = GridStudy

__all__ = ["GridStudy", "GridSimulator", "run"]
