"""
population.py

Population denominators for the age groups used by the surveillance
pipeline.

Only the following age groups are included:

    0
    1 i 2
    3 i 4
    5 a 9
    10 a 14

The surveillance datasets contain finer age groups than the census for
ages 0-4. Since the census provides only "De 0 a 4 anys", the population
for ages 0, 1-2, and 3-4 is approximated by distributing the 0-4
population evenly across the five single years:

    age 0       = 1/5 of population 0-4
    ages 1-2    = 2/5 of population 0-4
    ages 3-4    = 2/5 of population 0-4

This approximation is used consistently for both sexes and therefore
for the total population denominator.

IMPORTANT:

This module deliberately does NOT contain any daily interpolation.

SINDROMICA:
    Daily source data.
    The 7-day moving average is applied elsewhere in the plotting/data
    pipeline.

MULTITEST:
    Weekly source data.
    The raw weekly values are used directly.
"""


import pandas as pd


# ---------------------------------------------------------------------
# Population source
# ---------------------------------------------------------------------

# Catalonia population, 1 January 2026.
#
# Source:
# "Població a 1 de gener. Per sexe i grups d'edat. Catalunya. 2026 (p)"
#
# Only the census groups needed by this project are retained here.

CENSUS_POPULATION = {
    "De 0 a 4 anys": {
        "Home": 147327,
        "Dona": 139256,
    },
    "De 5 a 9 anys": {
        "Home": 180270,
        "Dona": 171700,
    },
    "De 10 a 14 anys": {
        "Home": 216268,
        "Dona": 202349,
    },
}


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


# ---------------------------------------------------------------------
# Population helpers
# ---------------------------------------------------------------------

def _pop_0_4_per_single_year(sexe: str) -> float:
    """
    Approximate the population of one single year within the 0-4
    census bucket.

    The census gives only 0-4 as a combined group, so we divide the
    population evenly across the five single years.
    """
    return CENSUS_POPULATION["De 0 a 4 anys"][sexe] / 5


def _population_for_age_group(grup_edat: str, sexe: str) -> float | None:
    """
    Return the population for one of the allowed surveillance age groups.

    Returns None for any age group outside AGE_GROUPS.
    """

    if grup_edat == "0":
        return _pop_0_4_per_single_year(sexe)

    if grup_edat == "1 i 2":
        return _pop_0_4_per_single_year(sexe) * 2

    if grup_edat == "3 i 4":
        return _pop_0_4_per_single_year(sexe) * 2

    if grup_edat == "5 a 9":
        return CENSUS_POPULATION["De 5 a 9 anys"][sexe]

    if grup_edat == "10 a 14":
        return CENSUS_POPULATION["De 10 a 14 anys"][sexe]

    return None


def get_population(grup_edat: str, sexe: str = "Total"):
    """
    Return the population denominator for one allowed age group.

    Parameters
    ----------
    grup_edat:
        One of:

            "0"
            "1 i 2"
            "3 i 4"
            "5 a 9"
            "10 a 14"

    sexe:
        "Home", "Dona", or "Total".

        Any value other than "Home" or "Dona" is treated as "Total".

    Returns
    -------
    float or None
        Population count, or None if the age group is not recognised.
    """

    if grup_edat not in AGE_GROUPS:
        return None

    if sexe in ("Home", "Dona"):
        return _population_for_age_group(grup_edat, sexe)

    home = _population_for_age_group(grup_edat, "Home")
    dona = _population_for_age_group(grup_edat, "Dona")

    return home + dona


# ---------------------------------------------------------------------
# Total population for the selected surveillance age range
# ---------------------------------------------------------------------

def get_selected_population(sexe: str = "Total") -> float:
    """
    Return the total population represented by the selected age groups.

    This is NOT the total population of Catalonia.

    It is the population of:

        0
        1 i 2
        3 i 4
        5 a 9
        10 a 14

    This denominator must be used whenever a "Total" incidence is
    calculated, because the numerator is also restricted to these
    age groups.
    """

    return sum(
        get_population(age_group, sexe)
        for age_group in AGE_GROUPS
    )


# ---------------------------------------------------------------------
# Data filtering
# ---------------------------------------------------------------------

def filter_allowed_age_groups(
    df: pd.DataFrame,
    age_col: str = "grup_edat",
) -> pd.DataFrame:
    """
    Filter a surveillance dataframe so that only the age groups used
    by this project remain.

    A copy is returned.

    This should be applied to BOTH:

        - sindromica
        - multitests_tests
        - multitests_positius

    before calculating any incidence or positivity.
    """

    if age_col not in df.columns:
        raise ValueError(
            f"Column '{age_col}' not found in dataframe. "
            f"Available columns: {list(df.columns)}"
        )

    filtered = df[df[age_col].isin(AGE_GROUPS)].copy()

    return filtered


# ---------------------------------------------------------------------
# Incidence calculations
# ---------------------------------------------------------------------

def compute_national_incidence(
    df: pd.DataFrame,
    date_col: str,
    count_col: str,
    sexe: str = "Total",
) -> pd.Series:

    pop = get_selected_population(sexe)

    grouped = (
        df
        .groupby(date_col)[count_col]
        .sum(min_count=1)
    )

    return (grouped / pop) * 100000


def compute_age_stratified_incidence(
    df: pd.DataFrame,
    date_col: str,
    count_col: str,
    age_col: str,
    sex_col: str,
    grup_edat: str,
    sexe: str = "Total",
) -> pd.Series | None:

    if grup_edat not in AGE_GROUPS:
        return None

    subset = df[df[age_col] == grup_edat].copy()

    if sexe in ("Home", "Dona"):
        subset = subset[subset[sex_col] == sexe]

    pop = get_population(grup_edat, sexe)

    if pop is None or pop <= 0:
        return None

    grouped = (
        subset
        .groupby(date_col)[count_col]
        .sum(min_count=1)
    )

    return (grouped / pop) * 100000


# ---------------------------------------------------------------------
# Moving average
# ---------------------------------------------------------------------

def rolling_average(
    series: pd.Series,
    window: int = 7,
    center: bool = True,
    min_periods: int = 1,
) -> pd.Series:
    """
    Apply a position-based rolling average.

    This is intended for the DAILY sindromica data.

    For the current pipeline:

        sindromica -> window=7

    Multitest data must NOT be passed through this function.
    """

    if series is None or series.empty:
        return series

    return series.rolling(
        window=window,
        center=center,
        min_periods=min_periods,
    ).mean()


# ---------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------

def get_age_groups() -> list[str]:
    """
    Return the age groups in the desired display order.
    """
    return AGE_GROUPS.copy()


# ---------------------------------------------------------------------
# Validation / diagnostic information
# ---------------------------------------------------------------------

def print_population_summary():
    """
    Print the population denominators used by the website.

    Useful for checking that the population calculation is behaving
    as expected.
    """

    print("Population denominators used by the surveillance site:")
    print()

    for age_group in AGE_GROUPS:
        population = get_population(age_group)
        print(f"  {age_group:>8}: {population:,.0f}")

    print()
    print(
        f"  {'TOTAL':>8}: "
        f"{get_selected_population():,.0f}"
    )


if __name__ == "__main__":
    print_population_summary()