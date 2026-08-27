"""
PSL Analytics — Player Feature Engineering

Computes per-player batting and bowling statistics from cleaned deliveries.

Usage:
    from src.features.player_features import compute_batting_stats, compute_bowling_stats
    batting = compute_batting_stats(deliveries_df)
    bowling = compute_bowling_stats(deliveries_df)
"""

import pandas as pd
import numpy as np


def compute_batting_stats(
    deliveries: pd.DataFrame,
    min_innings: int = 1,
) -> pd.DataFrame:
    """
    Compute batting statistics per player.

    Returns one row per batter with:
        innings, runs, balls, avg, sr, fours, sixes, dots,
        boundary_pct, dot_pct, plus phase-level SR.
    """
    legal = deliveries[deliveries["is_legal"] == 1].copy()

    # ── Overall stats ──
    overall = legal.groupby("batter").agg(
        innings=("match_id", "nunique"),
        balls=("batter_runs", "count"),
        runs=("batter_runs", "sum"),
        fours=("is_four", "sum"),
        sixes=("is_six", "sum"),
        dots=("is_dot", "sum"),
    ).reset_index()

    overall["avg"] = (overall["runs"] / overall["innings"]).round(2)
    overall["sr"] = (overall["runs"] / overall["balls"] * 100).round(2)
    overall["boundary_pct"] = (
        (overall["fours"] + overall["sixes"]) / overall["balls"] * 100
    ).round(2)
    overall["dot_pct"] = (overall["dots"] / overall["balls"] * 100).round(2)

    # ── Phase-level SR ──
    phase_sr = (
        legal.groupby(["batter", "phase"])
        .agg(phase_runs=("batter_runs", "sum"), phase_balls=("batter_runs", "count"))
        .reset_index()
    )
    phase_sr["phase_sr"] = (phase_sr["phase_runs"] / phase_sr["phase_balls"] * 100).round(2)
    phase_pivot = phase_sr.pivot_table(
        index="batter", columns="phase", values="phase_sr", fill_value=0
    ).reset_index()
    phase_pivot.columns = [
        "batter" if c == "batter" else f"sr_{c}" for c in phase_pivot.columns
    ]

    # ── Phase-level runs ──
    phase_runs_pivot = phase_sr.pivot_table(
        index="batter", columns="phase", values="phase_runs", fill_value=0
    ).reset_index()
    phase_runs_pivot.columns = [
        "batter" if c == "batter" else f"runs_{c}" for c in phase_runs_pivot.columns
    ]

    # ── Merge ──
    result = overall.merge(phase_pivot, on="batter", how="left")
    result = result.merge(phase_runs_pivot, on="batter", how="left")

    if min_innings > 1:
        result = result[result["innings"] >= min_innings]

    return result.sort_values("runs", ascending=False).reset_index(drop=True)


def compute_bowling_stats(
    deliveries: pd.DataFrame,
    min_innings: int = 1,
) -> pd.DataFrame:
    """
    Compute bowling statistics per player.

    Returns one row per bowler with:
        innings, overs, runs_conceded, wickets, economy, sr,
        dot_pct, boundary_conceded_pct, plus phase-level economy.
    """
    # ── Overall stats ──
    overall = deliveries.groupby("bowler").agg(
        innings=("match_id", "nunique"),
        total_balls=("bowler", "count"),
        legal_balls=("is_legal", "sum"),
        runs_conceded=("total_runs", "sum"),
        wickets=("is_wicket", "sum"),
        dots=("is_dot", "sum"),
        fours_conceded=("is_four", "sum"),
        sixes_conceded=("is_six", "sum"),
        wides=("is_wide", "sum"),
        noballs=("is_noball", "sum"),
    ).reset_index()

    overall["overs"] = (overall["legal_balls"] / 6).round(2)
    overall["economy"] = np.where(
        overall["overs"] > 0,
        (overall["runs_conceded"] / overall["overs"]).round(2),
        0,
    )
    overall["bowling_sr"] = np.where(
        overall["wickets"] > 0,
        (overall["legal_balls"] / overall["wickets"]).round(2),
        np.nan,
    )
    overall["dot_pct"] = np.where(
        overall["legal_balls"] > 0,
        (overall["dots"] / overall["legal_balls"] * 100).round(2),
        0,
    )
    overall["boundary_conceded_pct"] = np.where(
        overall["legal_balls"] > 0,
        (
            (overall["fours_conceded"] + overall["sixes_conceded"])
            / overall["legal_balls"]
            * 100
        ).round(2),
        0,
    )

    # ── Phase-level economy ──
    phase_bowl = (
        deliveries.groupby(["bowler", "phase"])
        .agg(
            phase_legal=("is_legal", "sum"),
            phase_runs=("total_runs", "sum"),
            phase_wickets=("is_wicket", "sum"),
        )
        .reset_index()
    )
    phase_bowl["phase_overs"] = phase_bowl["phase_legal"] / 6
    phase_bowl["phase_economy"] = np.where(
        phase_bowl["phase_overs"] > 0,
        (phase_bowl["phase_runs"] / phase_bowl["phase_overs"]).round(2),
        0,
    )

    phase_econ_pivot = phase_bowl.pivot_table(
        index="bowler", columns="phase", values="phase_economy", fill_value=0
    ).reset_index()
    phase_econ_pivot.columns = [
        "bowler" if c == "bowler" else f"economy_{c}"
        for c in phase_econ_pivot.columns
    ]

    phase_wkt_pivot = phase_bowl.pivot_table(
        index="bowler", columns="phase", values="phase_wickets", fill_value=0
    ).reset_index()
    phase_wkt_pivot.columns = [
        "bowler" if c == "bowler" else f"wickets_{c}"
        for c in phase_wkt_pivot.columns
    ]

    # ── Merge ──
    result = overall.merge(phase_econ_pivot, on="bowler", how="left")
    result = result.merge(phase_wkt_pivot, on="bowler", how="left")

    if min_innings > 1:
        result = result[result["innings"] >= min_innings]

    return result.sort_values("wickets", ascending=False).reset_index(drop=True)
