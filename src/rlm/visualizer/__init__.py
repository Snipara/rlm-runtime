"""Snipara Sandbox trajectory visualizer.

A Streamlit-based web UI for exploring Snipara Sandbox execution trajectories.

Usage:
    snipara-sandbox visualize [--log-dir ./logs] [--port 8501]

Or run directly:
    streamlit run -m snipara_sandbox.visualizer.app
"""

from rlm.visualizer.app import main

__all__ = ["main"]
