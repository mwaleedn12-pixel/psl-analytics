"""
PSL Analytics — Match State Feature Engineering

Computes ball-by-ball match context features for innings 2.

Features:
    - current_rr: Current run rate
    - required_runs: Runs still needed
    - required_rr: Required run rate
    - wickets_remaining: Wickets left
    - balls_remaining: Legal balls left
    - run_rate_ratio: current_rr / required_rr
    - pressure_index: Combined pressure metric

Usage:
    from src.features.match_features import add_match_state_features
    deliveries = add_match_state_features(deliveries_df, matches_df)
"""

import pandas as pd
import numpy as np


def _get_innings1_totals(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Get first innings total for each match."""
    inn1 = deliveries[deliveries["innings"] == 1]
    totals = inn1.groupby("match_id")["total_runs"].sum().reset_index()
    totals.columns = ["match_id", "target"]
    totals["target"] = totals["target"] + 1  # Need 1 more than innings 1 total
    return totals


def add_match_state_features(
    deliveries: pd.DataFrame,
    matches: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Add match-state context features to each delivery.

    For innings 2: required_runs, required_rr, balls_remaining, etc.
    For both innings: current_rr, wickets_remaining.

    Args:
        deliveries: Cleaned deliveries DataFrame (must have cumulative fields).
        matches: Cleaned matches DataFrame (optional, for additional context).

    Returns:
        DataFrame with added match-state columns.
    """
    df = deliveries.copy()

    # ── Innings 1 targets ──
    targets = _get_innings1_totals(df)
    df = df.merge(targets, on="match_id", how="left")

    # ── Wickets remaining ──
    df["wickets_remaining"] = 10 - df["cumulative_wickets"]

    # ── Balls remaining (legal balls, based on 120 ball innings) ──
    df["balls_remaining"] = 120 - df["legal_ball_number"]
    df["balls_remaining"] = df["balls_remaining"].clip(lower=0)

    # ── Current run rate ──
    overs_bowled = df["legal_ball_number"] / 6
    df["current_rr"] = np.where(
        overs_bowled > 0,
        (df["cumulative_runs"] / overs_bowled).round(2),
        0,
    )

    # ── Innings 2 specific: required runs & required RR ──
    df["required_runs"] = np.where(
        df["innings"] == 2,
        df["target"] - df["cumulative_runs"],
        np.nan,
    )

    overs_remaining = df["balls_remaining"] / 6
    df["required_rr"] = np.where(
        (df["innings"] == 2) & (overs_remaining > 0),
        (df["required_runs"] / overs_remaining).round(2),
        np.nan,
    )

    # ── Run rate ratio (innings 2 only) ──
    df["rr_ratio"] = np.where(
        (df["innings"] == 2) & (df["required_rr"] > 0),
        (df["current_rr"] / df["required_rr"]).round(3),
        np.nan,
    )

    # ── Pressure Index (innings 2 only) ──
    # Higher pressure = high required RR + few wickets remaining + few balls left
    # Normalized 0–100 scale
    df["pressure_index"] = np.where(
        (df["innings"] == 2) & (df["balls_remaining"] > 0),
        (
            # Required RR component (higher RR = more pressure)
            np.clip(df["required_rr"].fillna(0) / 15, 0, 1) * 40
            # Wickets lost component (more wickets lost = more pressure)
            + (df["cumulative_wickets"] / 10) * 30
            # Balls scarcity component (fewer balls = more pressure)
            + (1 - df["balls_remaining"] / 120) * 30
        ).round(1),
        np.nan,
    )

    return df


def compute_innings_summary(deliveries: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-innings summary from deliveries.

    Returns one row per (match_id, innings) with:
        total_runs, wickets, overs, run_rate, fours, sixes, dots, extras.
    """
    summary = deliveries.groupby(["match_id", "innings", "batting_team", "bowling_team"]).agg(
        total_runs=("total_runs", "sum"),
        wickets=("is_wicket", "sum"),
        legal_balls=("is_legal", "sum"),
        fours=("is_four", "sum"),
        sixes=("is_six", "sum"),
        dots=("is_dot", "sum"),
        extras=("extras_runs", "sum"),
        wides=("is_wide", "sum"),
        noballs=("is_noball", "sum"),
    ).reset_index()

    summary["overs"] = (summary["legal_balls"] / 6).round(1)
    summary["run_rate"] = np.where(
        summary["overs"] > 0,
        (summary["total_runs"] / summary["overs"]).round(2),
        0,
    )
    summary["boundary_runs"] = summary["fours"] * 4 + summary["sixes"] * 6
    summary["boundary_pct"] = np.where(
        summary["total_runs"] > 0,
        (summary["boundary_runs"] / summary["total_runs"] * 100).round(1),
        0,
    )
    summary["dot_pct"] = np.where(
        summary["legal_balls"] > 0,
        (summary["dots"] / summary["legal_balls"] * 100).round(1),
        0,
    )

    return summary
