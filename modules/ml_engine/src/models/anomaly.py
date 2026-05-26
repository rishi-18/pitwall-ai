import numpy as np
import pandas as pd
import joblib

from pathlib import Path

from sklearn.ensemble import (
    IsolationForest
)

from shared.schemas.prediction import (
    AnomalyResult
)

MODEL_DIR = (
    Path(__file__).parent.parent.parent
    / "artifacts"
)

WINDOW_SIZE = 10

CONTAMINATION = 0.05

FEATURE_COLS = [
    "speed_mean",
    "speed_std",
    "throttle_mean",
    "brake_rate",
    "rpm_mean",
]


def build_window_features(
    telemetry_df: pd.DataFrame
):

    return telemetry_df.groupby(
        "lap_number"
    ).agg(
        speed_mean=("speed", "mean"),
        speed_std=("speed", "std"),
        throttle_mean=("throttle", "mean"),
        brake_rate=("brake", "mean"),
        rpm_mean=("rpm", "mean"),
    ).fillna(0)


class TelemetryAnomalyDetector:

    def __init__(self):

        self.model = IsolationForest(
            contamination=CONTAMINATION,
            random_state=42,
            n_jobs=-1,
        )

    def fit(
        self,
        telemetry_df: pd.DataFrame
    ):

        features = build_window_features(
            telemetry_df
        )

        self.model.fit(
            features[FEATURE_COLS]
        )

    def detect(
        self,
        telemetry_df: pd.DataFrame,
        session_key: int,
        driver_number: int
    ):

        features = build_window_features(
            telemetry_df
        )

        scores = self.model.decision_function(
            features[FEATURE_COLS]
        )

        predictions = self.model.predict(
            features[FEATURE_COLS]
        )

        results = []

        for lap_num, (score, pred) in enumerate(
            zip(scores, predictions),
            start=1
        ):

            results.append(
                AnomalyResult(
                    session_key=session_key,
                    driver_number=driver_number,
                    lap_number=lap_num,
                    anomaly_score=float(score),
                    is_anomaly=bool(pred == -1),
                    anomalous_channels=[],
                )
            )

        return results
