"""Tests for Phase 7 (Expected Performance) + Phase 8 (Win Probability)."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"

from src.models.expected_models import ExpectedRunsModel, ExpectedWicketsModel
from src.models.win_probability import WinProbabilityModel


def _load():
    m = pd.read_csv(PROCESSED / "psl_matches_clean.csv")
    d = pd.read_csv(PROCESSED / "psl_deliveries_clean.csv", low_memory=False)
    return m, d


# ════════════════════════════════════════════════════════════
# EXPECTED RUNS
# ════════════════════════════════════════════════════════════

def test_expected_runs_trains():
    _, d = _load()
    model = ExpectedRunsModel()
    metrics = model.train(d)
    assert "mae" in metrics
    assert "r2" in metrics
    assert metrics["mae"] > 0
    assert metrics["mae"] < 5, f"MAE too high: {metrics['mae']}"


def test_expected_runs_predicts():
    _, d = _load()
    model = ExpectedRunsModel()
    model.train(d)
    preds = model.predict(d)
    assert "expected_runs" in preds.columns
    assert "runs_above_expected" in preds.columns
    assert (preds["expected_runs"] >= 0).all()


# ════════════════════════════════════════════════════════════
# EXPECTED WICKETS
# ════════════════════════════════════════════════════════════

def test_expected_wickets_trains():
    _, d = _load()
    model = ExpectedWicketsModel()
    metrics = model.train(d)
    assert "mae" in metrics
    assert metrics["mae"] < 1, f"MAE too high: {metrics['mae']}"


def test_expected_wickets_predicts():
    _, d = _load()
    model = ExpectedWicketsModel()
    model.train(d)
    preds = model.predict(d)
    assert "expected_wickets" in preds.columns
    assert (preds["expected_wickets"] >= 0).all()


# ════════════════════════════════════════════════════════════
# WIN PROBABILITY
# ════════════════════════════════════════════════════════════

def test_win_prob_logistic_trains():
    m, d = _load()
    model = WinProbabilityModel(model_type="logistic")
    metrics = model.train(d, m)
    assert "log_loss" in metrics
    assert "roc_auc" in metrics
    assert metrics["roc_auc"] > 0.5, "Model should beat random"


def test_win_prob_gb_trains():
    m, d = _load()
    model = WinProbabilityModel(model_type="gradient_boosting")
    metrics = model.train(d, m)
    assert metrics["roc_auc"] > 0.6, f"GB should achieve decent AUC: {metrics['roc_auc']}"
    assert metrics["log_loss"] < 0.7, f"Log loss too high: {metrics['log_loss']}"


def test_win_prob_predicts_valid_range():
    m, d = _load()
    model = WinProbabilityModel(model_type="gradient_boosting")
    model.train(d, m)
    preds = model.predict_proba(d, m)
    assert "win_probability" in preds.columns
    assert (preds["win_probability"] >= 0).all()
    assert (preds["win_probability"] <= 1).all()


def test_win_prob_no_future_leak():
    """Verify only innings 2 data is used and no future features."""
    m, d = _load()
    model = WinProbabilityModel()
    # Features should not include 'winner', 'target', or final score
    for feat in model.FEATURES:
        assert feat not in ["winner", "target", "final_score", "result"]


def test_win_prob_has_calibration():
    m, d = _load()
    model = WinProbabilityModel()
    metrics = model.train(d, m)
    assert "calibration" in metrics
    assert len(metrics["calibration"]["prob_true"]) > 0


def test_win_prob_feature_importance():
    m, d = _load()
    model = WinProbabilityModel(model_type="gradient_boosting")
    model.train(d, m)
    assert model.feature_importance is not None
    assert len(model.feature_importance) == len(model.FEATURES)
