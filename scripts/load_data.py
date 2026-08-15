#!/usr/bin/env python3

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

TODAY = datetime.now().strftime("%Y%m%d")

FILENAMES = {
    "sindromica": f"sindromica_{TODAY}.csv",       # Vigilància sindròmica d'infeccions a Atenció Primària
    "microbiologica": f"microbiologica_{TODAY}.csv",  # Vigilància microbiològica sentinella a Atenció Primària
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
FIG_DIR = os.path.join(REPO_ROOT, "figures")

def load_dataset(name: str, filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[{name}] Couldn't find '{path}'. "
            f"Check the file is in data/ and that FILENAMES['{name}'] "
            f"matches the exact filename (including extension)."
        )

    try:
        df = pd.read_csv(path, encoding="UTF-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin1", sep=",")

    if df.shape[1] == 1:
        df = pd.read_csv(path, sep=";", encoding="UTF-8")

    print(f"[{name}] loaded {len(df)} rows, {len(df.columns)} columns from {filename}")
    return df


def explore_and_plot(df: pd.DataFrame, name: str):
    """Generic exploratory plots: works even without knowing exact column
    names in advance, by auto-detecting date-like and numeric columns."""
    os.makedirs(FIG_DIR, exist_ok=True)

    print(f"\n[{name}] columns: {list(df.columns)}")
    print(df.head())
    print(df.dtypes)

    # --- try to find a date column ---
    date_col = None
    for col in df.columns:
        lower = col.lower()
        if "data" in lower or "date" in lower:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > 0:
                    df[col] = parsed
                    date_col = col
                    break
            except Exception:
                continue

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

    # --- Plot 2: top categories for the first text/categorical column ---
    cat_cols = df.select_dtypes(include="object").columns.tolist()
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