"""Tests for Phase 4 — Feature Engineering."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"

from src.features.player_features import compute_batting_stats, compute_bowling_stats
from src.features.match_features import add_match_state_features, compute_innings_summary


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv")
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


# ── Batting ──

def test_batting_stats_columns():
    _, d = _load()
    batting = compute_batting_stats(d)
    required = ["batter", "innings", "runs", "balls", "avg", "sr", "fours",
                 "sixes", "dots", "boundary_pct", "dot_pct"]
    for col in required:
        assert col in batting.columns, f"Missing: {col}"


def test_batting_stats_top_scorer():
    _, d = _load()
    batting = compute_batting_stats(d, min_innings=10)
    assert batting.iloc[0]["batter"] == "Babar Azam"


def test_batting_sr_range():
    _, d = _load()
    batting = compute_batting_stats(d, min_innings=10)
    assert (batting["sr"] > 0).all()
    assert (batting["sr"] < 400).all(), "SR above 400 is suspicious"


def test_batting_has_phase_sr():
    _, d = _load()
    batting = compute_batting_stats(d)
    phase_cols = [c for c in batting.columns if c.startswith("sr_")]
    assert len(phase_cols) >= 3, f"Expected 3 phase SR columns, got {phase_cols}"


# ── Bowling ──

def test_bowling_stats_columns():
    _, d = _load()
    bowling = compute_bowling_stats(d)
    required = ["bowler", "innings", "wickets", "economy", "dot_pct",
                 "bowling_sr", "runs_conceded"]
    for col in required:
        assert col in bowling.columns, f"Missing: {col}"


def test_bowling_top_wicket_taker():
    _, d = _load()
    bowling = compute_bowling_stats(d, min_innings=10)
    assert bowling.iloc[0]["bowler"] == "Hasan Ali"


def test_bowling_economy_range():
    _, d = _load()
    bowling = compute_bowling_stats(d, min_innings=10)
    assert (bowling["economy"] > 0).all()
    assert (bowling["economy"] < 20).all(), "Economy above 20 is suspicious"


def test_bowling_has_phase_economy():
    _, d = _load()
    bowling = compute_bowling_stats(d)
    phase_cols = [c for c in bowling.columns if c.startswith("economy_")]
    assert len(phase_cols) >= 3, f"Expected 3 phase economy columns, got {phase_cols}"


# ── Match State ──

def test_match_state_columns():
    m, d = _load()
    result = add_match_state_features(d, m)
    required = ["wickets_remaining", "balls_remaining", "current_rr",
                 "required_runs", "required_rr", "pressure_index"]
    for col in required:
        assert col in result.columns, f"Missing: {col}"


def test_wickets_remaining_range():
    m, d = _load()
    result = add_match_state_features(d, m)
    assert result["wickets_remaining"].min() >= 0
    assert result["wickets_remaining"].max() <= 10


def test_required_runs_only_innings2():
    m, d = _load()
    result = add_match_state_features(d, m)
    inn1 = result[result["innings"] == 1]
    assert inn1["required_runs"].isna().all(), "Innings 1 should not have required_runs"


def test_pressure_index_range():
    m, d = _load()
    result = add_match_state_features(d, m)
    pi = result["pressure_index"].dropna()
    assert pi.min() >= 0, "Pressure index should be >= 0"
    assert pi.max() <= 100, "Pressure index should be <= 100"


# ── Innings Summary ──

def test_innings_summary():
    _, d = _load()
    summary = compute_innings_summary(d)
    assert "total_runs" in summary.columns
    assert "run_rate" in summary.columns
    assert "boundary_pct" in summary.columns
    assert len(summary) > 0
