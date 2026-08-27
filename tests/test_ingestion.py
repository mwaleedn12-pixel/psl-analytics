"""Tests for Phase 1 — Data Ingestion."""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"


def _load():
    matches = pd.read_csv(PROCESSED / "psl_matches.csv")
    deliveries = pd.read_csv(PROCESSED / "psl_deliveries.csv", low_memory=False)
    return matches, deliveries


def test_files_exist():
    assert (PROCESSED / "psl_matches.csv").exists()
    assert (PROCESSED / "psl_deliveries.csv").exists()


def test_match_count():
    matches, _ = _load()
    assert len(matches) == 357, f"Expected 357 matches, got {len(matches)}"


def test_match_columns():
    matches, _ = _load()
    required = [
        "match_id", "season", "date", "venue", "team1", "team2",
        "toss_winner", "toss_decision", "winner",
    ]
    for col in required:
        assert col in matches.columns, f"Missing column: {col}"


def test_delivery_columns():
    _, deliveries = _load()
    required = [
        "match_id", "innings", "over", "ball", "batter", "bowler",
        "batter_runs", "extras_runs", "total_runs",
        "is_wicket", "is_wide", "is_noball", "is_legal",
        "is_four", "is_six", "is_dot",
    ]
    for col in required:
        assert col in deliveries.columns, f"Missing column: {col}"


def test_overs_1_indexed():
    """Overs should be 1-20, not 0-19."""
    _, deliveries = _load()
    assert deliveries["over"].min() >= 1
    assert deliveries["over"].max() <= 20


def test_innings_valid():
    _, deliveries = _load()
    assert set(deliveries["innings"].unique()).issubset({1, 2, 3, 4})


def test_batter_runs_non_negative():
    _, deliveries = _load()
    assert (deliveries["batter_runs"] >= 0).all()


def test_total_runs_equals_batter_plus_extras():
    _, deliveries = _load()
    computed = deliveries["batter_runs"] + deliveries["extras_runs"]
    assert (deliveries["total_runs"] == computed).all()


def test_no_duplicate_matches():
    matches, _ = _load()
    assert matches["match_id"].is_unique


def test_seasons_cover_psl_history():
    matches, _ = _load()
    seasons = matches["season"].unique()
    assert len(seasons) >= 10, f"Expected 10+ seasons, got {len(seasons)}"
