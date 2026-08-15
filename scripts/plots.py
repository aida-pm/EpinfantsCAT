#!/usr/bin/env python3
"""
plots.py

Reusable plotting functions for the EpinfantsCAT surveillance data.
Styled to match the conventions from the original research notebook
(Arial font, consistent color palette, dual-axis comparisons).

Each function saves a PNG to disk and returns a small metadata dict
describing what it made — this metadata is what generate_site_plots.py
uses to build the Jekyll pages automatically.
"""

import os
import re
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------
# Shared style, matching the look of the original notebook
# --------------------------------------------------------------------------
PALETTE = {
    "purple": "#9B59B6",
    "blue": "#3498DB",
    "teal": "#16A085",
    "orange": "#E67E22",
    "red": "#C0392B",
    "green": "#27AE60",
}


def set_style():
    plt.rcParams.update({
        "font.size": 14,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "axes.grid": False,
        "figure.dpi": 150,
    })


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def _save(fig, filename, images_dir):
    os.makedirs(images_dir, exist_ok=True)
    path = os.path.join(images_dir, filename)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_series(series, title, ylabel="", color=PALETTE["blue"], description="",
                 images_dir="assets/images/plots", slug=None):
    """Plot a pre-computed pandas Series indexed by date — e.g. the output
    of population.compute_national_incidence(). Use this when the
    aggregation/math already happened elsewhere and you just need the plot."""
    set_style()
    slug = slug or slugify(title)
    filename = f"{slug}.png"

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(series.index, series.values, color=color, linewidth=2)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.set_title(title, fontsize=16, fontweight="bold")
    fig.tight_layout()

    _save(fig, filename, images_dir)
    return {"title": title, "filename": filename, "slug": slug, "description": description}


def plot_timeseries(df, date_col, value_col, title, ylabel=None,
                     color=PALETTE["blue"], description="",
                     images_dir="assets/images/plots", slug=None):
    """Single-line time series, e.g. daily/weekly case counts."""
    set_style()
    slug = slug or slugify(title)
    filename = f"{slug}.png"

    grouped = df.groupby(date_col)[value_col].sum(numeric_only=True)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(grouped.index, grouped.values, color=color, linewidth=2)
    ax.set_ylabel(ylabel or value_col, fontsize=14)
    ax.set_xlabel("")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.set_title(title, fontsize=16, fontweight="bold")
    fig.tight_layout()

    _save(fig, filename, images_dir)
    return {"title": title, "filename": filename, "slug": slug, "description": description}


def plot_dual_axis_timeseries(df, date_col, col1, label1, col2, label2,
                               title, color1=PALETTE["purple"], color2=PALETTE["teal"],
                               description="", images_dir="assets/images/plots", slug=None):
    """Two variables on separate y-axes sharing the same time axis —
    same pattern as the Bronchiolitis/COVID-19 comparison in the notebook."""
    set_style()
    slug = slug or slugify(title)
    filename = f"{slug}.png"

    g1 = df.groupby(date_col)[col1].sum(numeric_only=True)
    g2 = df.groupby(date_col)[col2].sum(numeric_only=True)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(g1.index, g1.values, color=color1, linewidth=2, label=label1)
    ax.set_ylabel(label1, fontsize=14)
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    ax2 = ax.twinx()
    ax2.plot(g2.index, g2.values, color=color2, linewidth=2.5, label=label2)
    ax2.set_ylabel(label2, rotation=270, labelpad=20, fontsize=14)

    ax.set_title(title, fontsize=16, fontweight="bold")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    fig.tight_layout()

    _save(fig, filename, images_dir)
    return {"title": title, "filename": filename, "slug": slug, "description": description}


def plot_multi_series(df, date_col, value_cols, labels=None, colors=None,
                       title="", ylabel="", description="",
                       images_dir="assets/images/plots", slug=None):
    """Multiple lines on one axis — e.g. comparing several syndromes or age
    groups over the same time period."""
    set_style()
    slug = slug or slugify(title)
    filename = f"{slug}.png"
    labels = labels or value_cols
    colors = colors or list(PALETTE.values())

    fig, ax = plt.subplots(figsize=(12, 5))
    for col, label, color in zip(value_cols, labels, colors):
        grouped = df.groupby(date_col)[col].sum(numeric_only=True)
        ax.plot(grouped.index, grouped.values, label=label, color=color, linewidth=2)

    ax.set_ylabel(ylabel, fontsize=14)
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.legend(loc="upper left")
    fig.tight_layout()

    _save(fig, filename, images_dir)
    return {"title": title, "filename": filename, "slug": slug, "description": description}


def plot_top_categories(df, cat_col, title, description="",
                         images_dir="assets/images/plots", slug=None, top_n=15):
    """Bar chart of the most frequent values in a categorical column."""
    set_style()
    slug = slug or slugify(title)
    filename = f"{slug}.png"

    fig, ax = plt.subplots(figsize=(10, 5))
    df[cat_col].value_counts().head(top_n).plot(kind="bar", ax=ax, color=PALETTE["blue"])
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    fig.tight_layout()

    _save(fig, filename, images_dir)
    return {"title": title, "filename": filename, "slug": slug, "description": description}
