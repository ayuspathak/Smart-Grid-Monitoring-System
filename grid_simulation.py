"""Compatibility import for the rebuilt feeder model."""
from feeder_model import GridStudy
GridSimulator = GridStudy
__all__ = ["GridStudy", "GridSimulator"]
