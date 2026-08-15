#!/usr/bin/env python3
"""
generate_site_plots.py

Loads both datasets (sindromica + microbiologica), computes national
incidence rates (per 100,000 inhabitants, using the Catalonia 2026
population reference in population.py), and generates:

  1. One static PNG + Jekyll page per virus (microbiologica) and per
     syndromic diagnosis (sindromica) — tagged with a `category` front
     matter field (grip / vrs / altres) so they can be grouped on the
     Grip / VRS / Altres pages.

  2. Two interactive combined charts (all diagnoses in one, all viruses
     in one, toggleable via legend) written to assets/interactive/, meant
     to be embedded on the homepage.

Run any time you refresh your local data:

    python scripts/generate_site_plots.py

Then commit + push assets/, _plots/ via GitHub Desktop (data/ stays local,
per .gitignore).
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_data import load_dataset, FILENAMES  # noqa: E402
import plots  # noqa: E402
import population  # noqa: E402
import interactive  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images", "plots")
INTERACTIVE_DIR = os.path.join(REPO_ROOT, "assets", "interactive")
PLOTS_COLLECTION_DIR = os.path.join(REPO_ROOT, "_plots")

COLORS = list(plots.PALETTE.values())


def categorize(name: str) -> str:
    """Groups a virus/diagnostic name into one of three site categories."""
    n = name.lower()
    if "grip" in n:
        return "grip"
    if n == "vrs" or "vrs" in n:
        return "vrs"
    return "altres"


def generate_virus_plots(df):
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
        meta["category"] = categorize(virus)
        meta["source"] = "microbiologica"
        results.append(meta)
        print(f"  [{virus}] {len(subset)} rows -> {meta['filename']} (category: {meta['category']})")

    return results


def generate_diagnostic_plots(df):
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
        meta["category"] = categorize(diagnostic)
        meta["source"] = "sindromica"
        results.append(meta)
        print(f"  [{diagnostic}] {len(subset)} rows -> {meta['filename']} (category: {meta['category']})")

    return results


def generate_interactive_overview(dataframes):
    if "microbiologica" in dataframes:
        df = dataframes["microbiologica"]
        series_dict = {}
        for virus in sorted(df["virus"].dropna().unique()):
            s = population.compute_national_incidence(
                df[df["virus"] == virus], date_col="data_inici", count_col="positiu"
            )
            if not s.empty:
                series_dict[virus] = s
        interactive.build_interactive_lines(
            series_dict,
            title="Tots els virus — vigilància microbiològica",
            ylabel="Casos positius per 100.000 hab.",
            output_path=os.path.join(INTERACTIVE_DIR, "tots-microbiologics.html"),
        )

    if "sindromica" in dataframes:
        df = dataframes["sindromica"]
        series_dict = {}
        for diagnostic in sorted(df["diagnostic"].dropna().unique()):
            s = population.compute_national_incidence(
                df[df["diagnostic"] == diagnostic], date_col="data", count_col="casos"
            )
            if not s.empty:
                series_dict[diagnostic] = s
        interactive.build_interactive_lines(
            series_dict,
            title="Totes les síndromes — vigilància sindròmica",
            ylabel="Casos per 100.000 hab.",
            output_path=os.path.join(INTERACTIVE_DIR, "tots-sindromes.html"),
        )


def write_jekyll_page(meta):
    os.makedirs(PLOTS_COLLECTION_DIR, exist_ok=True)
    path = os.path.join(PLOTS_COLLECTION_DIR, f"{meta['slug']}.md")
    today = datetime.now().strftime("%Y-%m-%d")

    safe_title = meta["title"].replace('"', "'")
    safe_desc = meta["description"].replace('"', "'")

    front_matter = (
        "---\n"
        "layout: plot\n"
        f"title: \"{safe_title}\"\n"
        f"image: /assets/images/plots/{meta['filename']}\n"
        f"date: {today}\n"
        f"category: {meta.get('category', 'altres')}\n"
        f"source: {meta.get('source', '')}\n"
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

    print(f"\nGenerated {len(all_plot_meta)} static figures. Writing Jekyll pages...")
    for meta in all_plot_meta:
        write_jekyll_page(meta)

    print("\nGenerating combined interactive charts...")
    generate_interactive_overview(dataframes)

    print("\nDone. Now:")
    print("  1. git add assets/ _plots/")
    print("  2. commit + push via GitHub Desktop")


if __name__ == "__main__":
    main()
