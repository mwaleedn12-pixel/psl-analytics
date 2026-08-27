"""
PSL Analytics — Data Cleaning

Normalizes venues, seasons, cities, and player names.
Validates deliveries and handles edge cases.

Usage:
    from src.cleaning.cleaner import clean_matches, clean_deliveries
    matches_clean = clean_matches(matches_df)
    deliveries_clean = clean_deliveries(deliveries_df)
"""

import pandas as pd

# ──────────────────────────────────────────────
# Venue Normalization
# ──────────────────────────────────────────────
VENUE_MAP = {
    "Gaddafi Stadium":              "Gaddafi Stadium, Lahore",
    "National Stadium":             "National Stadium, Karachi",
    "Sheikh Zayed Stadium":         "Sheikh Zayed Stadium, Abu Dhabi",
}

# ──────────────────────────────────────────────
# Venue → City Mapping (fill missing cities)
# ──────────────────────────────────────────────
VENUE_CITY_MAP = {
    "Gaddafi Stadium, Lahore":              "Lahore",
    "National Stadium, Karachi":            "Karachi",
    "Dubai International Cricket Stadium":  "Dubai",
    "Sharjah Cricket Stadium":              "Sharjah",
    "Sheikh Zayed Stadium, Abu Dhabi":      "Abu Dhabi",
    "Rawalpindi Cricket Stadium":           "Rawalpindi",
    "Multan Cricket Stadium":               "Multan",
}

# ──────────────────────────────────────────────
# Season → PSL Edition Mapping
# ──────────────────────────────────────────────
SEASON_MAP = {
    "2015/16": "PSL 1",
    "2016/17": "PSL 2",
    "2017/18": "PSL 3",
    "2018/19": "PSL 4",
    "2019/20": "PSL 5",
    "2020/21": "PSL 6",
    "2021":    "PSL 6",   # PSL 6 resumed in 2021
    "2021/22": "PSL 7",
    "2022/23": "PSL 8",
    "2023/24": "PSL 9",
    "2025":    "PSL 10",
    "2026":    "PSL 11",
}

# Season → Year (for sorting/filtering)
SEASON_YEAR_MAP = {
    "2015/16": 2016,
    "2016/17": 2017,
    "2017/18": 2018,
    "2018/19": 2019,
    "2019/20": 2020,
    "2020/21": 2021,
    "2021":    2021,
    "2021/22": 2022,
    "2022/23": 2023,
    "2023/24": 2024,
    "2025":    2025,
    "2026":    2026,
}


def normalize_venues(df: pd.DataFrame, col: str = "venue") -> pd.DataFrame:
    """Map duplicate venue names to canonical versions."""
    df = df.copy()
    df[col] = df[col].replace(VENUE_MAP)
    return df


def fill_cities(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing city values using venue-to-city mapping."""
    df = df.copy()
    if "city" in df.columns:
        for venue, city in VENUE_CITY_MAP.items():
            mask = (df["city"].isna()) & (df["venue"] == venue)
            df.loc[mask, "city"] = city
    return df


def normalize_seasons(df: pd.DataFrame) -> pd.DataFrame:
    """Add psl_edition and season_year columns from raw season string."""
    df = df.copy()
    df["psl_edition"] = df["season"].map(SEASON_MAP)
    df["season_year"] = df["season"].map(SEASON_YEAR_MAP)
    return df


def add_match_phase(df: pd.DataFrame) -> pd.DataFrame:
    """Add phase column to deliveries (powerplay/middle/death)."""
    df = df.copy()
    conditions = [
        df["over"].between(1, 6),
        df["over"].between(7, 15),
        df["over"].between(16, 20),
    ]
    choices = ["powerplay", "middle", "death"]
    df["phase"] = pd.np.select(conditions, choices, default="unknown") if hasattr(pd, "np") else None

    # Use numpy directly
    import numpy as np
    df["phase"] = np.select(conditions, choices, default="unknown")
    return df


def add_cumulative_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add cumulative score, wickets, and ball number within each innings."""
    df = df.copy()
    df = df.sort_values(["match_id", "innings", "over", "ball"]).reset_index(drop=True)

    group_cols = ["match_id", "innings"]

    # Cumulative runs
    df["cumulative_runs"] = df.groupby(group_cols)["total_runs"].cumsum()

    # Cumulative wickets
    df["cumulative_wickets"] = df.groupby(group_cols)["is_wicket"].cumsum()

    # Legal ball number (for calculating overs completed)
    df["legal_ball_number"] = df.groupby(group_cols)["is_legal"].cumsum()

    # Overs completed (e.g. 3.4 means 3 overs and 4 balls)
    df["overs_completed"] = (
        (df["legal_ball_number"] - 1) // 6
        + ((df["legal_ball_number"] - 1) % 6) / 10
    )

    return df


def clean_matches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for matches DataFrame.

    Steps:
        1. Normalize venue names
        2. Fill missing cities
        3. Normalize seasons (add psl_edition, season_year)
        4. Parse date column
        5. Sort by date
    """
    df = df.copy()

    # 1. Venues
    df = normalize_venues(df)

    # 2. Cities
    df = fill_cities(df)

    # 3. Seasons
    df = normalize_seasons(df)

    # 4. Date
    df["date"] = pd.to_datetime(df["date"])

    # 5. Sort
    df = df.sort_values("date").reset_index(drop=True)

    return df


def clean_deliveries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for deliveries DataFrame.

    Steps:
        1. Normalize venue names
        2. Normalize seasons
        3. Add phase column
        4. Add cumulative fields
        5. Parse date and sort
    """
    df = df.copy()

    # 1. Venues
    df = normalize_venues(df)

    # 2. Seasons
    df = normalize_seasons(df)

    # 3. Phase
    df = add_match_phase(df)

    # 4. Date
    df["date"] = pd.to_datetime(df["date"])

    # 5. Sort
    df = df.sort_values(
        ["date", "match_id", "innings", "over", "ball"]
    ).reset_index(drop=True)

    # 6. Cumulative fields
    df = add_cumulative_fields(df)

    return df
