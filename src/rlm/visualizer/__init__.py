"""RLM Trajectory Visualizer.

A Streamlit-based web UI for exploring RLM execution trajectories.

Usage:
    rlm visualize [--log-dir ./logs] [--port 8501]

Or run directly:
    streamlit run -m rlm.visualizer.app
"""

from rlm.visualizer.app import main

__all__ = ["main"]
