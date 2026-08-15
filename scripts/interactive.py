#!/usr/bin/env python3
"""
interactive.py

Builds interactive, standalone HTML charts (via Plotly) combining several
time series into one chart with a toggleable legend — e.g. "all syndromic
diagnoses in one chart" or "all viruses in one chart". Unlike the static
PNGs in plots.py, these let the visitor hover for exact values and
click legend entries to show/hide individual lines.

Each function writes a fully self-contained HTML file (Plotly.js loaded
from a CDN) that can be embedded in a Jekyll page via an <iframe>.
"""

import os
import plotly.graph_objects as go


def build_interactive_lines(series_dict, title, ylabel, output_path,
                             xlabel=""):
    """series_dict: {label -> pandas Series indexed by date}.
    Writes a standalone interactive HTML file to output_path."""
    fig = go.Figure()

    for label, series in series_dict.items():
        if series is None or series.empty:
            continue
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            name=label,
            hovertemplate=f"{label}<br>%{{x|%d %b %Y}}: %{{y:.2f}}<extra></extra>",
        ))

    fig.update_layout(
        title=title,
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        hovermode="x unified",
        template="plotly_white",
        legend_title_text="",
        margin=dict(l=60, r=20, t=60, b=40),
        font=dict(family="Arial, Helvetica, sans-serif", size=13),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn", full_html=True)
    print(f"  wrote interactive chart: {output_path}")
    return output_path
