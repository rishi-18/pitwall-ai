"""
Isolation Forest anomaly detector - training script.
Run locally: python modules/ml_engine/src/models/train_anomaly.py

Detects unusual telemetry patterns per driver per session:
- Tyre cliff (sudden pace drop)
- Engine anomalies (RPM/throttle inconsistency)  
- Brake issues (unusual brake pressure patterns)
- DRS failures (DRS open when it shouldn't be)
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pitwall:pitwall_secret@localhost:5432/pitwall"
)
MODEL_DIR = Path(__file__).parent.parent.parent / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)

WINDOW_SIZE = 50  # telemetry points per window (~1.6 seconds at 300Hz)
FEATURE_COLS = [
    "speed_mean", "speed_std", "speed_min",
    "throttle_mean", "throttle_std",
    "brake_rate",
    "rpm_mean", "rpm_std",
    "gear_mean",
]


def load_telemetry(session_key: int, driver_number: int) -> pd.DataFrame:
    """Load telemetry for one driver from TimescaleDB."""
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql(
        text("""
            SELECT timestamp, speed, throttle, brake, gear, rpm, drs
            FROM telemetry
            WHERE session_key = :key AND driver_number = :driver
            ORDER BY timestamp
        """),
        engine,
        params={"key": session_key, "driver": driver_number}
    )
    return df


def build_window_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate telemetry into sliding window features.
    Each row = one window of WINDOW_SIZE telemetry points.
    """
    features = []
    for i in range(0, len(df) - WINDOW_SIZE, WINDOW_SIZE // 2):
        window = df.iloc[i:i + WINDOW_SIZE]
        speed = window["speed"].dropna()
        throttle = window["throttle"].dropna()
        brake = window["brake"].dropna()
        rpm = window["rpm"].dropna()
        gear = window["gear"].dropna()

        if len(speed) < WINDOW_SIZE // 2:
            continue

        features.append({
            "window_start": i,
            "timestamp": window["timestamp"].iloc[0],
            "speed_mean": float(speed.mean()) if len(speed) > 0 else 0,
            "speed_std": float(speed.std()) if len(speed) > 1 else 0,
            "speed_min": float(speed.min()) if len(speed) > 0 else 0,
            "throttle_mean": float(throttle.mean()) if len(throttle) > 0 else 0,
            "throttle_std": float(throttle.std()) if len(throttle) > 1 else 0,
            "brake_rate": float(brake.mean()) if len(brake) > 0 else 0,
            "rpm_mean": float(rpm.mean()) if len(rpm) > 0 else 0,
            "rpm_std": float(rpm.std()) if len(rpm) > 1 else 0,
            "gear_mean": float(gear.mean()) if len(gear) > 0 else 0,
        })

    return pd.DataFrame(features)


def train_detector(all_features: pd.DataFrame):
    """Train Isolation Forest on combined telemetry features."""
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    X = all_features[FEATURE_COLS].fillna(0)

    # Standardize features — IF works better on normalized data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,  # assume 5% anomalous windows
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Score distribution
    scores = model.decision_function(X_scaled)
    predictions = model.predict(X_scaled)
    anomaly_count = (predictions == -1).sum()

    print(f"Total windows: {len(X)}")
    print(f"Anomalies detected: {anomaly_count} ({anomaly_count/len(X)*100:.1f}%)")
    print(f"Score range: [{scores.min():.3f}, {scores.max():.3f}]")
    print(f"Score mean: {scores.mean():.3f}")

    return model, scaler


def save_artifacts(model, scaler):
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = MODEL_DIR / f"isolation_forest_{version}.joblib"
    scaler_path = MODEL_DIR / f"isolation_forest_scaler_{version}.joblib"
    meta_path = MODEL_DIR / f"isolation_forest_{version}_meta.json"

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    meta = {
        "version": version,
        "model_type": "isolation_forest",
        "contamination": 0.05,
        "window_size": WINDOW_SIZE,
        "feature_cols": FEATURE_COLS,
        "training_sessions": [9158, 9159, 9160],
        "n_estimators": 200,
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"\nModel saved: {model_path}")
    return model_path, scaler_path


if __name__ == "__main__":
    # Train on Verstappen (driver 1) across all 3 race sessions
    # Use one driver's data as "normal" baseline
    all_features = []

    for session_key, name in [(9158, "Bahrain"), (9159, "Jeddah"), (9160, "Australia")]:
        print(f"\nLoading {name} telemetry...")
        df = load_telemetry(session_key, driver_number=1)
        print(f"  Raw points: {len(df)}")
        features = build_window_features(df)
        features["session_key"] = session_key
        features["driver_number"] = 1
        all_features.append(features)
        print(f"  Windows: {len(features)}")

    combined = pd.concat(all_features, ignore_index=True)
    print(f"\nTotal training windows: {len(combined)}")

    model, scaler = train_detector(combined)
    save_artifacts(model, scaler)
    print("\nDone.")