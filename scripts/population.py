#!/usr/bin/env python3
"""
population.py

Reference population data for Catalonia (1 January 2026), used to convert
raw case/positive counts into incidence rates (per 100,000 inhabitants).

Source: population table pasted by the user, "Població a 1 de gener. Per
sexe i grups d'edat. Catalunya. 2026 (p)".

IMPORTANT ASSUMPTION — read before trusting numbers for age 0-4:
The census only gives a single combined bucket "De 0 a 4 anys" (5 single
years of age). But the surveillance datasets split this into three finer
pediatric groups: "0", "1 i 2", "3 i 4". Since we don't have single-year
population counts, we approximate by assuming the 0-4 population is spread
evenly across its 5 single years (dividing by 5). This is a reasonable
approximation for population pyramids without sharp discontinuities at
these ages, but it is an approximation — if you get access to single-year
population data later (e.g. from Idescat), swap it in here for more
accurate rates.

The "80 o més" bucket used in the datasets, by contrast, needs no
approximation: it's an exact sum of five whole census buckets (80-84
through 100+).
"""

import pandas as pd

# Raw census counts by 5-year age band and sex
CENSUS_POPULATION = {
    "De 0 a 4 anys":   {"Home": 147327, "Dona": 139256},
    "De 5 a 9 anys":   {"Home": 180270, "Dona": 171700},
    "De 10 a 14 anys": {"Home": 216268, "Dona": 202349},
    "De 15 a 19 anys": {"Home": 244789, "Dona": 223461},
    "De 20 a 24 anys": {"Home": 254131, "Dona": 227110},
    "De 25 a 29 anys": {"Home": 262305, "Dona": 239690},
    "De 30 a 34 anys": {"Home": 269705, "Dona": 252470},
    "De 35 a 39 anys": {"Home": 269441, "Dona": 260737},
    "De 40 a 44 anys": {"Home": 288731, "Dona": 285373},
    "De 45 a 49 anys": {"Home": 341190, "Dona": 332504},
    "De 50 a 54 anys": {"Home": 335384, "Dona": 326910},
    "De 55 a 59 anys": {"Home": 291696, "Dona": 292469},
    "De 60 a 64 anys": {"Home": 250805, "Dona": 265896},
    "De 65 a 69 anys": {"Home": 210386, "Dona": 237861},
    "De 70 a 74 anys": {"Home": 169777, "Dona": 202684},
    "De 75 a 79 anys": {"Home": 141318, "Dona": 181506},
    "De 80 a 84 anys": {"Home": 98903,  "Dona": 139664},
    "De 85 a 89 anys": {"Home": 54884,  "Dona": 91532},
    "De 90 a 94 anys": {"Home": 26451,  "Dona": 57197},
    "De 95 a 99 anys": {"Home": 5618,   "Dona": 17823},
    "100 anys o més":  {"Home": 534,    "Dona": 2605},
}

TOTAL_POPULATION = {"Home": 4059913, "Dona": 4150797, "Total": 8210710}


def _pop_0_4_per_single_year(sexe: str) -> float:
    """Approximate population for ONE single year of age within 0-4,
    assuming an even split across the 5 years in that census bucket."""
    return CENSUS_POPULATION["De 0 a 4 anys"][sexe] / 5


# Maps the exact age-group labels used in the surveillance datasets to a
# population count, given a sex. Covers both the pediatric-only labels
# used in "sindromica" (0, 1 i 2, 3 i 4, 5 a 9, 10 a 14) and the full
# adult range used in "microbiologica".
AGE_GROUP_TO_POPULATION = {
    "0":        lambda s: _pop_0_4_per_single_year(s) * 1,
    "1 i 2":    lambda s: _pop_0_4_per_single_year(s) * 2,
    "3 i 4":    lambda s: _pop_0_4_per_single_year(s) * 2,
    "5 a 9":    lambda s: CENSUS_POPULATION["De 5 a 9 anys"][s],
    "10 a 14":  lambda s: CENSUS_POPULATION["De 10 a 14 anys"][s],
    "15 a 19":  lambda s: CENSUS_POPULATION["De 15 a 19 anys"][s],
    "20 a 24":  lambda s: CENSUS_POPULATION["De 20 a 24 anys"][s],
    "25 a 29":  lambda s: CENSUS_POPULATION["De 25 a 29 anys"][s],
    "30 a 34":  lambda s: CENSUS_POPULATION["De 30 a 34 anys"][s],
    "35 a 39":  lambda s: CENSUS_POPULATION["De 35 a 39 anys"][s],
    "40 a 44":  lambda s: CENSUS_POPULATION["De 40 a 44 anys"][s],
    "45 a 49":  lambda s: CENSUS_POPULATION["De 45 a 49 anys"][s],
    "50 a 54":  lambda s: CENSUS_POPULATION["De 50 a 54 anys"][s],
    "55 a 59":  lambda s: CENSUS_POPULATION["De 55 a 59 anys"][s],
    "60 a 64":  lambda s: CENSUS_POPULATION["De 60 a 64 anys"][s],
    "65 a 69":  lambda s: CENSUS_POPULATION["De 65 a 69 anys"][s],
    "70 a 74":  lambda s: CENSUS_POPULATION["De 70 a 74 anys"][s],
    "75 a 79":  lambda s: CENSUS_POPULATION["De 75 a 79 anys"][s],
    "80 o més": lambda s: sum(CENSUS_POPULATION[k][s] for k in [
        "De 80 a 84 anys", "De 85 a 89 anys", "De 90 a 94 anys",
        "De 95 a 99 anys", "100 anys o més",
    ]),
}


def get_population(grup_edat: str, sexe: str = "Total"):
    """Population count for a given age-group label and sex.
    sexe="Total" (or anything other than 'Home'/'Dona', e.g. 'No disponible')
    returns both sexes combined. Returns None if grup_edat isn't recognized
    (e.g. 'No disponible')."""
    getter = AGE_GROUP_TO_POPULATION.get(grup_edat)
    if getter is None:
        return None
    if sexe in ("Home", "Dona"):
        return getter(sexe)
    return getter("Home") + getter("Dona")


def compute_national_incidence(df, date_col: str, count_col: str, sexe: str = "Total"):
    """Crude national incidence per 100,000 inhabitants: sums `count_col`
    across everything (all regions, ages, sexes present in df) grouped by
    date_col, divided by the total Catalan population. Use this for an
    overall trend for one virus/diagnostic, regardless of age breakdown.

    Returns a pandas Series indexed by date.
    """
    pop = TOTAL_POPULATION.get(sexe, TOTAL_POPULATION["Total"])
    grouped = df.groupby(date_col)[count_col].sum(numeric_only=True)
    return (grouped / pop) * 100000


def compute_age_stratified_incidence(df, date_col: str, count_col: str,
                                      age_col: str, sex_col: str,
                                      grup_edat: str, sexe: str = "Total"):
    """Incidence per 100,000 inhabitants for ONE specific age group (and
    sex, or 'Total' for both sexes combined), aggregated across all regions
    present in df. Returns a pandas Series indexed by date, or None if the
    age group isn't recognized.
    """
    subset = df[df[age_col] == grup_edat]
    if sexe in ("Home", "Dona"):
        subset = subset[subset[sex_col] == sexe]

    pop = get_population(grup_edat, sexe)
    if not pop:
        return None

    grouped = subset.groupby(date_col)[count_col].sum(numeric_only=True)
    return (grouped / pop) * 100000


def rolling_average(series, window: int = 7, center: bool = True, min_periods: int = 1):
    """Simple rolling average smoothing (position-based, not calendar-based)."""
    if series is None or series.empty:
        return series
    return series.rolling(window=window, center=center, min_periods=min_periods).mean()


def to_daily_smoothed(series, window: int = 7, center: bool = True, min_periods: int = 1):
    """Takes an incidence Series with WEEKLY-spaced points (as returned by
    compute_national_incidence, since the source data is reported weekly)
    and produces a DAILY-resolution series via linear interpolation
    between the known weekly points, then applies a `window`-day rolling
    average.

    IMPORTANT: Catalonia's open data here is reported weekly, not daily —
    there is no true daily granularity in the source. This function
    interpolates smoothly between weekly points to approximate a daily
    view (useful for smoother charts and season-over-season comparison),
    but the underlying data resolution is still weekly. Don't present
    this as literal daily case counts.
    """
    if series is None or series.empty:
        return series
    s = series.sort_index()
    daily_index = pd.date_range(s.index.min(), s.index.max(), freq="D")
    daily = s.reindex(s.index.union(daily_index)).sort_index()
    daily = daily.interpolate(method="linear")
    daily = daily.reindex(daily_index)
    return daily.rolling(window=window, center=center, min_periods=min_periods).mean()
