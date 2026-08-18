#!/usr/bin/env python3
"""
interactive.py

Builds interactive, standalone HTML charts (via Plotly) for the
EpinfantsCAT site, as orchestrated by generate_site_plots.py:

    - categorize(name)
        Maps a raw "diagnostic" or "virus" label to one of
        "grip" / "vrs" / "covid19" / "altres".

    - build_incidence_by_age(df, category, disease_col, value_col, output_path)
        Syndromic incidence, one line per age group + Total, on a
        single chart. For "altres" (which bundles several distinct
        diagnostics) a dropdown selects which diagnostic is shown.

    - build_seasonal_incidence(df, category, disease_col, output_path)
        Grid of subplots (Total + one per age group), each comparing
        the pre-pandemic average season (Sep 2014-Aug 2020, grey
        dashed) against every season since Sep 2020, all plotted on a
        shared Sep->Aug axis. Dropdown for "altres".

    - build_multitest_by_age(df, category, output_path)
        Multitest incidence (left axis) + positivity (right axis), one
        pair of lines per age group + Total. Dropdown for "altres".

    - build_seasonal_multitest(df, category, output_path)
        Same seasonal-grid idea as build_seasonal_incidence, but for
        multitest incidence + positivity (dual axis). Dropdown for
        "altres".

    - build_combined_viruses(multitests, output_path)
    - build_combined_diagnoses(sindromic, output_path)
        Homepage overview charts: every virus / every diagnostic on
        one chart with a toggleable legend.

Each function writes a fully self-contained HTML file (Plotly.js
loaded from a CDN) meant to be embedded in a Jekyll page via an
<iframe>.
"""

import os
import unicodedata

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots

import population


# --------------------------------------------------------------------------
# categorize()
# --------------------------------------------------------------------------
#
# The raw "diagnostic" / "virus" text values from SIVIC are not known
# in advance, so categories are assigned via keyword matching on the
# (accent-stripped, lowercased) label. Anything that doesn't match a
# keyword falls into "altres".
#
# IMPORTANT: once you've generated the site once, check
# assets/interactive/*.html (or print sindromic['diagnostic'].unique()
# / multitests['virus'].unique()) to confirm every label lands in the
# category you expect, and extend the keyword lists below if needed.

CATEGORY_KEYWORDS = {
    "grip": [
        "grip",
        "influ",
    ],
    "vrs": [
        "vrs",
        "sincitial",
        "bronquiolitis",
        "respiratori sincitial",
        "rsv",
    ],
    "covid19": [
        "covid",
        "sars-cov",
        "sars cov",
        "sarscov",
        "coronavirus",
    ],
}


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def categorize(name) -> str:
    """Map a raw diagnostic/virus label to grip / vrs / covid19 / altres."""
    normalized = _strip_accents(str(name)).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category

    return "altres"


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

PALETTE = qualitative.Vivid
SEASON_START_MONTH = 9  # September
PREPANDEMIC_LAST_START_YEAR = 2020  # seasons starting before Sep 2020

MONTH_TICK_DAYS = [0, 30, 61, 91, 122, 153, 181, 212, 243, 273, 304, 334]
MONTH_TICK_LABELS = [
    "Set", "Oct", "Nov", "Des", "Gen", "Feb",
    "Mar", "Abr", "Maig", "Jun", "Jul", "Ago",
]


def _write(fig, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn", full_html=True)
    print(f"  wrote interactive chart: {output_path}")
    return output_path


def _age_panels_present(df, age_col="grup_edat"):
    """Ordered list of age groups (Total last) actually present in df."""
    present = set(df[age_col].astype(str).unique())
    return [a for a in population.get_age_groups_with_total() if a in present]


def build_interactive_lines(series_dict, title, ylabel, output_path, xlabel=""):
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

    return _write(fig, output_path)


def _season_label(date: pd.Timestamp, start_month: int = SEASON_START_MONTH) -> str:
    start_year = date.year if date.month >= start_month else date.year - 1
    return f"{start_year}-{start_year + 1}"


def _seasonal_split(series: pd.Series, start_month: int = SEASON_START_MONTH):
    """
    series: daily pandas Series indexed by date.

    Returns (prepandemic_avg, seasons) where:
      - prepandemic_avg is a DataFrame [day, value] averaging every
        season starting before PREPANDEMIC_LAST_START_YEAR.
      - seasons is an ordered dict {season_label: DataFrame[day, value]}
        for every season from PREPANDEMIC_LAST_START_YEAR onward.
    """
    s = series.dropna()
    if s.empty:
        return pd.DataFrame(columns=["day", "value"]), {}

    records = []
    for date, value in s.items():
        start_year = date.year if date.month >= start_month else date.year - 1
        season_start = pd.Timestamp(year=start_year, month=start_month, day=1)
        day = (date - season_start).days
        records.append((start_year, f"{start_year}-{start_year + 1}", day, value))

    d = pd.DataFrame(records, columns=["start_year", "season", "day", "value"])

    prepandemic = d[d["start_year"] < PREPANDEMIC_LAST_START_YEAR]
    prepandemic_avg = (
        prepandemic.groupby("day")["value"].mean().reset_index()
        if not prepandemic.empty else pd.DataFrame(columns=["day", "value"])
    )

    seasons = {}
    recent = d[d["start_year"] >= PREPANDEMIC_LAST_START_YEAR]
    for label in sorted(recent["season"].unique()):
        sub = recent[recent["season"] == label].sort_values("day")
        seasons[label] = sub[["day", "value"]]

    return prepandemic_avg, seasons


def _totals_across_ages(sub: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse a multitest slice (one or more age groups) into a "Total"
    series by summing the raw positive/total_tests/poblacio counts
    (NOT the already-computed incidence/positivity, since those aren't
    additive) and recomputing incidence + positivity from the sums.
    """
    g = sub.groupby("data").agg(
        positive=("positive", "sum"),
        total_tests=("total_tests", "sum"),
        poblacio=("poblacio", "sum"),
    )

    g["incidencia"] = (g["positive"] / g["poblacio"]) * 100_000
    g.loc[g["poblacio"] <= 0, "incidencia"] = pd.NA

    g["positivity"] = (g["positive"] / g["total_tests"]) * 100
    g.loc[g["total_tests"] <= 0, "positivity"] = pd.NA

    return g


# --------------------------------------------------------------------------
# 1. Syndromic incidence per age group + total (single chart)
# --------------------------------------------------------------------------

def build_incidence_by_age(df, category, disease_col, value_col, output_path):
    d = df.dropna(subset=["data", value_col]).copy()

    if d.empty:
        return None

    ages = _age_panels_present(d)
    fig = go.Figure()

    if category == "altres":
        diseases = sorted(d[disease_col].astype(str).unique())
        trace_disease = []

        for disease in diseases:
            sub_disease = d[d[disease_col].astype(str) == disease]
            for i, age in enumerate(ages):
                sub = sub_disease[sub_disease["grup_edat"] == age].groupby("data")[value_col].sum()
                fig.add_trace(go.Scatter(
                    x=sub.index, y=sub.values, mode="lines", name=age,
                    line=dict(color=PALETTE[i % len(PALETTE)]),
                    visible=(disease == diseases[0]),
                ))
                trace_disease.append(disease)

        buttons = [
            dict(
                label=disease,
                method="update",
                args=[
                    {"visible": [dd == disease for dd in trace_disease]},
                    {"title.text": f"Altres — incidència sindròmica — {disease}"},
                ],
            )
            for disease in diseases
        ]

        if buttons:
            fig.update_layout(updatemenus=[dict(
                active=0, buttons=buttons, x=1, xanchor="right", y=1.15,
            )])

        title = f"Altres — incidència sindròmica — {diseases[0]}" if diseases else "Altres"

    else:
        for i, age in enumerate(ages):
            sub = d[d["grup_edat"] == age].groupby("data")[value_col].sum()
            fig.add_trace(go.Scatter(
                x=sub.index, y=sub.values, mode="lines", name=age,
                line=dict(color=PALETTE[i % len(PALETTE)]),
            ))

        title = f"Incidència sindròmica — {category}"

    fig.update_layout(
        title=title,
        yaxis_title="Incidència (per 100.000 hab.)",
        hovermode="x unified",
        template="plotly_white",
        legend_title_text="Grup d'edat",
        margin=dict(l=60, r=20, t=80, b=40),
    )

    return _write(fig, output_path)


# --------------------------------------------------------------------------
# 2. Multitest incidence + positivity per age group + total
# --------------------------------------------------------------------------

def build_multitest_by_age(df, category, output_path):
    d = df.dropna(subset=["data"]).copy()

    if d.empty:
        return None

    age_groups = [a for a in population.get_age_groups() if a in set(d["grup_edat"].astype(str))]
    panels = age_groups + ["Total"]

    diseases = sorted(d["virus"].astype(str).unique()) if category == "altres" else [None]

    fig = go.Figure()
    trace_disease = []

    for disease in diseases:
        sub_all = d if disease is None else d[d["virus"].astype(str) == disease]
        visible = (disease is None) or (disease == diseases[0])

        for k, age in enumerate(panels):
            color = PALETTE[k % len(PALETTE)]

            if age == "Total":
                g = _totals_across_ages(sub_all)
            else:
                g = (
                    sub_all[sub_all["grup_edat"] == age]
                    .groupby("data")[["incidencia", "positivity"]]
                    .sum(min_count=1)
                )

            fig.add_trace(go.Scatter(
                x=g.index, y=g["incidencia"], mode="lines",
                name=f"{age} — incidència", line=dict(color=color),
                legendgroup=age, visible=visible,
            ))
            trace_disease.append(disease)

            fig.add_trace(go.Scatter(
                x=g.index, y=g["positivity"], mode="lines",
                name=f"{age} — positivitat", line=dict(color=color, dash="dot"),
                legendgroup=age, yaxis="y2", visible=visible,
            ))
            trace_disease.append(disease)

    if category == "altres" and len(diseases) > 1:
        buttons = [
            dict(
                label=disease,
                method="update",
                args=[
                    {"visible": [dd == disease for dd in trace_disease]},
                    {"title.text": f"Altres — multitests — {disease}"},
                ],
            )
            for disease in diseases
        ]
        fig.update_layout(updatemenus=[dict(
            active=0, buttons=buttons, x=1, xanchor="right", y=1.15,
        )])

    title = (
        f"Altres — multitests — {diseases[0]}"
        if category == "altres" and diseases else f"Multitests — {category}"
    )

    fig.update_layout(
        title=title,
        yaxis=dict(title="Incidència de proves positives (per 100.000 hab.)"),
        yaxis2=dict(title="Positivitat (%)", overlaying="y", side="right"),
        hovermode="x unified",
        template="plotly_white",
        legend_title_text="",
        margin=dict(l=60, r=60, t=80, b=40),
    )

    return _write(fig, output_path)


# --------------------------------------------------------------------------
# 3. Seasonal grid: syndromic incidence
# --------------------------------------------------------------------------

def build_seasonal_incidence(df, category, disease_col, output_path):
    d = df.dropna(subset=["data"]).copy()

    if d.empty:
        return None

    ages = _age_panels_present(d)
    if not ages:
        return None

    diseases = sorted(d[disease_col].astype(str).unique()) if category == "altres" else [None]

    ncols = 2 if len(ages) > 1 else 1
    nrows = -(-len(ages) // ncols)

    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=ages)
    trace_disease = []

    for disease in diseases:
        sub_all = d if disease is None else d[d[disease_col].astype(str) == disease]
        visible = (disease is None) or (disease == diseases[0])
        first_of_disease = True

        for i, age in enumerate(ages):
            row, col = i // ncols + 1, i % ncols + 1
            series = sub_all[sub_all["grup_edat"] == age].groupby("data")["incidencia"].sum()
            prepandemic_avg, seasons = _seasonal_split(series)

            if not prepandemic_avg.empty:
                fig.add_trace(go.Scatter(
                    x=prepandemic_avg["day"], y=prepandemic_avg["value"], mode="lines",
                    line=dict(color="grey", dash="dash"), name="Mitjana prepandèmica",
                    legendgroup="prepandemic", showlegend=first_of_disease,
                    visible=visible,
                ), row=row, col=col)
                trace_disease.append(disease)
                first_of_disease = False

            for j, (label, sub_season) in enumerate(seasons.items()):
                fig.add_trace(go.Scatter(
                    x=sub_season["day"], y=sub_season["value"], mode="lines",
                    name=label, legendgroup=label,
                    line=dict(color=PALETTE[j % len(PALETTE)]),
                    showlegend=(i == 0 and (disease is None or disease == diseases[0])),
                    visible=visible,
                ), row=row, col=col)
                trace_disease.append(disease)

    fig.update_xaxes(tickvals=MONTH_TICK_DAYS, ticktext=MONTH_TICK_LABELS, range=[0, 365])
    fig.update_yaxes(title_text="Incidència (per 100.000 hab.)")

    if category == "altres" and len(diseases) > 1:
        buttons = [
            dict(label=disease, method="update", args=[{"visible": [dd == disease for dd in trace_disease]}])
            for disease in diseases
        ]
        fig.update_layout(updatemenus=[dict(active=0, buttons=buttons, x=1, xanchor="right", y=1.12)])

    fig.update_layout(
        title=f"Comparació de temporades — {category}",
        template="plotly_white",
        height=320 * nrows,
        legend_title_text="Temporada",
        margin=dict(t=100),
    )

    return _write(fig, output_path)


# --------------------------------------------------------------------------
# 4. Seasonal grid: multitest incidence + positivity
# --------------------------------------------------------------------------

def build_seasonal_multitest(df, category, output_path):
    d = df.dropna(subset=["data"]).copy()

    if d.empty:
        return None

    age_groups = [a for a in population.get_age_groups() if a in set(d["grup_edat"].astype(str))]
    panels = age_groups + ["Total"]

    diseases = sorted(d["virus"].astype(str).unique()) if category == "altres" else [None]

    ncols = 2 if len(panels) > 1 else 1
    nrows = -(-len(panels) // ncols)
    specs = [[{"secondary_y": True} for _ in range(ncols)] for _ in range(nrows)]

    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=panels, specs=specs)
    trace_disease = []

    for disease in diseases:
        sub_all = d if disease is None else d[d["virus"].astype(str) == disease]
        visible = (disease is None) or (disease == diseases[0])
        first_of_disease = True

        for i, age in enumerate(panels):
            row, col = i // ncols + 1, i % ncols + 1

            if age == "Total":
                g = _totals_across_ages(sub_all)
            else:
                g = (
                    sub_all[sub_all["grup_edat"] == age]
                    .groupby("data")[["incidencia", "positivity"]]
                    .sum(min_count=1)
                )

            prepandemic_inc, seasons_inc = _seasonal_split(g["incidencia"])
            _, seasons_pos = _seasonal_split(g["positivity"])

            if not prepandemic_inc.empty:
                fig.add_trace(go.Scatter(
                    x=prepandemic_inc["day"], y=prepandemic_inc["value"], mode="lines",
                    line=dict(color="grey", dash="dash"), name="Mitjana prepandèmica",
                    legendgroup="prepandemic", showlegend=first_of_disease, visible=visible,
                ), row=row, col=col, secondary_y=False)
                trace_disease.append(disease)
                first_of_disease = False

            for j, (label, sub_season) in enumerate(seasons_inc.items()):
                fig.add_trace(go.Scatter(
                    x=sub_season["day"], y=sub_season["value"], mode="lines",
                    name=label, legendgroup=label,
                    line=dict(color=PALETTE[j % len(PALETTE)]),
                    showlegend=(i == 0 and (disease is None or disease == diseases[0])),
                    visible=visible,
                ), row=row, col=col, secondary_y=False)
                trace_disease.append(disease)

            for j, (label, sub_season) in enumerate(seasons_pos.items()):
                fig.add_trace(go.Scatter(
                    x=sub_season["day"], y=sub_season["value"], mode="lines",
                    name=f"{label} (positivitat)", legendgroup=f"{label}-pos",
                    line=dict(color=PALETTE[j % len(PALETTE)], dash="dot"),
                    showlegend=False,
                    visible=visible,
                ), row=row, col=col, secondary_y=True)
                trace_disease.append(disease)

    fig.update_xaxes(tickvals=MONTH_TICK_DAYS, ticktext=MONTH_TICK_LABELS, range=[0, 365])
    fig.update_yaxes(title_text="Incidència (per 100.000 hab.)", secondary_y=False)
    fig.update_yaxes(title_text="Positivitat (%)", secondary_y=True)

    if category == "altres" and len(diseases) > 1:
        buttons = [
            dict(label=disease, method="update", args=[{"visible": [dd == disease for dd in trace_disease]}])
            for disease in diseases
        ]
        fig.update_layout(updatemenus=[dict(active=0, buttons=buttons, x=1, xanchor="right", y=1.12)])

    fig.update_layout(
        title=f"Comparació de temporades — multitests — {category}",
        template="plotly_white",
        height=340 * nrows,
        legend_title_text="Temporada (línia continua: incidència; punteada: positivitat)",
        margin=dict(t=100),
    )

    return _write(fig, output_path)


# --------------------------------------------------------------------------
# 5. Homepage overview charts
# --------------------------------------------------------------------------

def build_combined_diagnoses(sindromic, output_path):
    d = sindromic.dropna(subset=["data", "incidencia"])
    d = d[d["grup_edat"] == "Total"]

    series_dict = {
        str(diagnostic): sub.groupby("data")["incidencia"].sum()
        for diagnostic, sub in d.groupby("diagnostic", observed=True)
    }

    return build_interactive_lines(
        series_dict,
        title="Tots els diagnòstics — vigilància sindròmica",
        ylabel="Incidència (per 100.000 hab.)",
        output_path=output_path,
    )


def build_combined_viruses(multitests, output_path):
    """
    Multitest data doesn't carry an aggregated "Total" age group (see
    _totals_across_ages), so for this overview chart we sum the
    already-smoothed-per-age incidence across ages per virus as a
    reasonable approximation, rather than recomputing a population-
    weighted total per virus.
    """
    d = multitests.dropna(subset=["data", "incidencia"])

    series_dict = {
        str(virus): sub.groupby("data")["incidencia"].sum()
        for virus, sub in d.groupby("virus", observed=True)
    }

    return build_interactive_lines(
        series_dict,
        title="Tots els virus — multitests",
        ylabel="Incidència de proves positives (per 100.000 hab.)",
        output_path=output_path,
    )
