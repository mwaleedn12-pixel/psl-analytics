"""
PSL Analytics — Player Impact Score

The PSL Impact Score measures a player's contribution relative to
match context and difficulty, not just raw numbers.

Components:
    Batting Impact  (40%)  — Runs, SR, boundaries, dots, phase context
    Bowling Impact  (40%)  — Wickets, economy, dots, phase context
    Fielding Impact (10%)  — Catches, run-outs (where data supports)
    Context Impact  (10%)  — Contribution in high-pressure moments

Formula Version: 1.0
All weights are documented and configurable via src/config.py.

Usage:
    from src.analytics.impact_engine import compute_impact_scores
    scores = compute_impact_scores(deliveries_df, matches_df)
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import IMPACT_WEIGHTS


# ════════════════════════════════════════════════════════════
# BATTING IMPACT (per match per player)
# ════════════════════════════════════════════════════════════

def _batting_impact_per_match(deliveries: pd.DataFrame) -> pd.DataFrame:
    """
    Compute batting impact per player per match.

    Sub-components:
        - runs_component:     Normalized runs scored
        - sr_component:       Strike rate relative to match average
        - boundary_component: Boundary hitting ability
        - dot_component:      Penalty for dot balls (inverted)
        - phase_bonus:        Extra credit for death-overs scoring
    """
    legal = deliveries[deliveries["is_legal"] == 1].copy()

    # Per batter per match
    bat = legal.groupby(["match_id", "batter"]).agg(
        runs=("batter_runs", "sum"),
        balls=("batter_runs", "count"),
        fours=("is_four", "sum"),
        sixes=("is_six", "sum"),
        dots=("is_dot", "sum"),
    ).reset_index()

    bat["sr"] = np.where(bat["balls"] > 0, bat["runs"] / bat["balls"] * 100, 0)

    # Match average SR for normalization
    match_avg_sr = bat.groupby("match_id")["sr"].mean().reset_index()
    match_avg_sr.columns = ["match_id", "match_avg_sr"]
    bat = bat.merge(match_avg_sr, on="match_id")

    # Death overs runs
    death = legal[legal["phase"] == "death"]
    death_runs = death.groupby(["match_id", "batter"])["batter_runs"].sum().reset_index()
    death_runs.columns = ["match_id", "batter", "death_runs"]
    bat = bat.merge(death_runs, on=["match_id", "batter"], how="left")
    bat["death_runs"] = bat["death_runs"].fillna(0)

    # ── Sub-components (each 0–100 scale) ──

    # Runs: log scale to reduce dominance of huge innings
    bat["runs_component"] = np.clip(np.log1p(bat["runs"]) / np.log1p(100) * 100, 0, 100)

    # SR relative to match: above avg = bonus, below = penalty
    bat["sr_component"] = np.clip(
        (bat["sr"] / bat["match_avg_sr"].replace(0, 1) - 0.5) * 100, 0, 100
    )

    # Boundary %
    bat["boundary_component"] = np.where(
        bat["balls"] > 0,
        np.clip((bat["fours"] + bat["sixes"]) / bat["balls"] * 200, 0, 100),
        0,
    )

    # Dot ball penalty (fewer dots = higher score)
    bat["dot_component"] = np.where(
        bat["balls"] > 0,
        np.clip((1 - bat["dots"] / bat["balls"]) * 100, 0, 100),
        0,
    )

    # Death overs bonus
    bat["phase_bonus"] = np.clip(np.log1p(bat["death_runs"]) / np.log1p(50) * 100, 0, 100)

    # ── Combined batting impact ──
    bat["batting_impact"] = (
        bat["runs_component"] * 0.35
        + bat["sr_component"] * 0.25
        + bat["boundary_component"] * 0.15
        + bat["dot_component"] * 0.10
        + bat["phase_bonus"] * 0.15
    ).round(2)

    return bat[["match_id", "batter", "runs", "balls", "sr", "batting_impact"]]


# ════════════════════════════════════════════════════════════
# BOWLING IMPACT (per match per player)
# ════════════════════════════════════════════════════════════

def _bowling_impact_per_match(deliveries: pd.DataFrame) -> pd.DataFrame:
    """
    Compute bowling impact per player per match.

    Sub-components:
        - wickets_component:  Wickets taken (weighted)
        - economy_component:  Economy relative to match average (inverted)
        - dot_component:      Dot ball percentage
        - death_bonus:        Bowling in death overs economy
    """
    bowl = deliveries.groupby(["match_id", "bowler"]).agg(
        legal_balls=("is_legal", "sum"),
        runs_conceded=("total_runs", "sum"),
        wickets=("is_wicket", "sum"),
        dots=("is_dot", "sum"),
        fours_conceded=("is_four", "sum"),
        sixes_conceded=("is_six", "sum"),
    ).reset_index()

    bowl["overs"] = bowl["legal_balls"] / 6
    bowl["economy"] = np.where(bowl["overs"] > 0, bowl["runs_conceded"] / bowl["overs"], 0)

    # Match average economy
    match_avg_econ = bowl.groupby("match_id")["economy"].mean().reset_index()
    match_avg_econ.columns = ["match_id", "match_avg_economy"]
    bowl = bowl.merge(match_avg_econ, on="match_id")

    # Death overs economy
    death = deliveries[deliveries["phase"] == "death"]
    death_bowl = death.groupby(["match_id", "bowler"]).agg(
        death_legal=("is_legal", "sum"),
        death_runs=("total_runs", "sum"),
    ).reset_index()
    death_bowl["death_overs"] = death_bowl["death_legal"] / 6
    death_bowl["death_economy"] = np.where(
        death_bowl["death_overs"] > 0,
        death_bowl["death_runs"] / death_bowl["death_overs"], 0
    )
    bowl = bowl.merge(
        death_bowl[["match_id", "bowler", "death_economy"]],
        on=["match_id", "bowler"], how="left"
    )
    bowl["death_economy"] = bowl["death_economy"].fillna(bowl["economy"])

    # ── Sub-components ──

    # Wickets (each wicket is valuable, diminishing returns after 4)
    bowl["wickets_component"] = np.clip(bowl["wickets"] / 4 * 100, 0, 100)

    # Economy (lower than match avg = good)
    bowl["economy_component"] = np.where(
        bowl["match_avg_economy"] > 0,
        np.clip((1 - bowl["economy"] / (bowl["match_avg_economy"] * 1.5)) * 100, 0, 100),
        50,
    )

    # Dot ball %
    bowl["dot_component"] = np.where(
        bowl["legal_balls"] > 0,
        np.clip(bowl["dots"] / bowl["legal_balls"] * 150, 0, 100),
        0,
    )

    # Death bowling bonus (low death economy = high bonus)
    bowl["death_bonus"] = np.clip((1 - bowl["death_economy"] / 15) * 100, 0, 100)

    # ── Combined bowling impact ──
    bowl["bowling_impact"] = (
        bowl["wickets_component"] * 0.40
        + bowl["economy_component"] * 0.25
        + bowl["dot_component"] * 0.20
        + bowl["death_bonus"] * 0.15
    ).round(2)

    return bowl[["match_id", "bowler", "wickets", "economy", "bowling_impact"]]


# ════════════════════════════════════════════════════════════
# FIELDING IMPACT (per match per player)
# ════════════════════════════════════════════════════════════

def _fielding_impact_per_match(deliveries: pd.DataFrame) -> pd.DataFrame:
    """
    Compute fielding impact from catch/run-out data.

    Limited by available data — only catches and run-outs where
    the fielder is recorded.
    """
    wickets = deliveries[deliveries["is_wicket"] == 1].copy()

    # Catches
    catches = wickets[
        (wickets["wicket_kind"] == "caught") & (wickets["fielder"].notna())
    ]
    catch_counts = catches.groupby(["match_id", "fielder"]).size().reset_index(name="catches")
    catch_counts.columns = ["match_id", "player", "catches"]

    # Run-outs
    runouts = wickets[
        (wickets["wicket_kind"] == "run out") & (wickets["fielder"].notna())
    ]
    runout_counts = runouts.groupby(["match_id", "fielder"]).size().reset_index(name="runouts")
    runout_counts.columns = ["match_id", "player", "runouts"]

    # Merge
    fielding = catch_counts.merge(runout_counts, on=["match_id", "player"], how="outer")
    fielding["catches"] = fielding["catches"].fillna(0).astype(int)
    fielding["runouts"] = fielding["runouts"].fillna(0).astype(int)

    # Fielding impact: each catch = 15 pts, each run-out = 25 pts, cap at 100
    fielding["fielding_impact"] = np.clip(
        fielding["catches"] * 15 + fielding["runouts"] * 25, 0, 100
    ).round(2)

    return fielding[["match_id", "player", "catches", "runouts", "fielding_impact"]]


# ════════════════════════════════════════════════════════════
# COMBINED IMPACT SCORE
# ════════════════════════════════════════════════════════════

def compute_impact_scores(
    deliveries: pd.DataFrame,
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute the PSL Impact Score for every player in every match.

    Impact Score = (batting * 0.4) + (bowling * 0.4) + (fielding * 0.1) + (context * 0.1)

    Returns one row per (match_id, player) with component scores
    and final impact_score.
    """
    # ── Component scores ──
    batting = _batting_impact_per_match(deliveries)
    bowling = _bowling_impact_per_match(deliveries)
    fielding = _fielding_impact_per_match(deliveries)

    # ── Build player list (all batters + bowlers + fielders) ──
    bat_players = batting[["match_id", "batter"]].rename(columns={"batter": "player"})
    bowl_players = bowling[["match_id", "bowler"]].rename(columns={"bowler": "player"})
    field_players = fielding[["match_id", "player"]]
    all_players = pd.concat([bat_players, bowl_players, field_players]).drop_duplicates()

    # ── Merge components ──
    result = all_players.copy()

    result = result.merge(
        batting[["match_id", "batter", "batting_impact", "runs", "balls", "sr"]].rename(
            columns={"batter": "player"}
        ),
        on=["match_id", "player"], how="left",
    )
    result = result.merge(
        bowling[["match_id", "bowler", "bowling_impact", "wickets", "economy"]].rename(
            columns={"bowler": "player"}
        ),
        on=["match_id", "player"], how="left",
    )
    result = result.merge(
        fielding[["match_id", "player", "fielding_impact", "catches", "runouts"]],
        on=["match_id", "player"], how="left",
    )

    # Fill NaN with 0 (player didn't bat/bowl/field)
    for col in ["batting_impact", "bowling_impact", "fielding_impact",
                 "runs", "balls", "wickets", "catches", "runouts"]:
        result[col] = result[col].fillna(0)

    # ── Context impact (placeholder — enhanced in Phase 7+) ──
    # For now: average of batting + bowling as proxy
    result["context_impact"] = ((result["batting_impact"] + result["bowling_impact"]) / 2).round(2)

    # ── Final Impact Score ──
    w = IMPACT_WEIGHTS
    result["impact_score"] = (
        result["batting_impact"] * w["batting"]
        + result["bowling_impact"] * w["bowling"]
        + result["fielding_impact"] * w["fielding"]
        + result["context_impact"] * w["context"]
    ).round(2)

    # ── Add match metadata ──
    match_meta = matches[["match_id", "date", "psl_edition", "season_year", "venue"]].copy()
    match_meta["match_id"] = match_meta["match_id"].astype(str)
    result["match_id"] = result["match_id"].astype(str)
    result = result.merge(match_meta, on="match_id", how="left")

    return result.sort_values(
        ["match_id", "impact_score"], ascending=[True, False]
    ).reset_index(drop=True)


def compute_career_impact(impact_df: pd.DataFrame, min_matches: int = 5) -> pd.DataFrame:
    """
    Aggregate impact scores across matches for career rankings.

    Returns one row per player with:
        matches, avg_impact, total_impact, avg_batting, avg_bowling, etc.
    """
    career = impact_df.groupby("player").agg(
        matches=("match_id", "nunique"),
        avg_impact=("impact_score", "mean"),
        max_impact=("impact_score", "max"),
        total_impact=("impact_score", "sum"),
        avg_batting=("batting_impact", "mean"),
        avg_bowling=("bowling_impact", "mean"),
        avg_fielding=("fielding_impact", "mean"),
        total_runs=("runs", "sum"),
        total_wickets=("wickets", "sum"),
    ).reset_index()

    career["avg_impact"] = career["avg_impact"].round(2)
    career["avg_batting"] = career["avg_batting"].round(2)
    career["avg_bowling"] = career["avg_bowling"].round(2)

    if min_matches > 0:
        career = career[career["matches"] >= min_matches]

    return career.sort_values("avg_impact", ascending=False).reset_index(drop=True)
