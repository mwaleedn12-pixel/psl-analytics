"""
PSL Analytics — Win Probability Model

Predicts the probability of the batting team winning at any point
during innings 2 of a T20 match.

CRITICAL: Only features available at that exact ball are used.
          No future data leakage.

Models:
    1. Logistic Regression (baseline)
    2. Gradient Boosting (primary)

Evaluation:
    - Log Loss (primary)
    - ROC-AUC
    - Brier Score
    - Accuracy
    - Calibration analysis

Usage:
    from src.models.win_probability import WinProbabilityModel
    wp = WinProbabilityModel()
    wp.train(deliveries_df, matches_df)
    proba = wp.predict_proba(features_df)
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    log_loss, roc_auc_score, brier_score_loss,
    accuracy_score, classification_report,
)
from sklearn.calibration import calibration_curve

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.config import RANDOM_SEED, MODELS_DIR


class WinProbabilityModel:
    """
    Win Probability prediction for innings 2 of PSL matches.

    Target: Did the batting team (chasing team) win? (1 = yes, 0 = no)

    Features (all available at prediction time):
        - cumulative_runs: Runs scored so far
        - cumulative_wickets: Wickets fallen so far
        - balls_remaining: Legal balls left
        - required_runs: Runs still needed
        - required_rr: Required run rate
        - current_rr: Current run rate
        - rr_ratio: current_rr / required_rr
        - phase_encoded: powerplay/middle/death
        - venue_encoded: Match venue
        - over: Current over number
    """

    FEATURES = [
        "cumulative_runs", "cumulative_wickets", "balls_remaining",
        "required_runs", "required_rr", "current_rr", "rr_ratio",
        "over", "phase_encoded", "venue_encoded",
    ]

    def __init__(self, model_type: str = "gradient_boosting"):
        """
        Args:
            model_type: 'logistic' for baseline, 'gradient_boosting' for primary.
        """
        self.model_type = model_type
        if model_type == "logistic":
            self.model = LogisticRegression(
                max_iter=1000, random_state=RANDOM_SEED
            )
            self.scaler = StandardScaler()
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=300,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=RANDOM_SEED,
            )
            self.scaler = None

        self.phase_encoder = LabelEncoder()
        self.venue_encoder = LabelEncoder()
        self.trained = False
        self.metrics = {}
        self.feature_importance = None

    def _prepare_training_data(
        self,
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Prepare ball-by-ball training data for innings 2 only.
        Label = did the chasing (batting) team win?
        """
        from src.features.match_features import add_match_state_features

        df = add_match_state_features(deliveries, matches)

        # Innings 2 only
        inn2 = df[df["innings"] == 2].copy()

        # Get match winner
        match_winner = matches[["match_id", "winner"]].copy()
        match_winner["match_id"] = match_winner["match_id"].astype(str)
        inn2["match_id"] = inn2["match_id"].astype(str)
        inn2 = inn2.merge(match_winner, on="match_id", how="left")

        # Target: did batting team win?
        inn2["batting_won"] = (inn2["batting_team"] == inn2["winner"]).astype(int)

        # Drop matches with no result
        inn2 = inn2[inn2["winner"].notna()].copy()

        # Drop rows with NaN in required features
        inn2 = inn2.dropna(subset=["required_runs", "required_rr", "rr_ratio"])

        return inn2

    def _encode(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        df = df.copy()
        if fit:
            df["phase_encoded"] = self.phase_encoder.fit_transform(df["phase"].astype(str))
            df["venue_encoded"] = self.venue_encoder.fit_transform(df["venue"].astype(str))
        else:
            for col, enc, new_col in [
                ("phase", self.phase_encoder, "phase_encoded"),
                ("venue", self.venue_encoder, "venue_encoded"),
            ]:
                df[new_col] = df[col].astype(str).map(
                    dict(zip(enc.classes_, enc.transform(enc.classes_)))
                ).fillna(-1).astype(int)
        return df

    def train(
        self,
        deliveries: pd.DataFrame,
        matches: pd.DataFrame,
    ) -> dict:
        """
        Train win probability model using chronological split.

        Returns evaluation metrics dict.
        """
        data = self._prepare_training_data(deliveries, matches)
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date").reset_index(drop=True)
        data = self._encode(data, fit=True)

        X = data[self.FEATURES]
        y = data["batting_won"]

        # Chronological 80/20 split
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if self.scaler:
            X_train = pd.DataFrame(
                self.scaler.fit_transform(X_train), columns=self.FEATURES
            )
            X_test = pd.DataFrame(
                self.scaler.transform(X_test), columns=self.FEATURES
            )

        self.model.fit(X_train, y_train)

        # Predictions
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        # Evaluation
        self.metrics = {
            "model_type": self.model_type,
            "log_loss": round(log_loss(y_test, y_proba), 4),
            "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
            "brier_score": round(brier_score_loss(y_test, y_proba), 4),
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "train_positive_rate": round(y_train.mean(), 4),
            "test_positive_rate": round(y_test.mean(), 4),
        }

        # Feature importance (Gradient Boosting)
        if hasattr(self.model, "feature_importances_"):
            self.feature_importance = dict(
                sorted(
                    zip(self.FEATURES, self.model.feature_importances_),
                    key=lambda x: x[1], reverse=True,
                )
            )

        # Calibration data
        prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=10)
        self.metrics["calibration"] = {
            "prob_true": prob_true.tolist(),
            "prob_pred": prob_pred.tolist(),
        }

        self.trained = True
        return self.metrics

    def predict_proba(self, deliveries: pd.DataFrame, matches: pd.DataFrame = None) -> pd.DataFrame:
        """
        Predict win probability for innings 2 deliveries.

        Returns DataFrame with added 'win_probability' column.
        """
        if not self.trained:
            raise RuntimeError("Model not trained. Call train() first.")

        if matches is not None:
            from src.features.match_features import add_match_state_features
            df = add_match_state_features(deliveries, matches)
        else:
            df = deliveries.copy()

        inn2 = df[df["innings"] == 2].copy()
        inn2 = inn2.dropna(subset=["required_runs", "required_rr", "rr_ratio"])
        inn2 = self._encode(inn2, fit=False)

        X = inn2[self.FEATURES]

        if self.scaler:
            X = pd.DataFrame(self.scaler.transform(X), columns=self.FEATURES)

        inn2["win_probability"] = self.model.predict_proba(X)[:, 1]
        inn2["win_probability"] = inn2["win_probability"].round(4)

        return inn2

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / f"win_probability_{self.model_type}.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "phase_encoder": self.phase_encoder,
            "venue_encoder": self.venue_encoder,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "model_type": self.model_type,
        }, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / f"win_probability_{self.model_type}.joblib"
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.phase_encoder = data["phase_encoder"]
        self.venue_encoder = data["venue_encoder"]
        self.metrics = data["metrics"]
        self.feature_importance = data["feature_importance"]
        self.model_type = data["model_type"]
        self.trained = True
