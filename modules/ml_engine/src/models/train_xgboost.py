"""
XGBoost pit strategy model - training script.
Run locally: python modules/ml_engine/src/models/train_xgboost.py

Training data: lap data from TimescaleDB (3 races - Bahrain, Jeddah, Australia)
Labels: actual pit stop laps from Jolpica
Target: predict whether a driver should pit on the current lap (binary classification)
        and which lap is optimal (regression)
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pitwall:pitwall_secret@localhost:5432/pitwall"
)

MODEL_DIR = Path(__file__).parent.parent.parent / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)


def load_training_data() -> pd.DataFrame:
    """Load lap data from TimescaleDB for all ingested sessions."""
    engine = create_engine(DATABASE_URL)
    print("Connecting to TimescaleDB...")

    query = """
        SELECT
            l.session_key,
            l.driver_number,
            l.lap_number,
            l.lap_duration,
            l.sector1_duration,
            l.sector2_duration,
            l.sector3_duration,
            l.compound,
            l.tyre_age_laps,
            l.is_pit_out_lap
        FROM laps l
        WHERE l.lap_duration IS NOT NULL
        AND l.tyre_age_laps IS NOT NULL
        ORDER BY l.session_key, l.driver_number, l.lap_number
    """

    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} laps from {df['session_key'].nunique()} sessions")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build feature matrix from raw lap data."""
    df = df.copy()
    df = df.sort_values(['session_key', 'driver_number', 'lap_number'])

    # Tyre degradation - rolling pace drop on same stint
    df['lap_duration_rolling_mean'] = (
        df.groupby(['session_key', 'driver_number'])['lap_duration']
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )
    df['pace_drop'] = df['lap_duration'] - df['lap_duration_rolling_mean']

    # Compound encoding
    compound_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2, 'INTERMEDIATE': 3, 'WET': 4}
    df['compound_encoded'] = df['compound'].map(compound_map).fillna(1)

    # Session total laps (approximate from max lap per session/driver)
    session_laps = df.groupby(['session_key'])['lap_number'].max().reset_index()
    session_laps.columns = ['session_key', 'total_laps']
    df = df.merge(session_laps, on='session_key', how='left')
    df['laps_remaining'] = df['total_laps'] - df['lap_number']
    df['race_progress'] = df['lap_number'] / df['total_laps']

    # Lap number within stint
    df['stint_lap'] = df.groupby(
        ['session_key', 'driver_number',
         (df['is_pit_out_lap']).cumsum()]
    ).cumcount() + 1

    # Label: will this driver pit in the next 3 laps?
    df['pitted_next_3'] = (
        df.groupby(['session_key', 'driver_number'])['is_pit_out_lap']
        .transform(lambda x: x.shift(-1).fillna(False) |
                              x.shift(-2).fillna(False) |
                              x.shift(-3).fillna(False))
    ).astype(int)

    return df


def train_model(df: pd.DataFrame):
    """Train XGBoost classifier - predicts if driver should pit in next 3 laps."""
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, roc_auc_score

    feature_cols = [
        'lap_number', 'tyre_age_laps', 'stint_lap',
        'compound_encoded', 'lap_duration', 'pace_drop',
        'sector1_duration', 'sector2_duration', 'sector3_duration',
        'laps_remaining', 'race_progress',
    ]

    df_clean = df[feature_cols + ['pitted_next_3']].dropna()
    print(f"\nTraining on {len(df_clean)} laps")
    print(f"Pit rate: {df_clean['pitted_next_3'].mean():.1%}")

    X = df_clean[feature_cols]
    y = df_clean['pitted_next_3']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Class weight for imbalanced labels (most laps don't have pits)
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        eval_metric='auc',
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    print(f"\nAUC-ROC: {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Pit', 'Pit Soon']))

    # Feature importance
    importance = dict(zip(feature_cols, model.feature_importances_))
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print("\nTop Feature Importances:")
    for feat, imp in importance_sorted[:5]:
        print(f"  {feat}: {imp:.4f}")

    return model, feature_cols, auc


def save_model(model, feature_cols: list, auc: float):
    """Save model artifact with metadata."""
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = MODEL_DIR / f"xgb_pit_strategy_{version}.joblib"
    meta_path = MODEL_DIR / f"xgb_pit_strategy_{version}_meta.json"

    joblib.dump(model, model_path)

    meta = {
        "version": version,
        "model_type": "xgboost_pit_classifier",
        "auc_roc": round(auc, 4),
        "feature_cols": feature_cols,
        "training_sessions": [9157, 9158, 9159, 9160],
        "target": "pitted_next_3_laps",
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"\nModel saved: {model_path}")
    print(f"Metadata: {meta_path}")
    return model_path


if __name__ == "__main__":
    df = load_training_data()
    df = engineer_features(df)
    model, feature_cols, auc = train_model(df)
    save_model(model, feature_cols, auc)
    print("\nDone.")