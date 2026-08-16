#!/usr/bin/env python3
"""
generate_site_plots.py

Loads both datasets, computes national incidence (per 100,000 inhabitants)
for every virus and every syndromic diagnosis, applies a 7-period moving
average (matching the original notebooks' methodology), and builds:

  1. THREE combined static PNGs — one per category (Grip / VRS / Altres),
     each showing every relevant line (virus + diagnostic) together on a
     single chart:
         assets/images/plots/grip-combined.png
         assets/images/plots/vrs-combined.png
         assets/images/plots/altres-combined.png
     These are what grip.md / vrs.md / altres.md display, and (via their
     `image:` front matter) what shows up as the homepage tile thumbnail.

  2. TWO combined interactive charts — all viruses in one, all diagnoses
     in one, with a toggleable legend:
         assets/interactive/tots-microbiologics.html
         assets/interactive/tots-sindromes.html
     These are embedded on the homepage (index.md) under "Massa libero".

This REPLACES the old one-PNG-per-virus/per-diagnostic approach and the
_plots collection — everything is now consolidated into these 5 outputs.

Run any time you refresh your local data:

    python scripts/generate_site_plots.py

Then commit + push assets/ via GitHub Desktop (data/ stays local).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_data import load_dataset, FILENAMES  # noqa: E402
import plots  # noqa: E402
import population  # noqa: E402
import interactive  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images", "plots")
INTERACTIVE_DIR = os.path.join(REPO_ROOT, "assets", "interactive")

SMOOTH_YLABEL_SUFFIX = " (mitjana mòbil 7 dies)"


def categorize(name: str) -> str:
    """Groups a virus/diagnostic name into one of three site categories."""
    n = name.lower()
    if "grip" in n:
        return "grip"
    if n == "vrs" or "vrs" in n:
        return "vrs"
    return "altres"


def build_series_for_dataset(df, date_col, count_col, group_col):
    """Returns {name: 7-day-smoothed incidence Series} for every distinct
    value in group_col (e.g. every virus, or every diagnostic). Groups
    directly by the real date_col values (daily), no interpolation."""
    result = {}
    for value in sorted(df[group_col].dropna().unique().tolist()):
        subset = df[df[group_col] == value]
        s = population.compute_national_incidence(subset, date_col=date_col, count_col=count_col)
        if not s.empty:
            result[value] = population.rolling_average(s, window=7, center=True, min_periods=1)
    return result


def build_category_static_plots(virus_series, diagnostic_series):
    """Builds ONE combined static PNG per category (grip/vrs/altres),
    mixing both sources when relevant (e.g. Grip's virus-detection line
    together with Grip's syndromic-diagnosis line)."""
    combined = {"grip": {}, "vrs": {}, "altres": {}}

    for name, s in virus_series.items():
        combined[categorize(name)][f"{name} (microbiològica)"] = s
    for name, s in diagnostic_series.items():
        combined[categorize(name)][f"{name} (sindròmica)"] = s

    titles = {
        "grip": "Grip",
        "vrs": "VRS",
        "altres": "Altres virus i síndromes",
    }
    results = {}

    for cat, series_dict in combined.items():
        if not series_dict:
            print(f"  [{cat}] no data available, skipping.")
            continue

        title = titles[cat]
        meta = plots.plot_combined_series(
            series_dict,
            title=title,
            ylabel="Casos / positius per 100.000 hab." + SMOOTH_YLABEL_SUFFIX,
            description=(
                f"Evolució combinada (mitjana mòbil ~7 setmanes) de totes les "
                f"figures de la categoria {title}, combinant vigilància "
                f"sindròmica i microbiològica quan escau."
            ),
            images_dir=IMAGES_DIR,
            slug=f"{cat}-combined",
        )
        results[cat] = meta
        print(f"  [{cat}] {len(series_dict)} línies -> {meta['filename']}")

    return results


def build_seasonal_plots(virus_series, diagnostic_series):
    """Season-over-season overlay charts (Sept-Aug), for the signals where
    this comparison is most meaningful: Grip and VRS. Each season gets its
    own colored line on a shared "day of season" x-axis, in addition to
    (not replacing) the full-timeline combined charts built above."""
    targets = []
    if "Grip" in virus_series:
        targets.append(("grip-virus-seasonal", "Grip — vigilància microbiològica, per temporada", virus_series["Grip"]))
    if "Grip" in diagnostic_series:
        targets.append(("grip-diagnostic-seasonal", "Grip — vigilància sindròmica, per temporada", diagnostic_series["Grip"]))
    if "VRS" in virus_series:
        targets.append(("vrs-virus-seasonal", "VRS — vigilància microbiològica, per temporada", virus_series["VRS"]))

    results = {}
    for slug, title, series in targets:
        meta = plots.plot_seasonal_overlay(
            series,
            title=title,
            ylabel="Incidència per 100.000 hab." + SMOOTH_YLABEL_SUFFIX,
            description=f"Comparació de temporades (setembre-agost) per a {title}.",
            images_dir=IMAGES_DIR,
            slug=slug,
        )
        if meta:
            results[slug] = meta
            print(f"  [seasonal] {meta['filename']}")
    return results


def build_interactive_overview(virus_series, diagnostic_series):
    if virus_series:
        interactive.build_interactive_lines(
            virus_series,
            title="Tots els virus — vigilància microbiològica",
            ylabel="Casos positius per 100.000 hab." + SMOOTH_YLABEL_SUFFIX,
            output_path=os.path.join(INTERACTIVE_DIR, "tots-microbiologics.html"),
        )
    if diagnostic_series:
        interactive.build_interactive_lines(
            diagnostic_series,
            title="Totes les síndromes — vigilància sindròmica",
            ylabel="Casos per 100.000 hab." + SMOOTH_YLABEL_SUFFIX,
            output_path=os.path.join(INTERACTIVE_DIR, "tots-sindromes.html"),
        )


def main():
    dataframes = {}
    for name, filename in FILENAMES.items():
        try:
            dataframes[name] = load_dataset(name, filename)
        except FileNotFoundError as e:
            print(f"WARNING: {e}", file=sys.stderr)

    if not dataframes:
        print("No datasets loaded — check data/ folder and FILENAMES in load_data.py.", file=sys.stderr)
        sys.exit(1)

    virus_series = {}
    diagnostic_series = {}

    if "microbiologica" in dataframes:
        print("Computing smoothed incidence per virus (microbiologica)...")
        virus_series = build_series_for_dataset(
            dataframes["microbiologica"], date_col="data_inici",
            count_col="positiu", group_col="virus",
        )

    if "sindromica" in dataframes:
        print("Computing smoothed incidence per diagnosis (sindromica)...")
        diagnostic_series = build_series_for_dataset(
            dataframes["sindromica"], date_col="data",
            count_col="casos", group_col="diagnostic",
        )

    print("\nBuilding category combined static plots (grip/vrs/altres)...")
    build_category_static_plots(virus_series, diagnostic_series)

    print("\nBuilding season-over-season overlay plots (grip/vrs)...")
    build_seasonal_plots(virus_series, diagnostic_series)

    print("\nBuilding combined interactive overview charts...")
    build_interactive_overview(virus_series, diagnostic_series)

    print("\nDone. Now:")
    print("  1. git add assets/")
    print("  2. commit + push via GitHub Desktop")


if __name__ == "__main__":
    main()
