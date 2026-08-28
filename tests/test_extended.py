"""Tests for Quick Win + Advanced analytics engines."""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"

from src.analytics.extended_engines import (
    SeasonRankings, PowerplayIndex, DeathSpecialists,
    PlayerValueIndex, PressurePerformance, ClutchAnalysis,
    SeasonImprovement,
)
from src.analytics.impact_engine import compute_impact_scores


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv")
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


# ── Season Rankings ──

def test_top_run_scorers_per_season():
    _, d = _load()
    result = SeasonRankings.top_run_scorers(d, top_n=3)
    assert len(result) > 0
    assert "rank" in result.columns
    assert result["rank"].max() <= 3
    seasons = result["psl_edition"].nunique()
    assert seasons >= 10


def test_top_wicket_takers_per_season():
    _, d = _load()
    result = SeasonRankings.top_wicket_takers(d, top_n=3)
    assert len(result) > 0
    assert result["rank"].max() <= 3


# ── Powerplay Aggression ──

def test_powerplay_index():
    _, d = _load()
    result = PowerplayIndex.compute(d, min_innings=10)
    assert "aggression_index" in result.columns
    assert (result["aggression_index"] >= 0).all()
    assert (result["aggression_index"] <= 100).all()
    assert len(result) > 0


# ── Death Specialists ──

def test_best_finishers():
    _, d = _load()
    result = DeathSpecialists.best_finishers(d, min_innings=10)
    assert "finisher_score" in result.columns
    assert "sr" in result.columns
    assert len(result) > 0


def test_best_death_bowlers():
    _, d = _load()
    result = DeathSpecialists.best_death_bowlers(d, min_innings=10)
    assert "death_score" in result.columns
    assert "economy" in result.columns
    assert len(result) > 0


# ── Player Value Index ──

def test_player_value_index():
    m, d = _load()
    scores = compute_impact_scores(d, m)
    result = PlayerValueIndex.compute(scores, min_matches=20)
    assert "value_index" in result.columns
    assert "consistency" in result.columns
    assert (result["consistency"] >= 0).all()
    assert (result["consistency"] <= 1).all()


# ── Pressure Performance ──

def test_batting_under_pressure():
    m, d = _load()
    result = PressurePerformance.batting_under_pressure(d, m, min_innings=3)
    assert "pressure_sr" in result.columns
    assert "pressure_avg" in result.columns
    assert len(result) > 0


# ── Clutch Analysis ──

def test_clutch_batters():
    _, d = _load()
    result = ClutchAnalysis.clutch_batters(d, rr_threshold=10, min_balls=20)
    assert "clutch_sr" in result.columns
    assert len(result) > 0


def test_clutch_bowlers():
    _, d = _load()
    result = ClutchAnalysis.clutch_bowlers(d, rr_threshold=10, min_balls=20)
    assert "clutch_economy" in result.columns
    assert len(result) > 0


# ── Season Improvement ──

def test_batting_trend():
    _, d = _load()
    result = SeasonImprovement.batting_trend(d, min_seasons=3)
    assert "trend" in result.columns
    assert "sr_trend_slope" in result.columns
    assert set(result["trend"].unique()).issubset({"Improving", "Declining", "Stable"})
    assert len(result) > 0
