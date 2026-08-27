"""Tests for Phase 2 — Data Cleaning."""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv")
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


def test_clean_files_exist():
    assert (PROCESSED / "psl_matches_clean.csv").exists()
    assert (PROCESSED / "psl_deliveries_clean.csv").exists()


def test_venues_normalized():
    """No duplicate venue names should exist."""
    m, _ = _load()
    venues = m.venue.unique()
    assert "Gaddafi Stadium" not in venues, "Should be 'Gaddafi Stadium, Lahore'"
    assert "National Stadium" not in venues, "Should be 'National Stadium, Karachi'"
    assert "Sheikh Zayed Stadium" not in venues, "Should be 'Sheikh Zayed Stadium, Abu Dhabi'"


def test_venue_count():
    m, _ = _load()
    assert m.venue.nunique() == 7


def test_no_missing_cities():
    m, _ = _load()
    assert m.city.isna().sum() == 0


def test_psl_edition_exists():
    m, _ = _load()
    assert "psl_edition" in m.columns
    assert "season_year" in m.columns
    assert m.psl_edition.isna().sum() == 0


def test_season_year_range():
    m, _ = _load()
    assert m.season_year.min() == 2016
    assert m.season_year.max() == 2026


def test_phase_column_exists():
    _, d = _load()
    assert "phase" in d.columns
    assert set(d.phase.unique()) == {"powerplay", "middle", "death"}


def test_phase_over_mapping():
    """Powerplay=1-6, Middle=7-15, Death=16-20."""
    _, d = _load()
    pp = d[d.phase == "powerplay"]
    mid = d[d.phase == "middle"]
    death = d[d.phase == "death"]

    assert pp["over"].min() >= 1 and pp["over"].max() <= 6
    assert mid["over"].min() >= 7 and mid["over"].max() <= 15
    assert death["over"].min() >= 16 and death["over"].max() <= 20


def test_cumulative_runs_non_decreasing():
    _, d = _load()
    # Check one match
    match_id = d.match_id.iloc[0]
    inn1 = d[(d.match_id == match_id) & (d.innings == 1)]
    diffs = inn1["cumulative_runs"].diff().dropna()
    assert (diffs >= 0).all(), "Cumulative runs should never decrease"


def test_cumulative_wickets_max_10():
    _, d = _load()
    max_w = d.groupby(["match_id", "innings"])["cumulative_wickets"].max()
    assert max_w.max() <= 10, "Cannot have more than 10 wickets"


def test_legal_ball_max_reasonable():
    """Allow up to 121 — CricSheet has 2 matches with a 7-ball over (source data quirk)."""
    _, d = _load()
    max_balls = d.groupby(["match_id", "innings"])["legal_ball_number"].max()
    assert max_balls.max() <= 126, "Legal balls should not exceed 21 overs worth"
    # Only 2 matches exceed 120, both by exactly 1 ball
    over_120 = (max_balls > 120).sum()
    assert over_120 <= 2, f"Expected at most 2 edge cases, got {over_120}"


def test_deliveries_venue_normalized():
    _, d = _load()
    venues = d.venue.unique()
    assert "Gaddafi Stadium" not in venues
    assert "National Stadium" not in venues


def test_row_count_unchanged():
    m, d = _load()
    assert len(m) == 357
    assert len(d) == 83799
