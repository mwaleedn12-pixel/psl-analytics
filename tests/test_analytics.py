"""Tests for Phase 5 (Impact Score) + Phase 6 (Advanced Analytics)."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"

from src.analytics.impact_engine import compute_impact_scores, compute_career_impact
from src.analytics.engines import (
    FormEngine, VenueEngine, MatchupEngine,
    TeamEngine, TossEngine, PhaseEngine,
)


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv")
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


# ════════════════════════════════════════════════════════════
# IMPACT SCORE TESTS
# ════════════════════════════════════════════════════════════

def test_impact_scores_columns():
    m, d = _load()
    scores = compute_impact_scores(d, m)
    required = ["match_id", "player", "batting_impact", "bowling_impact",
                 "fielding_impact", "impact_score"]
    for col in required:
        assert col in scores.columns, f"Missing: {col}"


def test_impact_scores_range():
    m, d = _load()
    scores = compute_impact_scores(d, m)
    assert scores["impact_score"].min() >= 0, "Impact score should be >= 0"
    assert scores["impact_score"].max() <= 100, "Impact score should be <= 100"


def test_career_impact_ranking():
    m, d = _load()
    scores = compute_impact_scores(d, m)
    career = compute_career_impact(scores, min_matches=20)
    assert len(career) > 0
    # Top player should have reasonable avg impact
    assert career.iloc[0]["avg_impact"] > 10


def test_impact_not_all_zeros():
    m, d = _load()
    scores = compute_impact_scores(d, m)
    assert scores["impact_score"].sum() > 0


# ════════════════════════════════════════════════════════════
# FORM ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_batting_form():
    _, d = _load()
    form = FormEngine.batting_form(d, window=5)
    assert "rolling_avg" in form.columns
    assert "rolling_sr" in form.columns
    assert len(form) > 0


def test_bowling_form():
    _, d = _load()
    form = FormEngine.bowling_form(d, window=5)
    assert "rolling_wickets" in form.columns
    assert "rolling_economy" in form.columns


def test_form_is_chronological():
    _, d = _load()
    form = FormEngine.batting_form(d)
    babar = form[form["batter"] == "Babar Azam"].reset_index(drop=True)
    dates = babar["date"].values
    assert (dates[1:] >= dates[:-1]).all(), "Form must be chronologically ordered"


# ════════════════════════════════════════════════════════════
# VENUE ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_venue_profile():
    m, d = _load()
    profile = VenueEngine.venue_profile(d, m)
    assert "avg_score" in profile.columns
    assert "chase_win_pct" in profile.columns
    assert len(profile) == 7  # 7 normalized venues


# ════════════════════════════════════════════════════════════
# MATCHUP ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_batter_vs_bowler():
    _, d = _load()
    matchups = MatchupEngine.batter_vs_bowler(d, min_balls=12)
    assert "sr" in matchups.columns
    assert "dismissals" in matchups.columns
    assert len(matchups) > 0


def test_team_vs_team():
    m, _ = _load()
    records = MatchupEngine.team_vs_team(m)
    assert "team1_wins" in records.columns
    assert len(records) > 0


# ════════════════════════════════════════════════════════════
# TEAM ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_team_batting_strength():
    _, d = _load()
    strength = TeamEngine.team_batting_strength(d)
    assert "avg_score" in strength.columns
    assert "avg_powerplay_score" in strength.columns


def test_team_bowling_strength():
    _, d = _load()
    strength = TeamEngine.team_bowling_strength(d)
    assert "avg_conceded" in strength.columns
    assert "avg_wickets" in strength.columns


# ════════════════════════════════════════════════════════════
# TOSS ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_toss_analysis():
    m, _ = _load()
    result = TossEngine.toss_analysis(m)
    assert "overall" in result
    assert "by_decision" in result
    assert result["overall"]["total_matches"] > 0


# ════════════════════════════════════════════════════════════
# PHASE ENGINE TESTS
# ════════════════════════════════════════════════════════════

def test_phase_summary():
    _, d = _load()
    summary = PhaseEngine.phase_summary(d)
    assert len(summary) == 3  # powerplay, middle, death
    assert "rpo" in summary.columns


def test_team_phase_performance():
    _, d = _load()
    perf = PhaseEngine.team_phase_performance(d)
    assert "avg_runs" in perf.columns
    assert len(perf) > 0
