"""
population.py

Population denominators for the age groups used by the surveillance
pipeline, built from the official yearly "population by single year of
age" open-data export (population_YYYYMMDD.csv / poblacio_YYYYMMDD.csv,
placed in data/, same convention as load_data.py).

That file has one row per (any, regio, abs, genere, edat) with a
"poblacio oficial" count. This module aggregates it nationally (summed
across all regions/ABS and both sexes) into yearly totals for the five
age groups used by the site:

    0
    1 i 2
    3 i 4
    5 a 9
    10 a 14

and a synthetic "Total" group (the sum of the five).

Because the surveillance data is daily/weekly but the census is yearly,
`aggregate_population()` expands the yearly totals into a daily series
(each calendar year's population is held constant across its days),
which is what the rest of the pipeline (generate_site_plots.py) expects
to merge against.

IMPORTANT:
This module deliberately does NOT interpolate populations within a
year, and does not redistribute the old 0-4 census bucket evenly
anymore: the source file already reports single-year ages, so the
former 1/5-2/5-2/5 approximation is no longer needed/used.
"""

import glob
import os
import re
from datetime import datetime
from functools import lru_cache

import pandas as pd


# ---------------------------------------------------------------------
# File discovery (mirrors load_data.py's convention)
# ---------------------------------------------------------------------

TODAY = datetime.now().strftime("%Y%m%d")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")

# Either naming is accepted: population_YYYYMMDD.csv (as supplied) or
# poblacio_YYYYMMDD.csv.
POPULATION_FILE_PREFIXES = ["population", "poblacio"]


def _candidate_filenames():
    return [f"{prefix}_{TODAY}.csv" for prefix in POPULATION_FILE_PREFIXES]


def _find_population_file():
    """
    Look for today's dated population file first; otherwise fall back
    to the most recent dated file available in data/.
    """
    for filename in _candidate_filenames():
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            return path

    candidates = []
    for prefix in POPULATION_FILE_PREFIXES:
        candidates += glob.glob(os.path.join(DATA_DIR, f"{prefix}_*.csv"))

    dated = []
    for path in candidates:
        match = re.search(r"_(\d{8})\.csv$", os.path.basename(path))
        if not match:
            continue
        try:
            date = datetime.strptime(match.group(1), "%Y%m%d")
        except ValueError:
            continue
        dated.append((date, path))

    if not dated:
        raise FileNotFoundError(
            "[poblacio] Could not find a population_YYYYMMDD.csv or "
            f"poblacio_YYYYMMDD.csv file in {DATA_DIR}."
        )

    dated.sort(key=lambda item: item[0])
    latest_date, latest_path = dated[-1]

    print(
        "[poblacio] No file dated today. "
        f"Using {os.path.basename(latest_path)} "
        f"({latest_date.strftime('%d/%m/%Y')})."
    )

    return latest_path


def _read_population_csv(path):
    """
    Read the population CSV robustly (encoding/delimiter can vary,
    same defensive approach as load_data._read_csv)."""
    attempts = [
        {"encoding": "UTF-8", "sep": ","},
        {"encoding": "latin1", "sep": ","},
        {"encoding": "UTF-8", "sep": ";"},
        {"encoding": "latin1", "sep": ";"},
    ]

    last_error = None

    for options in attempts:
        try:
            df = pd.read_csv(path, dtype=str, **options)
            if df.shape[1] > 1:
                print(
                    f"[poblacio] loaded {len(df):,} rows, "
                    f"{len(df.columns)} columns from "
                    f"{os.path.basename(path)}"
                )
                return df
        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error

    raise ValueError(f"Could not determine CSV format for {path}")


# ---------------------------------------------------------------------
# Age groups used by the website
# ---------------------------------------------------------------------

AGE_GROUPS = [
    "0",
    "1 i 2",
    "3 i 4",
    "5 a 9",
    "10 a 14",
]

# Single-year ages (as reported in the census file's "edat" column)
# that fall into each of the above groups.
AGE_GROUP_YEARS = {
    "0": [0],
    "1 i 2": [1, 2],
    "3 i 4": [3, 4],
    "5 a 9": [5, 6, 7, 8, 9],
    "10 a 14": [10, 11, 12, 13, 14],
}

# Reverse lookup: single year of age -> age-group label, for fast
# vectorised mapping.
_AGE_TO_GROUP = {
    year: label
    for label, years in AGE_GROUP_YEARS.items()
    for year in years
}


def get_age_groups() -> list[str]:
    """Age groups in display order (without the synthetic "Total")."""
    return AGE_GROUPS.copy()


def get_age_groups_with_total() -> list[str]:
    """Age groups in display order, plus the synthetic "Total" group."""
    return AGE_GROUPS + ["Total"]


# ---------------------------------------------------------------------
# Loading + national aggregation by year
# ---------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_population_raw():
    path = _find_population_file()
    return _read_population_csv(path)


@lru_cache(maxsize=1)
def national_population_by_year() -> pd.DataFrame:
    """
    National population by year and age group (summed across every
    region, ABS and both sexes), including a "Total" age-group row.

    Returns columns: any (int), grup_edat, poblacio
    """
    raw = _load_population_raw().copy()

    pop_col_candidates = ["població oficial", "poblacio oficial", "poblaci\ufffd oficial"]
    pop_col = next((c for c in pop_col_candidates if c in raw.columns), None)
    if pop_col is None:
        raise ValueError(
            "[poblacio] Could not find the population count column "
            f"(looked for {pop_col_candidates!r}). "
            f"Available columns: {list(raw.columns)}"
        )

    raw["any"] = pd.to_numeric(raw["any"], errors="coerce")
    raw["edat"] = pd.to_numeric(raw["edat"], errors="coerce")
    raw["poblacio"] = pd.to_numeric(raw[pop_col], errors="coerce")

    raw = raw.dropna(subset=["any", "edat", "poblacio"])

    # Keep only the single-year ages that belong to one of our age
    # groups; this also keeps the aggregation below fast.
    raw = raw[raw["edat"].isin(_AGE_TO_GROUP.keys())].copy()
    raw["grup_edat"] = raw["edat"].map(_AGE_TO_GROUP)

    grouped = (
        raw.groupby(["any", "grup_edat"], observed=True)["poblacio"]
        .sum()
        .reset_index()
    )

    totals = grouped.groupby("any", observed=True)["poblacio"].sum().reset_index()
    totals["grup_edat"] = "Total"

    result = pd.concat(
        [grouped, totals[["any", "grup_edat", "poblacio"]]],
        ignore_index=True,
    )
    result["any"] = result["any"].astype(int)

    return result


# ---------------------------------------------------------------------
# Public: daily population denominator table
# ---------------------------------------------------------------------

def aggregate_population(sindromica_raw=None, date_col: str = "data") -> pd.DataFrame:
    """
    Build the daily population-denominator table used by the rest of
    the pipeline.

    Each calendar year's official population (per age group, plus the
    "Total" group) is held constant across every day of that year.

    The date range covered is the full span of the census file
    (widened, if needed, to also cover the date range found in
    `sindromica_raw`, so the surveillance data is never left without a
    matching population row even if it extends beyond the census).

    Returns columns: data, grup_edat, poblacio
    """
    by_year = national_population_by_year()

    years_available = sorted(by_year["any"].unique())
    start = pd.Timestamp(year=years_available[0], month=1, day=1)
    end = pd.Timestamp(year=years_available[-1] + 1, month=12, day=31)

    if sindromica_raw is not None and date_col in getattr(sindromica_raw, "columns", []):
        dates = pd.to_datetime(sindromica_raw[date_col], errors="coerce").dropna()
        if not dates.empty:
            start = min(start, dates.min().normalize())
            end = max(end, dates.max().normalize())

    all_days = pd.date_range(start, end, freq="D")

    frames = []

    for grup in by_year["grup_edat"].unique():
        sub = by_year[by_year["grup_edat"] == grup].set_index("any")["poblacio"]

        # Reindex over every year spanned by the requested date range,
        # forward/backward filling for years outside official census
        # coverage (e.g. a partial current year, or dates that precede
        # the earliest census year).
        year_index = range(start.year, end.year + 1)
        sub = sub.reindex(year_index).ffill().bfill()
        year_lookup = sub.to_dict()

        frames.append(pd.DataFrame({
            "data": all_days,
            "grup_edat": grup,
            "poblacio": all_days.year.map(year_lookup),
        }))

    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------
# Incidence calculation (used by prepare_sindromic)
# ---------------------------------------------------------------------

def compute_incidence(
    df: pd.DataFrame,
    population_df: pd.DataFrame,
    date_col: str,
    count_col: str,
    group_cols: list[str],
) -> pd.DataFrame:
    """
    Aggregate `df` by [date_col] + group_cols (summing count_col), then
    divide by the matching national population (per date_col +
    grup_edat) to obtain incidence per 100,000 inhabitants.

    `group_cols` MUST include "grup_edat". A synthetic "Total" grup_edat
    row is added automatically for every combination of the *other*
    group_cols, aggregating counts across all age groups together and
    dividing by the total selected-age population.

    Returns columns: date_col, *group_cols, count, poblacio, incidencia
    """
    if "grup_edat" not in group_cols:
        raise ValueError(
            "compute_incidence requires 'grup_edat' in group_cols"
        )

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")

    grouped = (
        work.groupby([date_col] + list(group_cols), observed=True, dropna=False)[count_col]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={count_col: "count"})
    )

    other_group_cols = [c for c in group_cols if c != "grup_edat"]

    totals = (
        grouped.groupby([date_col] + other_group_cols, observed=True, dropna=False)["count"]
        .sum(min_count=1)
        .reset_index()
    )
    totals["grup_edat"] = "Total"
    totals = totals[[date_col] + list(group_cols) + ["count"]]

    combined = pd.concat([grouped, totals], ignore_index=True)

    pop = (
        population_df[["data", "grup_edat", "poblacio"]]
        .rename(columns={"data": date_col})
    )

    result = combined.merge(pop, on=[date_col, "grup_edat"], how="left")

    result["incidencia"] = (result["count"] / result["poblacio"]) * 100_000
    result.loc[
        result["poblacio"].isna() | (result["poblacio"] <= 0),
        "incidencia",
    ] = pd.NA

    return result


# ---------------------------------------------------------------------
# Moving average (group-aware; used by prepare_sindromic)
# ---------------------------------------------------------------------

def rolling_average(
    df: pd.DataFrame,
    value_col: str,
    group_cols: list[str],
    window: int = 7,
    date_col: str = "data",
    center: bool = True,
    min_periods: int = 1,
) -> pd.DataFrame:
    """
    Apply a position-based rolling average to `value_col`, computed
    independently within each combination of `group_cols` (e.g. one
    diagnostic/age-group pair at a time), after sorting by date.
    """
    if df is None or df.empty:
        return df

    work = df.sort_values(list(group_cols) + [date_col]).copy()

    work[value_col] = (
        work.groupby(list(group_cols), observed=True, dropna=False)[value_col]
        .transform(
            lambda s: s.rolling(
                window=window,
                center=center,
                min_periods=min_periods,
            ).mean()
        )
    )

    return work


# ---------------------------------------------------------------------
# Diagnostic / validation helper
# ---------------------------------------------------------------------

def print_population_summary():
    """Print the latest-year population denominators, for a sanity check."""
    by_year = national_population_by_year()
    latest_year = by_year["any"].max()
    latest = by_year[by_year["any"] == latest_year].set_index("grup_edat")["poblacio"]

    print(f"Population denominators for {latest_year}:")
    print()

    for age_group in AGE_GROUPS:
        print(f"  {age_group:>8}: {latest.get(age_group, float('nan')):,.0f}")

    print()
    print(f"  {'TOTAL':>8}: {latest.get('Total', float('nan')):,.0f}")


if __name__ == "__main__":
    print_population_summary()
