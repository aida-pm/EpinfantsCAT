#!/usr/bin/env python3
"""
generate_site_plots.py

Loads both datasets, computes national incidence rates (per 100,000
inhabitants, using the Catalonia 2026 population reference in
population.py), and generates ONE plot per virus (microbiologica) and ONE
plot per syndromic diagnosis (sindromica) — automatically, based on
whatever distinct values show up in the data, no manual list to maintain.

Each figure is written as:
  - PNG image   -> assets/images/plots/<slug>.png
  - Jekyll page -> _plots/<slug>.md

Run any time you refresh your local data:

    python scripts/generate_site_plots.py

Then commit + push assets/images/plots/ and _plots/ via GitHub Desktop.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_data import load_dataset, FILENAMES  # noqa: E402
import plots  # noqa: E402
import population  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images", "plots")
PLOTS_COLLECTION_DIR = os.path.join(REPO_ROOT, "_plots")

COLORS = list(plots.PALETTE.values())


def generate_virus_plots(df):
    """One national incidence plot per distinct value of 'virus', from the
    microbiologica dataset. Denominator: total Catalan population (both
    sexes, all ages) — a crude national incidence, not age-adjusted."""
    results = []
    viruses = sorted(v for v in df["virus"].dropna().unique().tolist())

    for i, virus in enumerate(viruses):
        subset = df[df["virus"] == virus]
        incidence = population.compute_national_incidence(
            subset, date_col="data_inici", count_col="positiu"
        )
        if incidence.empty:
            continue

        title = f"{virus} — vigilància microbiològica"
        meta = plots.plot_series(
            incidence,
            title=title,
            ylabel="Casos positius per 100.000 hab.",
            color=COLORS[i % len(COLORS)],
            description=(
                f"Evolució setmanal de casos positius de {virus} a Catalunya, "
                f"per 100.000 habitants (font: vigilància microbiològica "
                f"sentinella a Atenció Primària; població de referència: "
                f"cens de Catalunya, gener 2026)."
            ),
            images_dir=IMAGES_DIR,
            slug=f"virus-{plots.slugify(virus)}",
        )
        results.append(meta)
        print(f"  [{virus}] {len(subset)} rows -> {meta['filename']}")

    return results


def generate_diagnostic_plots(df):
    """One national incidence plot per distinct value of 'diagnostic', from
    the sindromica dataset. Same national-crude-rate approach as above."""
    results = []
    diagnostics = sorted(d for d in df["diagnostic"].dropna().unique().tolist())

    for i, diagnostic in enumerate(diagnostics):
        subset = df[df["diagnostic"] == diagnostic]
        incidence = population.compute_national_incidence(
            subset, date_col="data", count_col="casos"
        )
        if incidence.empty:
            continue

        title = f"{diagnostic} — vigilància sindròmica"
        meta = plots.plot_series(
            incidence,
            title=title,
            ylabel="Casos per 100.000 hab.",
            color=COLORS[i % len(COLORS)],
            description=(
                f"Evolució setmanal de casos de {diagnostic} a Catalunya, "
                f"per 100.000 habitants (font: vigilància sindròmica "
                f"d'infeccions a Atenció Primària; població de referència: "
                f"cens de Catalunya, gener 2026)."
            ),
            images_dir=IMAGES_DIR,
            slug=f"diagnostic-{plots.slugify(diagnostic)}",
        )
        results.append(meta)
        print(f"  [{diagnostic}] {len(subset)} rows -> {meta['filename']}")

    return results


def write_jekyll_page(meta):
    os.makedirs(PLOTS_COLLECTION_DIR, exist_ok=True)
    path = os.path.join(PLOTS_COLLECTION_DIR, f"{meta['slug']}.md")
    today = datetime.now().strftime("%Y-%m-%d")

    # Escape any stray double-quotes in title/description so the YAML
    # front matter doesn't break.
    safe_title = meta["title"].replace('"', "'")
    safe_desc = meta["description"].replace('"', "'")

    front_matter = (
        "---\n"
        "layout: plot\n"
        f"title: \"{safe_title}\"\n"
        f"image: /assets/images/plots/{meta['filename']}\n"
        f"date: {today}\n"
        f"description: \"{safe_desc}\"\n"
        "---\n\n"
        f"{safe_desc}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(front_matter)

    print(f"  wrote page: {path}")


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

    all_plot_meta = []

    if "microbiologica" in dataframes:
        print("\nGenerating one plot per virus (microbiologica)...")
        all_plot_meta.extend(generate_virus_plots(dataframes["microbiologica"]))

    if "sindromica" in dataframes:
        print("\nGenerating one plot per diagnosis (sindromica)...")
        all_plot_meta.extend(generate_diagnostic_plots(dataframes["sindromica"]))

    print(f"\nGenerated {len(all_plot_meta)} figures. Writing Jekyll pages...")
    for meta in all_plot_meta:
        write_jekyll_page(meta)

    print("\nDone. Now:")
    print("  1. git add assets/images/plots _plots")
    print("  2. commit + push via GitHub Desktop")
    print("  3. make sure _config.yml declares the 'plots' collection")


if __name__ == "__main__":
    main()
