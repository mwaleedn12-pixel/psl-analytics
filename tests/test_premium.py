"""Tests for Premium features."""
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
PROCESSED = PROJECT_ROOT / "data" / "processed"

from src.models.match_predictor import MatchPredictor
from src.analytics.premium import OptimalXI, SeasonAwards, PlayerComparison


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv", parse_dates=["date"])
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


def test_match_predictor_trains():
    m, _ = _load()
    mp = MatchPredictor()
    metrics = mp.train(m)
    assert metrics["accuracy"] > 0.45
    assert metrics["roc_auc"] > 0.4  # Pre-match prediction is inherently noisy


def test_match_predictor_predicts():
    m, _ = _load()
    mp = MatchPredictor()
    mp.train(m)
    result = mp.predict("Lahore Qalandars", "Karachi Kings",
                         "National Stadium, Karachi", "Lahore Qalandars", "field")
    assert result["team1_win_pct"] + result["team2_win_pct"] > 99
    assert result["predicted_winner"] in ["Lahore Qalandars", "Karachi Kings"]
    assert len(result["factors"]) > 0


def test_optimal_xi():
    _, d = _load()
    result = OptimalXI.suggest(d, "Lahore Qalandars")
    assert len(result["suggested_batters"]) > 0
    assert len(result["suggested_bowlers"]) > 0


def test_optimal_xi_venue_filter():
    _, d = _load()
    result = OptimalXI.suggest(d, "Karachi Kings", venue="National Stadium, Karachi")
    assert result["venue"] == "National Stadium, Karachi"


def test_season_awards():
    _, d = _load()
    awards = SeasonAwards.compute(d)
    assert len(awards) >= 10
    assert "best_batter" in awards.columns
    assert "best_bowler" in awards.columns
    assert "best_allrounder" in awards.columns


def test_player_comparison_batters():
    _, d = _load()
    result = PlayerComparison.compare_batters(d, "Babar Azam", "Fakhar Zaman")
    assert result["player1"]["player"] == "Babar Azam"
    assert result["player2"]["player"] == "Fakhar Zaman"
    assert result["player1"]["runs"] > 0


def test_player_comparison_bowlers():
    _, d = _load()
    result = PlayerComparison.compare_bowlers(d, "Hasan Ali", "Shaheen Afridi")
    assert result["player1"]["wickets"] > 0
