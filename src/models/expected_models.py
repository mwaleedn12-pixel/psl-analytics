"""
PSL Analytics — Expected Performance Models

Expected Runs:   How many runs SHOULD a batter score given the context?
Expected Wickets: How many wickets SHOULD a bowler take given the context?

Actual - Expected = Value Above Expected (positive = outperformed)

Features used (no future data leakage):
    - phase, over, venue, batting_team, bowling_team
    - wickets_fallen (so far), current_rr, balls_remaining

Usage:
    from src.models.expected_models import ExpectedRunsModel, ExpectedWicketsModel
    er = ExpectedRunsModel()
    er.train(deliveries_df)
    predictions = er.predict(deliveries_df)
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.config import RANDOM_SEED, MODELS_DIR, CV_FOLDS


class ExpectedRunsModel:
    """
    Expected Runs per over — predicts how many runs should be scored
    in a given over based on match context.

    Purpose:  Identify batters/bowlers who over/under-perform expectations.
    Method:   GradientBoostingRegressor on contextual features.
    Output:   expected_runs, actual_runs, runs_above_expected
    """

    FEATURES = [
        "over", "innings", "cumulative_wickets", "current_rr",
        "balls_remaining", "phase_encoded", "venue_encoded",
        "batting_team_encoded", "bowling_team_encoded",
    ]

    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=RANDOM_SEED,
        )
        self.venue_encoder = LabelEncoder()
        self.bat_team_encoder = LabelEncoder()
        self.bowl_team_encoder = LabelEncoder()
        self.phase_encoder = LabelEncoder()
        self.trained = False
        self.metrics = {}

    def _prepare_over_data(self, deliveries: pd.DataFrame) -> pd.DataFrame:
        """Aggregate deliveries to per-over level and encode features."""
        from src.features.match_features import add_match_state_features

        df = deliveries.copy()
        # Add match state features if not present
        if "current_rr" not in df.columns:
            df = add_match_state_features(df)

        # Per-over aggregation
        over_data = df.groupby(["match_id", "innings", "over", "venue",
                                 "batting_team", "bowling_team", "phase"]).agg(
            actual_runs=("total_runs", "sum"),
            cumulative_wickets=("cumulative_wickets", "max"),
            current_rr=("current_rr", "last"),
            balls_remaining=("balls_remaining", "min"),
            date=("date", "first"),
        ).reset_index()

        return over_data

    def _encode(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Encode categorical features."""
        df = df.copy()
        if fit:
            df["venue_encoded"] = self.venue_encoder.fit_transform(df["venue"].astype(str))
            df["batting_team_encoded"] = self.bat_team_encoder.fit_transform(df["batting_team"].astype(str))
            df["bowling_team_encoded"] = self.bowl_team_encoder.fit_transform(df["bowling_team"].astype(str))
            df["phase_encoded"] = self.phase_encoder.fit_transform(df["phase"].astype(str))
        else:
            # Handle unseen labels
            for col, enc, new_col in [
                ("venue", self.venue_encoder, "venue_encoded"),
                ("batting_team", self.bat_team_encoder, "batting_team_encoded"),
                ("bowling_team", self.bowl_team_encoder, "bowling_team_encoded"),
                ("phase", self.phase_encoder, "phase_encoded"),
            ]:
                df[new_col] = df[col].astype(str).map(
                    dict(zip(enc.classes_, enc.transform(enc.classes_)))
                ).fillna(-1).astype(int)
        return df

    def train(self, deliveries: pd.DataFrame) -> dict:
        """
        Train the Expected Runs model using chronological split.

        Returns evaluation metrics.
        """
        over_data = self._prepare_over_data(deliveries)
        over_data = over_data.sort_values("date").reset_index(drop=True)
        over_data = self._encode(over_data, fit=True)

        X = over_data[self.FEATURES]
        y = over_data["actual_runs"]

        # Chronological split (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        self.metrics = {
            "mae": round(mean_absolute_error(y_test, y_pred), 3),
            "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 3),
            "r2": round(r2_score(y_test, y_pred), 3),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        self.trained = True
        return self.metrics

    def predict(self, deliveries: pd.DataFrame) -> pd.DataFrame:
        """Predict expected runs per over and compute runs above expected."""
        if not self.trained:
            raise RuntimeError("Model not trained. Call train() first.")

        over_data = self._prepare_over_data(deliveries)
        over_data = self._encode(over_data, fit=False)

        X = over_data[self.FEATURES]
        over_data["expected_runs"] = np.clip(self.model.predict(X), 0, None).round(2)
        over_data["runs_above_expected"] = (
            over_data["actual_runs"] - over_data["expected_runs"]
        ).round(2)

        return over_data

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / "expected_runs.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "encoders": {
            "venue": self.venue_encoder,
            "bat_team": self.bat_team_encoder,
            "bowl_team": self.bowl_team_encoder,
            "phase": self.phase_encoder,
        }, "metrics": self.metrics}, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / "expected_runs.joblib"
        data = joblib.load(path)
        self.model = data["model"]
        self.venue_encoder = data["encoders"]["venue"]
        self.bat_team_encoder = data["encoders"]["bat_team"]
        self.bowl_team_encoder = data["encoders"]["bowl_team"]
        self.phase_encoder = data["encoders"]["phase"]
        self.metrics = data["metrics"]
        self.trained = True


class ExpectedWicketsModel:
    """
    Expected Wickets per over — predicts how many wickets should fall
    in a given over based on match context.

    Purpose:  Identify bowlers who outperform wicket expectations.
    Method:   GradientBoostingRegressor on contextual features.
    Output:   expected_wickets, actual_wickets, wickets_above_expected
    """

    FEATURES = [
        "over", "innings", "cumulative_wickets", "current_rr",
        "balls_remaining", "phase_encoded", "venue_encoded",
        "batting_team_encoded", "bowling_team_encoded",
    ]

    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            random_state=RANDOM_SEED,
        )
        self.venue_encoder = LabelEncoder()
        self.bat_team_encoder = LabelEncoder()
        self.bowl_team_encoder = LabelEncoder()
        self.phase_encoder = LabelEncoder()
        self.trained = False
        self.metrics = {}

    def _prepare_over_data(self, deliveries: pd.DataFrame) -> pd.DataFrame:
        from src.features.match_features import add_match_state_features

        df = deliveries.copy()
        if "current_rr" not in df.columns:
            df = add_match_state_features(df)

        over_data = df.groupby(["match_id", "innings", "over", "venue",
                                 "batting_team", "bowling_team", "phase"]).agg(
            actual_wickets=("is_wicket", "sum"),
            cumulative_wickets=("cumulative_wickets", "first"),
            current_rr=("current_rr", "first"),
            balls_remaining=("balls_remaining", "max"),
            date=("date", "first"),
        ).reset_index()
        return over_data

    def _encode(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        df = df.copy()
        if fit:
            df["venue_encoded"] = self.venue_encoder.fit_transform(df["venue"].astype(str))
            df["batting_team_encoded"] = self.bat_team_encoder.fit_transform(df["batting_team"].astype(str))
            df["bowling_team_encoded"] = self.bowl_team_encoder.fit_transform(df["bowling_team"].astype(str))
            df["phase_encoded"] = self.phase_encoder.fit_transform(df["phase"].astype(str))
        else:
            for col, enc, new_col in [
                ("venue", self.venue_encoder, "venue_encoded"),
                ("batting_team", self.bat_team_encoder, "batting_team_encoded"),
                ("bowling_team", self.bowl_team_encoder, "bowling_team_encoded"),
                ("phase", self.phase_encoder, "phase_encoded"),
            ]:
                df[new_col] = df[col].astype(str).map(
                    dict(zip(enc.classes_, enc.transform(enc.classes_)))
                ).fillna(-1).astype(int)
        return df

    def train(self, deliveries: pd.DataFrame) -> dict:
        over_data = self._prepare_over_data(deliveries)
        over_data = over_data.sort_values("date").reset_index(drop=True)
        over_data = self._encode(over_data, fit=True)

        X = over_data[self.FEATURES]
        y = over_data["actual_wickets"]

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        self.metrics = {
            "mae": round(mean_absolute_error(y_test, y_pred), 3),
            "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 3),
            "r2": round(r2_score(y_test, y_pred), 3),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        self.trained = True
        return self.metrics

    def predict(self, deliveries: pd.DataFrame) -> pd.DataFrame:
        if not self.trained:
            raise RuntimeError("Model not trained. Call train() first.")

        over_data = self._prepare_over_data(deliveries)
        over_data = self._encode(over_data, fit=False)

        X = over_data[self.FEATURES]
        over_data["expected_wickets"] = np.clip(self.model.predict(X), 0, None).round(3)
        over_data["wickets_above_expected"] = (
            over_data["actual_wickets"] - over_data["expected_wickets"]
        ).round(3)

        return over_data

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / "expected_wickets.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "encoders": {
            "venue": self.venue_encoder,
            "bat_team": self.bat_team_encoder,
            "bowl_team": self.bowl_team_encoder,
            "phase": self.phase_encoder,
        }, "metrics": self.metrics}, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / "expected_wickets.joblib"
        data = joblib.load(path)
        self.model = data["model"]
        self.venue_encoder = data["encoders"]["venue"]
        self.bat_team_encoder = data["encoders"]["bat_team"]
        self.bowl_team_encoder = data["encoders"]["bowl_team"]
        self.phase_encoder = data["encoders"]["phase"]
        self.metrics = data["metrics"]
        self.trained = True
