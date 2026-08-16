#!/usr/bin/env python3
"""
load_data.py

Loads the manually-downloaded Catalunya open-data CSVs from data/ into
pandas DataFrames with the correct dtype for each column (dates as
datetime, identifiers as category/string, counts as nullable Int64),
instead of leaving everything as generic strings/objects.

Usage:
    python scripts/load_data.py
    # or, if made executable:
    ./scripts/load_data.py

Setup:
    1. Download the CSVs manually from:
       - https://analisi.transparenciacatalunya.cat/Salut/Vigil-ncia-sindr-mica-d-infeccions-a-Atenci-Prim-r/fa7i-d8gc/about_data
       - https://analisi.transparenciacatalunya.cat/Salut/Vigil-ncia-microbiol-gica-sentinella-a-Atenci-Prim/f5wm-z2ut/about_data
    2. Place them in the data/ folder at the repo root.
    3. Update FILENAMES below if your downloaded filenames differ.
"""

import os
import sys
import glob
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

TODAY = datetime.now().strftime("%Y%m%d")

FILENAMES = {
    "sindromica": f"sindromica_{TODAY}.csv",          # Vigilància sindròmica d'infeccions a Atenció Primària
    "microbiologica": f"microbiologica_{TODAY}.csv",  # Vigilància microbiològica sentinella a Atenció Primària
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
FIG_DIR = os.path.join(REPO_ROOT, "figures")

# --------------------------------------------------------------------------
# Per-dataset dtype specification.
#
# "microbiologica" is filled in based on the real file structure (weekly
# counts of positive virus detections, by region/sex/age group/socioeconomic
# index). "sindromica" is left empty for now — once you share that file's
# columns, I'll fill this in the same way.
#
#   category      -> repeated text labels (region names, virus, sex, age group...)
#   string        -> free identifiers you don't want to do math on (codes)
#   Int64         -> whole numbers that could contain missing values (nullable)
#   dates         -> parsed separately below via `dates` + `date_format`
# --------------------------------------------------------------------------
DTYPE_SPECS = {
    "microbiologica": {
        "dtype": {
            "setmana_epidemiologica": "Int64",   # epidemiological week number (1-52)
            "any": "Int64",                       # year
            "codi_regio": "string",               # region code
            "nom_regio": "category",              # region name
            "codi_ambit": "string",                # area code (mirrors codi_regio)
            "nom_ambit": "category",               # area name (mirrors nom_regio)
            "virus": "category",                  # VRS, Grip, SARS-CoV-2, Rinovirus, ...
            "sexe": "category",                   # Home / Dona / No disponible
            "grup_edat": "category",              # age group, e.g. "5 a 9", "80 o més"
            "index_socioeconomic": "category",    # socioeconomic index (ordinal-ish, incl. -1 = not available)
            "positiu": "Int64",                   # count of positive detections
        },
        "dates": ["data_inici", "data_final"],
        "date_format": "%d/%m/%Y",
    },
    "sindromica": {
        "dtype": {
            "setmana_epidemiologica": "Int64",    # epidemiological week number (1-52)
            "any": "Int64",                        # year
            "codi_regio": "string",                # region code
            "nom_regio": "category",               # region name
            "codi_ambit": "string",                 # area code (mirrors codi_regio)
            "nom_ambit": "category",                # area name (mirrors nom_regio)
            "codi_abs": "string",                   # basic health area (ABS) code
            "nom_abs": "category",                  # basic health area (ABS) name
            "diagnostic": "category",               # syndrome/diagnosis (e.g. bronchiolitis, flu-like...)
            "sexe": "category",                     # Home / Dona / No disponible
            "grup_edat": "category",                # age group
            "index_socioeconomic": "category",      # socioeconomic index (incl. -1 = not available)
            "casos": "Int64",                       # case count
            "poblacio": "Int64",                    # population denominator for that group/week
        },
        "dates": ["data"],
        "date_format": "%d/%m/%Y",  # same portal as microbiologica; adjust if parsing looks wrong
    },
}


def find_latest_matching_file(name: str, filename: str) -> str:
    """If the exact dated filename doesn't exist, look in DATA_DIR for
    other files matching '{name}_YYYYMMDD.csv' and return the path of the
    most recent one by date. Returns None if nothing matches at all."""
    prefix = filename.rsplit("_", 1)[0]  # e.g. "sindromica" from "sindromica_20260816.csv"
    pattern = os.path.join(DATA_DIR, f"{prefix}_*.csv")
    candidates = glob.glob(pattern)

    dated = []
    for path in candidates:
        m = re.search(r"_(\d{8})\.csv$", os.path.basename(path))
        if m:
            try:
                date = datetime.strptime(m.group(1), "%Y%m%d")
                dated.append((date, path))
            except ValueError:
                continue

    if not dated:
        return None

    dated.sort(key=lambda t: t[0])
    latest_date, latest_path = dated[-1]
    print(f"[{name}] No file dated today — using most recent available: "
          f"{os.path.basename(latest_path)} ({latest_date.strftime('%d/%m/%Y')})")
    return latest_path


def load_dataset(name: str, filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        fallback_path = find_latest_matching_file(name, filename)
        if fallback_path is None:
            raise FileNotFoundError(
                f"[{name}] Couldn't find '{path}', and no other "
                f"'{name}_YYYYMMDD.csv' files were found in {DATA_DIR} either. "
                f"Check the file is actually in data/."
            )
        path = fallback_path

    try:
        df = pd.read_csv(path, encoding="UTF-8", dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin1", sep=",", dtype=str)

    if df.shape[1] == 1:
        df = pd.read_csv(path, sep=";", encoding="UTF-8", dtype=str)

    df = apply_dtypes(df, name)

    print(f"[{name}] loaded {len(df)} rows, {len(df.columns)} columns from {os.path.basename(path)}")
    return df


def parse_date_column(series: pd.Series, date_format: str = None) -> pd.Series:
    """Parse a date column, falling back to pandas' own inference if the
    given format doesn't match most of the values. This guards against a
    wrong date_format guess in DTYPE_SPECS silently producing all-NaT."""
    original_notna = series.notna().sum()
    if original_notna == 0:
        return pd.to_datetime(series, errors="coerce")

    parsed = pd.to_datetime(series, format=date_format, errors="coerce") if date_format \
        else pd.to_datetime(series, errors="coerce", dayfirst=True)

    success_rate = parsed.notna().sum() / original_notna
    if success_rate < 0.9 and date_format:
        fallback = pd.to_datetime(series, errors="coerce", dayfirst=True)
        if fallback.notna().sum() > parsed.notna().sum():
            print(f"  NOTE: date_format '{date_format}' only matched "
                  f"{success_rate:.0%} of values — used automatic parsing instead.")
            return fallback

    return parsed


def apply_dtypes(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Cast each column to its proper dtype based on DTYPE_SPECS. Falls back
    to leaving columns untouched (as strings) if no spec exists yet for
    this dataset — better to be inspectable than to silently guess wrong."""
    spec = DTYPE_SPECS.get(name)
    if not spec:
        print(f"[{name}] No dtype spec defined yet — columns kept as text. "
              f"Share the column list and we can add one.")
        return df

    for col, dtype in spec.get("dtype", {}).items():
        if col not in df.columns:
            print(f"[{name}] WARNING: expected column '{col}' not found in file.")
            continue
        try:
            df[col] = df[col].astype(dtype)
        except Exception as e:
            print(f"[{name}] WARNING: couldn't cast '{col}' to {dtype}: {e}")

    date_format = spec.get("date_format")
    for date_col in spec.get("dates", []):
        if date_col not in df.columns:
            print(f"[{name}] WARNING: expected date column '{date_col}' not found in file.")
            continue
        df[date_col] = parse_date_column(df[date_col], date_format)

    return df


def explore_and_plot(df: pd.DataFrame, name: str):
    """Generic exploratory plots: works even without a dtype spec, by
    auto-detecting date-like and numeric columns."""
    os.makedirs(FIG_DIR, exist_ok=True)

    print(f"\n[{name}] columns: {list(df.columns)}")
    print(df.head())
    print(df.dtypes)

    # --- find a date column: prefer already-parsed datetime columns first ---
    date_col = None
    datetime_cols = df.select_dtypes(include="datetime").columns.tolist()
    if datetime_cols:
        date_col = datetime_cols[0]
    else:
        for col in df.columns:
            lower = col.lower()
            if "data" in lower or "date" in lower:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > 0:
                    df[col] = parsed
                    date_col = col
                    break

    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # --- Plot 1: time series of numeric columns, if a date column exists ---
    if date_col and numeric_cols:
        for num_col in numeric_cols[:3]:  # limit to first 3 to avoid clutter
            fig, ax = plt.subplots(figsize=(10, 5))
            grouped = df.groupby(date_col)[num_col].sum(numeric_only=True)
            grouped.plot(ax=ax)
            ax.set_title(f"{name}: {num_col} over time")
            ax.set_xlabel(date_col)
            ax.set_ylabel(num_col)
            fig.tight_layout()
            out_path = os.path.join(FIG_DIR, f"{name}_{num_col}_timeseries.png")
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            print(f"[{name}] saved plot: {out_path}")

    # --- Plot 2: top categories for the first category/text column ---
    cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    if cat_cols:
        cat_col = cat_cols[0]
        fig, ax = plt.subplots(figsize=(10, 5))
        df[cat_col].value_counts().head(15).plot(kind="bar", ax=ax)
        ax.set_title(f"{name}: top values of {cat_col}")
        fig.tight_layout()
        out_path = os.path.join(FIG_DIR, f"{name}_{cat_col}_top_values.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"[{name}] saved plot: {out_path}")

    if not date_col and not numeric_cols:
        print(f"[{name}] No date or numeric columns auto-detected — "
              f"inspect the CSV manually to write custom plots.")


def main():
    dataframes = {}

    for name, filename in FILENAMES.items():
        try:
            df = load_dataset(name, filename)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            continue

        dataframes[name] = df
        explore_and_plot(df, name)

    print("\nDone. Check the figures/ folder for plots.")
    print("DataFrames are available as: " + ", ".join(dataframes.keys()))
    return dataframes


if __name__ == "__main__":
    dfs = main()
    # If running interactively (e.g. `python -i scripts/load_data.py`),
    # you can now access dfs["sindromica"] and dfs["microbiologica"]
    # directly in the console for further manipulation.
