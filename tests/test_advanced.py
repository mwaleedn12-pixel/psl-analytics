"""Tests for Phase 9 (Turning Points) + Phase 10 (Player Similarity)."""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"

from src.models.win_probability import WinProbabilityModel
from src.analytics.turning_points import TurningPointEngine
from src.analytics.player_similarity import PlayerSimilarityEngine
from src.features.player_features import compute_batting_stats, compute_bowling_stats


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv")
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


def _trained_wp():
    m, d = _load()
    wp = WinProbabilityModel("logistic")
    wp.train(d, m)
    return wp, m, d


# ════════════════════════════════════════════════════════════
# TURNING POINTS
# ════════════════════════════════════════════════════════════

def test_turning_point_detection():
    wp, m, d = _trained_wp()
    engine = TurningPointEngine(wp)
    mid = str(d["match_id"].unique()[5])
    points = engine.detect(d, m, match_id=mid, top_n=3)
    assert len(points) <= 3
    assert "prob_change" in points.columns
    assert "event_type" in points.columns


def test_turning_point_has_description():
    wp, m, d = _trained_wp()
    engine = TurningPointEngine(wp)
    mid = str(d["match_id"].unique()[5])
    points = engine.detect(d, m, match_id=mid)
    if len(points) > 0:
        assert "description" in points.columns
        assert len(points.iloc[0]["description"]) > 10


def test_probability_timeline():
    wp, m, d = _trained_wp()
    engine = TurningPointEngine(wp)
    mid = str(d["match_id"].unique()[5])
    timeline = engine.compute_probability_timeline(d, m, match_id=mid)
    assert "win_probability" in timeline.columns
    assert "prob_change" in timeline.columns
    assert (timeline["win_probability"] >= 0).all()
    assert (timeline["win_probability"] <= 1).all()


def test_match_summary():
    wp, m, d = _trained_wp()
    engine = TurningPointEngine(wp)
    mid = str(d["match_id"].unique()[5])
    summary = engine.match_summary(d, m, mid)
    assert "match_info" in summary
    assert "turning_points" in summary
    assert "timeline" in summary


# ════════════════════════════════════════════════════════════
# PLAYER SIMILARITY
# ════════════════════════════════════════════════════════════

def test_batting_similarity_fit():
    _, d = _load()
    batting = compute_batting_stats(d, min_innings=1)
    engine = PlayerSimilarityEngine()
    result = engine.fit_batting(batting, min_innings=10)
    assert "archetype" in result.columns
    assert "cluster" in result.columns
    assert len(result) > 0


def test_find_similar_batters():
    _, d = _load()
    batting = compute_batting_stats(d, min_innings=1)
    engine = PlayerSimilarityEngine()
    engine.fit_batting(batting, min_innings=10)
    similar = engine.find_similar_batters("Babar Azam", top_n=5)
    assert len(similar) == 5
    assert "similarity" in similar.columns
    assert (similar["similarity"] <= 1.0).all()
    assert "Babar Azam" not in similar["player"].values


def test_bowling_similarity_fit():
    _, d = _load()
    bowling = compute_bowling_stats(d, min_innings=1)
    engine = PlayerSimilarityEngine()
    result = engine.fit_bowling(bowling, min_innings=10)
    assert "archetype" in result.columns
    assert len(result) > 0


def test_find_similar_bowlers():
    _, d = _load()
    bowling = compute_bowling_stats(d, min_innings=1)
    engine = PlayerSimilarityEngine()
    engine.fit_bowling(bowling, min_innings=10)
    similar = engine.find_similar_bowlers("Hasan Ali", top_n=5)
    assert len(similar) == 5
    assert "Hasan Ali" not in similar["player"].values


def test_archetypes_assigned():
    _, d = _load()
    batting = compute_batting_stats(d, min_innings=1)
    engine = PlayerSimilarityEngine()
    result = engine.fit_batting(batting, min_innings=10)
    assert result["archetype"].notna().all()
    # Should have multiple archetype types
    assert result["archetype"].nunique() >= 2
