#!/usr/bin/env python3
#!/usr/bin/env python3
"""
load_data.py

Loads the three manually-downloaded Catalunya open-data CSVs:

    sindromica
    multitests_positius
    multitests_tests

The datasets are returned as pandas DataFrames with dates and counts
converted to appropriate dtypes.

The production plotting pipeline should import:

    load_dataset()
    FILENAMES

from this module.

The exploratory plotting functionality from the old version has deliberately
been removed from the normal loading process. Site generation should not
create miscellaneous static plots in figures/.
"""

import glob
import os
import re
from datetime import datetime

import pandas as pd
import population


TODAY = datetime.now().strftime("%Y%m%d")

FILENAMES = {
    "sindromica": f"sindromica_{TODAY}.csv",
    "multitests_tests": f"multitests_test_{TODAY}.csv",
    "multitests_positius": f"multitests_pos_{TODAY}.csv",
}


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")


DTYPE_SPECS = {
    "sindromica": {
        "dtype": {
            "setmana_epidemiologica": "Int64",
            "any": "Int64",
            "codi_regio": "string",
            "nom_regio": "category",
            "codi_ambit": "string",
            "nom_ambit": "category",
            "codi_abs": "string",
            "nom_abs": "category",
            "diagnostic": "category",
            "sexe": "category",
            "grup_edat": "category",
            "index_socioeconomic": "category",
            "casos": "Int64",
            "poblacio": "Int64",
        },
        "dates": ["data"],
        "date_format": "%d/%m/%Y",
    },

    "multitests_tests": {
        "dtype": {
            "setmana_epidemiologica": "Int64",
            "any": "Int64",
            "codi_regio": "string",
            "nom_regio": "category",
            "codi_ambit": "string",
            "nom_ambit": "category",
            "sexe": "category",
            "grup_edat": "category",
            "index_socioeconomic": "category",
            "total": "Int64",
            "positiu": "Int64",
        },
        "dates": ["data_inici", "data_final"],
        "date_format": "%d/%m/%Y",
    },

    "multitests_positius": {
        "dtype": {
            "setmana_epidemiologica": "Int64",
            "any": "Int64",
            "codi_regio": "string",
            "nom_regio": "category",
            "codi_ambit": "string",
            "nom_ambit": "category",
            "virus": "category",
            "sexe": "category",
            "grup_edat": "category",
            "index_socioeconomic": "category",
            "positiu": "Int64",
        },
        "dates": ["data_inici", "data_final"],
        "date_format": "%d/%m/%Y",
    },
}


def find_latest_matching_file(name: str, filename: str):
    """
    If today's exact filename does not exist, find the most recent
    name_YYYYMMDD.csv file.
    """
    prefix = filename.rsplit("_", 1)[0]
    pattern = os.path.join(DATA_DIR, f"{prefix}_*.csv")

    candidates = glob.glob(pattern)

    dated = []

    for path in candidates:
        match = re.search(
            r"_(\d{8})\.csv$",
            os.path.basename(path),
        )

        if not match:
            continue

        try:
            date = datetime.strptime(match.group(1), "%Y%m%d")
        except ValueError:
            continue

        dated.append((date, path))

    if not dated:
        return None

    dated.sort(key=lambda item: item[0])

    latest_date, latest_path = dated[-1]

    print(
        f"[{name}] No file dated today. "
        f"Using {os.path.basename(latest_path)} "
        f"({latest_date.strftime('%d/%m/%Y')})."
    )

    return latest_path


def parse_date_column(series: pd.Series, date_format: str = None):
    """
    Parse dates robustly.

    First tries the declared format. If fewer than 90% of values match,
    falls back to pandas day-first parsing.
    """
    original_notna = series.notna().sum()

    if original_notna == 0:
        return pd.to_datetime(series, errors="coerce")

    if date_format:
        parsed = pd.to_datetime(
            series,
            format=date_format,
            errors="coerce",
        )
    else:
        parsed = pd.to_datetime(
            series,
            errors="coerce",
            dayfirst=True,
        )

    success_rate = parsed.notna().sum() / original_notna

    if success_rate < 0.90 and date_format:
        fallback = pd.to_datetime(
            series,
            errors="coerce",
            dayfirst=True,
        )

        if fallback.notna().sum() > parsed.notna().sum():
            print(
                f"  NOTE: date format {date_format!r} matched only "
                f"{success_rate:.0%}; using automatic parsing."
            )
            return fallback

    return parsed


def apply_dtypes(df: pd.DataFrame, name: str):
    """
    Apply the dtype specification for a dataset.

    Missing expected columns produce warnings rather than silently
    crashing the loader.
    """
    spec = DTYPE_SPECS.get(name)

    if spec is None:
        print(
            f"[{name}] No dtype specification exists. "
            "Columns remain as loaded."
        )
        return df

    for col, dtype in spec.get("dtype", {}).items():
        if col not in df.columns:
            print(
                f"[{name}] WARNING: expected column {col!r} "
                "was not found."
            )
            continue

        try:
            df[col] = df[col].astype(dtype)
        except Exception as exc:
            print(
                f"[{name}] WARNING: could not cast {col!r} "
                f"to {dtype}: {exc}"
            )

    for date_col in spec.get("dates", []):
        if date_col not in df.columns:
            print(
                f"[{name}] WARNING: expected date column "
                f"{date_col!r} was not found."
            )
            continue

        df[date_col] = parse_date_column(
            df[date_col],
            spec.get("date_format"),
        )

    return df


def _read_csv(path: str):
    """
    Read CSVs robustly.

    The Catalunya open-data exports can occasionally differ in delimiter
    or encoding, so several reasonable fallbacks are attempted.
    """
    attempts = [
        {"encoding": "UTF-8", "sep": ","},
        {"encoding": "latin1", "sep": ","},
        {"encoding": "UTF-8", "sep": ";"},
        {"encoding": "latin1", "sep": ";"},
    ]

    last_error = None

    for options in attempts:
        try:
            df = pd.read_csv(
                path,
                dtype=str,
                **options,
            )

            if df.shape[1] > 1:
                return df

        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error

    raise ValueError(f"Could not determine CSV format for {path}")


def load_dataset(name: str, filename: str):
    """
    Load one named dataset.

    If the exact current-date filename does not exist, the most recent
    dated file in data/ is automatically used.
    """
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        fallback = find_latest_matching_file(
            name,
            filename,
        )

        if fallback is None:
            raise FileNotFoundError(
                f"[{name}] Could not find {path}, and no "
                f"fallback {name}_YYYYMMDD.csv file exists in {DATA_DIR}."
            )

        path = fallback

    df = _read_csv(path)
    df = apply_dtypes(df, name)

    print(
        f"[{name}] loaded {len(df):,} rows, "
        f"{len(df.columns)} columns from "
        f"{os.path.basename(path)}"
    )

    return df


def load_all_datasets():
    """
    Load all available datasets and keep only the age groups used
    by the website.

    Returns:
        dict[str, pandas.DataFrame]
    """
    datasets = {}

    for name, filename in FILENAMES.items():
        try:
            df = load_dataset(
                name,
                filename,
            )

            # Keep only the age groups used by the website.
            df = population.filter_allowed_age_groups(
                df,
                age_col="grup_edat",
            )

            datasets[name] = df

            print(
                f"[{name}] after age filtering: "
                f"{len(df):,} rows"
            )

        except FileNotFoundError as exc:
            print(f"WARNING: {exc}")

    return datasets

if __name__ == "__main__":
    datasets = load_all_datasets()

    print("\nLoaded datasets:")
    for name, df in datasets.items():
        print(f"  {name}: {len(df):,} rows")