"""Tests for src/config.py — verify constants and paths."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    PHASES,
    TOTAL_OVERS,
    BALLS_PER_OVER,
    TOTAL_BALLS,
    TOTAL_WICKETS,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    RANDOM_SEED,
    IMPACT_WEIGHTS,
)


def test_phase_definitions():
    """Powerplay 1-6, Middle 7-15, Death 16-20."""
    assert PHASES["powerplay"] == {"start_over": 1, "end_over": 6}
    assert PHASES["middle"] == {"start_over": 7, "end_over": 15}
    assert PHASES["death"] == {"start_over": 16, "end_over": 20}


def test_t20_constants():
    assert TOTAL_OVERS == 20
    assert BALLS_PER_OVER == 6
    assert TOTAL_BALLS == 120
    assert TOTAL_WICKETS == 10


def test_paths_exist_as_path_objects():
    assert isinstance(RAW_DATA_DIR, Path)
    assert isinstance(PROCESSED_DATA_DIR, Path)


def test_random_seed_is_set():
    assert isinstance(RANDOM_SEED, int)


def test_impact_weights_sum_to_one():
    total = sum(IMPACT_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Impact weights sum to {total}, expected 1.0"
