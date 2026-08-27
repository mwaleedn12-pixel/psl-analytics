"""
PSL Analytics — Central Configuration

Single source of truth for constants, paths, phase definitions,
feature names, random seeds, and thresholds.

Do NOT hard-code these values elsewhere in the project.
Import from this module instead.
"""

from pathlib import Path

# ──────────────────────────────────────────────
# Project Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJECT_ROOT / "models"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DOCS_DIR = PROJECT_ROOT / "docs"

# ──────────────────────────────────────────────
# Cricket Phase Definitions (T20)
# ──────────────────────────────────────────────
PHASES = {
    "powerplay": {"start_over": 1, "end_over": 6},
    "middle":    {"start_over": 7, "end_over": 15},
    "death":     {"start_over": 16, "end_over": 20},
}

TOTAL_OVERS = 20
BALLS_PER_OVER = 6
TOTAL_BALLS = TOTAL_OVERS * BALLS_PER_OVER  # 120
TOTAL_WICKETS = 10

# ──────────────────────────────────────────────
# Random Seeds (reproducibility)
# ──────────────────────────────────────────────
RANDOM_SEED = 42

# ──────────────────────────────────────────────
# Model Defaults
# ──────────────────────────────────────────────
TEST_SIZE = 0.2
CV_FOLDS = 5

# ──────────────────────────────────────────────
# Form Engine Defaults
# ──────────────────────────────────────────────
FORM_WINDOW_SHORT = 5   # last 5 matches
FORM_WINDOW_LONG = 10   # last 10 matches

# ──────────────────────────────────────────────
# Impact Score Weights (initial — will be tuned)
# ──────────────────────────────────────────────
IMPACT_WEIGHTS = {
    "batting": 0.40,
    "bowling": 0.40,
    "fielding": 0.10,
    "context": 0.10,
}

# ──────────────────────────────────────────────
# Dashboard Config
# ──────────────────────────────────────────────
DASHBOARD_TITLE = "PSL Analytics & Match Intelligence"
DASHBOARD_ICON = "🏏"
DASHBOARD_LAYOUT = "wide"

# ──────────────────────────────────────────────
# PSL Seasons (update as new seasons are added)
# ──────────────────────────────────────────────
PSL_SEASONS = list(range(2016, 2025))  # PSL 1 (2016) through PSL 9 (2024)

# ──────────────────────────────────────────────
# Team Name Mapping (canonical names)
# ──────────────────────────────────────────────
TEAM_NAME_MAP: dict[str, str] = {
    # Add mappings during Phase 2 — Data Cleaning
    # e.g. "Karachi King": "Karachi Kings",
}

# ──────────────────────────────────────────────
# Venue Name Mapping (canonical names)
# ──────────────────────────────────────────────
VENUE_NAME_MAP: dict[str, str] = {
    # Add mappings during Phase 2 — Data Cleaning
}
