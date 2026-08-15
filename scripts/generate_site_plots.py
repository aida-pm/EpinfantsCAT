#!/usr/bin/env python3
"""
generate_site_plots.py

Loads the local CSVs (via load_data.py's loader), generates figures using
the reusable functions in plots.py, and writes them straight into the
Jekyll site as:

  - PNG images   -> assets/images/plots/<slug>.png
  - Jekyll pages -> _plots/<slug>.md   (one page per figure, with front matter)

Jekyll then renders each figure as its own page (via the `plot` layout),
and the homepage gallery lists them all as clickable thumbnails.

Run this any time you refresh your local data and want the site's figures
updated:

    python scripts/generate_site_plots.py

Then commit + push the changed files in assets/images/plots/ and _plots/
(and any local data/ changes if you're tracking those) via GitHub Desktop.
"""

import os
import sys
from datetime import datetime

# Make sure we can import the sibling modules regardless of the working
# directory this script is run from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_data import load_dataset, FILENAMES  # noqa: E402
import plots  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images", "plots")
PLOTS_COLLECTION_DIR = os.path.join(REPO_ROOT, "_plots")

# --------------------------------------------------------------------------
# AUTO MODE: with no knowledge of exact column names, this detects a date
# column and the numeric columns in each dataset and makes a generic
# timeseries + a bar chart of the top categorical values.
#
# Once you know the real column names (run scripts/load_data.py once and
# check the printed df.dtypes), switch AUTO_MODE to False and fill in
# CUSTOM_PLOTS below for full control — titles, labels, colors, dual-axis
# comparisons, multi-series comparisons, etc.
# --------------------------------------------------------------------------
AUTO_MODE = True


def detect_date_column(df):
    for col in df.columns:
        lower = col.lower()
        if "data" in lower or "date" in lower:
            import pandas as pd
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() > 0:
                df[col] = parsed
                return col
    return None


def auto_generate_plots(df, dataset_name):
    results = []
    date_col = detect_date_column(df)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()

    if date_col and numeric_cols:
        for num_col in numeric_cols[:3]:
            title = f"{dataset_name.capitalize()}: {num_col} over time"
            meta = plots.plot_timeseries(
                df, date_col, num_col, title=title, ylabel=num_col,
                description=f"Daily/weekly trend of '{num_col}' from the {dataset_name} dataset.",
                images_dir=IMAGES_DIR,
            )
            results.append(meta)

    if cat_cols:
        cat_col = cat_cols[0]
        title = f"{dataset_name.capitalize()}: top values of {cat_col}"
        meta = plots.plot_top_categories(
            df, cat_col, title=title,
            description=f"Most frequent values of '{cat_col}' in the {dataset_name} dataset.",
            images_dir=IMAGES_DIR,
        )
        results.append(meta)

    return results


# --------------------------------------------------------------------------
# CUSTOM_PLOTS: once you know your real column names, write specific plot
# calls here instead of relying on auto-detection. Example (edit/uncomment
# once you know actual column names from df.dtypes):
#
# def custom_generate_plots(dataframes):
#     results = []
#     df = dataframes["sindromica"]
#     results.append(plots.plot_dual_axis_timeseries(
#         df, date_col="data",
#         col1="Bronquiolitis (<5 a.)", label1="Bronchiolitis",
#         col2="COVID-19 (tothom)", label2="COVID-19",
#         title="Bronchiolitis vs COVID-19",
#         description="Weekly incidence comparison between bronchiolitis and COVID-19.",
#         images_dir=IMAGES_DIR,
#     ))
#     results.append(plots.plot_multi_series(
#         df, date_col="data",
#         value_cols=["Grip (0 a.)", "Grip (1-2 a.)", "Grip (3-4 a.)"],
#         labels=["0 years", "1-2 years", "3-4 years"],
#         title="Influenza incidence by age group",
#         ylabel="Cases per 100,000 inh.",
#         description="Comparing influenza incidence across pediatric age groups.",
#         images_dir=IMAGES_DIR,
#     ))
#     return results
# --------------------------------------------------------------------------


def write_jekyll_page(meta):
    os.makedirs(PLOTS_COLLECTION_DIR, exist_ok=True)
    path = os.path.join(PLOTS_COLLECTION_DIR, f"{meta['slug']}.md")
    today = datetime.now().strftime("%Y-%m-%d")

    front_matter = (
        "---\n"
        "layout: plot\n"
        f"title: \"{meta['title']}\"\n"
        f"image: /assets/images/plots/{meta['filename']}\n"
        f"date: {today}\n"
        f"description: \"{meta['description']}\"\n"
        "---\n\n"
        f"{meta['description']}\n"
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

    if AUTO_MODE:
        for name, df in dataframes.items():
            print(f"\n[{name}] generating auto plots...")
            all_plot_meta.extend(auto_generate_plots(df, name))
    else:
        # Uncomment custom_generate_plots above and use it here instead.
        raise NotImplementedError(
            "Set AUTO_MODE = True, or implement + call custom_generate_plots(dataframes)."
        )

    print(f"\nGenerated {len(all_plot_meta)} figures. Writing Jekyll pages...")
    for meta in all_plot_meta:
        write_jekyll_page(meta)

    print("\nDone. Now:")
    print("  1. git add assets/images/plots _plots")
    print("  2. commit + push via GitHub Desktop")
    print("  3. make sure _config.yml declares the 'plots' collection (see instructions)")


if __name__ == "__main__":
    main()
