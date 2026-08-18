#!/usr/bin/env python3
"""
generate_site_plots.py

Loads all datasets, computes national incidence (per 100,000 inhabitants)
for every virus and every syndromic diagnosis, applies a 7-period moving
average, and builds:

    1. Interactive plots (Grip / VRS / COVID-19 / Altres) for diagnostics,
     each showing the diagnostic incidence per age group and total together on a
     single chart. For the "altres" tag, there will be a dropdown button to select
     specific disease.
         assets/images/interactive/grip-inc-ages.png
         assets/images/interactive/vrs-inc-ages.png
         assets/images/interactive/covid19-inc-ages.png
         assets/images/interactive/altres-inc-ages.png

    2. Interactive plots (Grip / VRS / COVID-19 / Altres) for multitests,
        showing virus incidence (left axis) together with positivity (right axis), per age
        and total, on a single chart. For the "altres" tag, there will be a dropdown button to select
     specific disease.
            assets/images/interactive/grip-mt-ages.png
            assets/images/interactive/vrs-mt-ages.png
            assets/images/interactive/covid19-mt-ages.png
            assets/images/interactive/altres-mt-ages.png

    3. Interactive plots (Grip / VRS / COVID-19 / Altres) for diagnostics,
     each showing a single x axis ranging from September to August, and
     y axis with diagnostic incidence where the average pre-pandemic season is plotted, 
     together with all seasons since 2020. This means, all epidemics since September 2014 to 
     August 2020 are averaged into a single prepandemic average. Then, this
     average epidemic is plotted on the graph as a grey dashed line. Then, 
     the data is plotted from September 2020 to August 2021, from September 2021 
     to August 2022, until the most recent data available, starting a new season from 
     September the latest even though it is not finished. All seasons will have different
     colours and will share the same x axis. Temporal yearly resolution will not be available,
     only days/weeks and months will be, all seasons are put together on top of each other. This will
     be a grid of plots, where the 1st grid is the total data, the second is the first age group, 
     the third is the second age group, and so on for all age groups available. For the "altres" tag, 
     there will be a dropdown button to select specific disease.
         assets/images/interactive/grip-ontop.png
         assets/images/interactive/vrs-ontop.png
         assets/images/interactive/covid19-ontop.png
         assets/images/interactive/altres-ontop.png

    4. Interactive plots (Grip / VRS / COVID-19 / Altres) for multitests,
        each showing a single x axis ranging from September to August, and
        y axis with positive test incidence in the left and positivity in the right y axis,
        where the average pre-pandemic season is plotted, 
        together with all seasons since 2020. This means, all epidemics since September 2014 to 
        August 2020 are averaged into a single prepandemic average. Then, this
        average epidemic is plotted on the graph as a grey dashed line. Then, 
        the data is plotted from September 2020 to August 2021, from September 2021 
        to August 2022, until the most recent data available, starting a new season from 
        September the latest even though it is not finished. All seasons will have different
        colours and will share the same x axis. Temporal yearly resolution will not be available,
        only days/weeks and months will be, all seasons are put together on top of each other. This will
        be a grid of plots, where the 1st grid is the total data, the second is the first age group, 
        the third is the second age group, and so on for all age groups available. For the "altres" tag, 
        there will be a dropdown button to select specific disease.
            assets/images/interactive/grip-mt-ontop.png
            assets/images/interactive/vrs-mt-ontop.png
            assets/images/interactive/covid19-mt-ontop.png
            assets/images/interactive/altres-mt-ontop.png


  5. TWO combined interactive charts — all viruses in one, all diagnoses
     in one, with a toggleable legend:
         assets/interactive/tots-microbiologics.html
         assets/interactive/tots-sindromes.html
     These are embedded on the homepage (index.md) under "Fes un cop d'ull!".

Run any time you refresh your local data:

    python scripts/generate_site_plots.py

Then commit + push assets/ via GitHub Desktop (data/ stays local).
"""


import os
import sys

import pandas as pd

sys.path.insert(
    0,
    os.path.dirname(
        os.path.abspath(__file__)
    ),
)

from load_data import load_all_datasets
import interactive
import population


REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INTERACTIVE_DIR = os.path.join(
    REPO_ROOT,
    "assets",
    "interactive",
)


CATEGORY_NAMES = [
    "grip",
    "vrs",
    "covid19",
    "altres",
]


def ensure_output_dirs():
    os.makedirs(
        INTERACTIVE_DIR,
        exist_ok=True,
    )


def prepare_sindromic(
    df,
    population_df,
):
    """
    Prepare daily syndromic data.

    Output:

        data
        diagnostic
        grup_edat
        count
        poblacio
        incidencia

    Incidence is calculated nationally and then smoothed over seven
    calendar observations.

    The source is daily, so the seven-period window is seven days.
    """
    required = {
        "data",
        "diagnostic",
        "grup_edat",
        "casos",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Syndromic dataset is missing: "
            + ", ".join(sorted(missing))
        )

    work = df.copy()

    work["data"] = pd.to_datetime(
        work["data"],
        errors="coerce",
    )

    work["casos"] = pd.to_numeric(
        work["casos"],
        errors="coerce",
    )

    work = work.dropna(
        subset=[
            "data",
            "diagnostic",
            "grup_edat",
            "casos",
        ]
    )

    # National age-specific incidence.
    incidence = population.compute_incidence(
        work,
        population_df,
        date_col="data",
        count_col="casos",
        group_cols=[
            "diagnostic",
            "grup_edat",
        ],
    )

    # Seven-day moving average applies ONLY here.
    incidence = population.rolling_average(
        incidence,
        value_col="incidencia",
        group_cols=[
            "diagnostic",
            "grup_edat",
        ],
        window=7,
    )

    return incidence


def prepare_multitests(
    positives,
    tests,
    population_df,
):
    """
    Combine the weekly positive-test and total-test datasets.

    The positive dataset identifies which virus was detected.

    The total-test dataset supplies the denominator for positivity.

    Because total tests do not necessarily contain a virus dimension,
    the total-test denominator is joined to each virus after aggregation
    at the relevant week/age dimensions.

    Output columns:

        data
        virus
        grup_edat
        positive
        total_tests
        poblacio
        incidence
        positivity

    NO moving average is applied.
    """
    required_positive = {
        "data_inici",
        "virus",
        "grup_edat",
        "positiu",
    }

    required_tests = {
        "data_inici",
        "grup_edat",
        "total",
    }

    missing_positive = (
        required_positive - set(positives.columns)
    )

    missing_tests = (
        required_tests - set(tests.columns)
    )

    if missing_positive:
        raise ValueError(
            "Multitest positive dataset is missing: "
            + ", ".join(sorted(missing_positive))
        )

    if missing_tests:
        raise ValueError(
            "Multitest total-test dataset is missing: "
            + ", ".join(sorted(missing_tests))
        )

    pos = positives.copy()
    test = tests.copy()

    pos["data_inici"] = pd.to_datetime(
        pos["data_inici"],
        errors="coerce",
    )

    test["data_inici"] = pd.to_datetime(
        test["data_inici"],
        errors="coerce",
    )

    pos["positiu"] = pd.to_numeric(
        pos["positiu"],
        errors="coerce",
    )

    test["total"] = pd.to_numeric(
        test["total"],
        errors="coerce",
    )

    pos = pos.dropna(
        subset=[
            "data_inici",
            "virus",
            "grup_edat",
            "positiu",
        ]
    )

    test = test.dropna(
        subset=[
            "data_inici",
            "grup_edat",
            "total",
        ]
    )

    # ----------------------------------------
    # Positive detections
    # ----------------------------------------
    positive_group = (
        pos.groupby(
            [
                "data_inici",
                "virus",
                "grup_edat",
            ],
            observed=True,
            dropna=False,
        )["positiu"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "data_inici": "data",
                "positiu": "positive",
            }
        )
    )

    # ----------------------------------------
    # Total tests
    # ----------------------------------------
    tests_group = (
        test.groupby(
            [
                "data_inici",
                "grup_edat",
            ],
            observed=True,
            dropna=False,
        )["total"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "data_inici": "data",
                "total": "total_tests",
            }
        )
    )

    # ----------------------------------------
    # Population
    # ----------------------------------------
    #
    # The multitest data is weekly. The syndromic population is daily.
    #
    # Convert the population denominator to the same weekly start dates.
    #
    pop = population_df.copy()

    pop["data"] = pd.to_datetime(
        pop["data"],
        errors="coerce",
    )

    # Find the Monday corresponding to each date.
    pop["week_start"] = (
        pop["data"]
        - pd.to_timedelta(
            pop["data"].dt.weekday,
            unit="D",
        )
    )

    pop_weekly = (
        pop.groupby(
            [
                "week_start",
                "grup_edat",
            ],
            observed=True,
            dropna=False,
        )["poblacio"]
        .mean()
        .reset_index()
        .rename(
            columns={
                "week_start": "data",
            }
        )
    )

    # ----------------------------------------
    # Normalize source week dates
    # ----------------------------------------
    positive_group["data"] = (
        positive_group["data"]
        - pd.to_timedelta(
            positive_group["data"].dt.weekday,
            unit="D",
        )
    )

    tests_group["data"] = (
        tests_group["data"]
        - pd.to_timedelta(
            tests_group["data"].dt.weekday,
            unit="D",
        )
    )

    # ----------------------------------------
    # Join positives + total tests + population
    # ----------------------------------------
    result = positive_group.merge(
        tests_group,
        on=[
            "data",
            "grup_edat",
        ],
        how="left",
    )

    result = result.merge(
        pop_weekly,
        on=[
            "data",
            "grup_edat",
        ],
        how="left",
    )

    result["incidencia"] = (
        result["positive"]
        / result["poblacio"]
        * 100_000
    )

    result.loc[
        result["poblacio"] <= 0,
        "incidencia",
    ] = pd.NA

    result["positivity"] = (
        result["positive"]
        / result["total_tests"]
        * 100
    )

    result.loc[
        result["total_tests"] <= 0,
        "positivity",
    ] = pd.NA

    return result


def split_categories(
    df,
    name_col,
):
    """
    Return:

        {
            "grip": DataFrame,
            "vrs": DataFrame,
            "covid19": DataFrame,
            "altres": DataFrame,
        }
    """
    result = {
        category: df.iloc[0:0].copy()
        for category in CATEGORY_NAMES
    }

    if df.empty:
        return result

    category_series = (
        df[name_col]
        .astype(str)
        .map(interactive.categorize)
    )

    for category in CATEGORY_NAMES:
        result[category] = df[
            category_series == category
        ].copy()

    return result


def build_sindromic_plots(
    sindromic,
):
    """
    Build:

        grip-inc-ages.html
        vrs-inc-ages.html
        covid19-inc-ages.html
        altres-inc-ages.html

        grip-ontop.html
        vrs-ontop.html
        covid19-ontop.html
        altres-ontop.html
    """
    categories = split_categories(
        sindromic,
        "diagnostic",
    )

    for category, df in categories.items():
        if df.empty:
            print(
                f"  [{category}] no syndromic data."
            )
            continue

        age_output = os.path.join(
            INTERACTIVE_DIR,
            f"{category}-inc-ages.html",
        )

        interactive.build_incidence_by_age(
            df,
            category=category,
            disease_col="diagnostic",
            value_col="incidencia",
            output_path=age_output,
        )

        seasonal_output = os.path.join(
            INTERACTIVE_DIR,
            f"{category}-ontop.html",
        )

        interactive.build_seasonal_incidence(
            df,
            category=category,
            disease_col="diagnostic",
            output_path=seasonal_output,
        )


def build_multitest_plots(
    multitests,
):
    """
    Build:

        grip-mt-ages.html
        vrs-mt-ages.html
        covid19-mt-ages.html
        altres-mt-ages.html

        grip-mt-ontop.html
        vrs-mt-ontop.html
        covid19-mt-ontop.html
        altres-mt-ontop.html
    """
    categories = split_categories(
        multitests,
        "virus",
    )

    for category, df in categories.items():
        if df.empty:
            print(
                f"  [{category}] no multitest data."
            )
            continue

        age_output = os.path.join(
            INTERACTIVE_DIR,
            f"{category}-mt-ages.html",
        )

        interactive.build_multitest_by_age(
            df,
            category=category,
            output_path=age_output,
        )

        seasonal_output = os.path.join(
            INTERACTIVE_DIR,
            f"{category}-mt-ontop.html",
        )

        interactive.build_seasonal_multitest(
            df,
            category=category,
            output_path=seasonal_output,
        )


def build_homepage_plots(
    sindromic,
    multitests,
):
    """
    Build:

        tots-microbiologics.html
        tots-sindromes.html
    """
    if not multitests.empty:
        interactive.build_combined_viruses(
            multitests,
            os.path.join(
                INTERACTIVE_DIR,
                "tots-microbiologics.html",
            ),
        )

    if not sindromic.empty:
        interactive.build_combined_diagnoses(
            sindromic,
            os.path.join(
                INTERACTIVE_DIR,
                "tots-sindromes.html",
            ),
        )


def print_summary(
    sindromic,
    multitests,
):
    print("\n" + "=" * 70)
    print("GENERATED DATA SUMMARY")
    print("=" * 70)

    print(
        f"Syndromic rows:  {len(sindromic):,}"
    )

    if not sindromic.empty:
        print(
            "Syndromic date range: "
            f"{sindromic['data'].min().date()} → "
            f"{sindromic['data'].max().date()}"
        )

        print(
            "Diagnoses: "
            f"{sindromic['diagnostic'].nunique()}"
        )

        print(
            "Age groups: "
            f"{sindromic['grup_edat'].nunique()}"
        )

    print(
        f"Multitest rows:  {len(multitests):,}"
    )

    if not multitests.empty:
        print(
            "Multitest date range: "
            f"{multitests['data'].min().date()} → "
            f"{multitests['data'].max().date()}"
        )

        print(
            "Viruses: "
            f"{multitests['virus'].nunique()}"
        )

        print(
            "Age groups: "
            f"{multitests['grup_edat'].nunique()}"
        )

    print("=" * 70)


def main():
    ensure_output_dirs()

    print("=" * 70)
    print("Loading datasets")
    print("=" * 70)

    datasets = load_all_datasets()

    required = {
        "sindromica",
        "multitests_positius",
        "multitests_tests",
    }

    missing = required - set(datasets)

    if missing:
        print(
            "\nERROR: required datasets are missing:",
            ", ".join(sorted(missing)),
            file=sys.stderr,
        )

        sys.exit(1)

    sindromica_raw = datasets[
        "sindromica"
    ]

    multitests_positius = datasets[
        "multitests_positius"
    ]

    multitests_tests = datasets[
        "multitests_tests"
    ]

    print("\n" + "=" * 70)
    print("Building population denominator")
    print("=" * 70)

    population_df = population.aggregate_population(
        sindromica_raw
    )

    print(
        f"Population rows: {len(population_df):,}"
    )

    print("\n" + "=" * 70)
    print("Preparing syndromic surveillance")
    print("=" * 70)

    sindromic = prepare_sindromic(
        sindromica_raw,
        population_df,
    )

    print(
        f"Prepared syndromic rows: "
        f"{len(sindromic):,}"
    )

    print("\n" + "=" * 70)
    print("Preparing multitest surveillance")
    print("=" * 70)

    multitests = prepare_multitests(
        positives=multitests_positius,
        tests=multitests_tests,
        population_df=population_df,
    )

    print(
        f"Prepared multitest rows: "
        f"{len(multitests):,}"
    )

    print("\n" + "=" * 70)
    print("Building syndromic interactive plots")
    print("=" * 70)

    build_sindromic_plots(
        sindromic
    )

    print("\n" + "=" * 70)
    print("Building multitest interactive plots")
    print("=" * 70)

    build_multitest_plots(
        multitests
    )

    print("\n" + "=" * 70)
    print("Building homepage interactive plots")
    print("=" * 70)

    build_homepage_plots(
        sindromic,
        multitests,
    )

    print_summary(
        sindromic,
        multitests,
    )

    print("\nDone.")
    print(
        f"Interactive plots are in: {INTERACTIVE_DIR}"
    )
    print("\nNext:")
    print("  git add assets/")
    print("  commit + push via GitHub Desktop")


if __name__ == "__main__":
    main()