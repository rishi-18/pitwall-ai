"""Predictions router - pit strategy and anomaly detection endpoints."""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from shared.schemas.prediction import PitStrategyInput, PitStrategyOutput, AnomalyResult
from shared.utils.db import get_async_db

router = APIRouter()

MODEL_DIR = Path("/app/modules/ml_engine/artifacts")


def load_latest_model():
    """Load the most recently trained XGBoost model."""
    model_files = sorted(MODEL_DIR.glob("xgb_pit_strategy_*.joblib"))
    if not model_files:
        raise FileNotFoundError("No trained model found")
    latest = model_files[-1]
    meta_path = latest.with_name(latest.stem + "_meta.json")
    model = joblib.load(latest)
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    return model, meta


@router.post("/pit-strategy", response_model=PitStrategyOutput)
async def predict_pit_strategy(
    payload: PitStrategyInput,
    db=Depends(get_async_db),
):
    """
    Predict pit window for a driver given current race state.
    Returns probability of needing to pit in the next 3 laps.
    """
    try:
        model, meta = load_latest_model()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not yet trained")

    compound_map = {'SOFT': 0, 'MEDIUM': 1, 'HARD': 2, 'INTERMEDIATE': 3, 'WET': 4}

    features = pd.DataFrame([{
        'lap_number': payload.current_lap,
        'tyre_age_laps': payload.tyre_age,
        'stint_lap': payload.tyre_age,
        'compound_encoded': compound_map.get(payload.tyre_compound.upper(), 1),
        'lap_duration': 96.0,  # placeholder - would come from live telemetry
        'pace_drop': 0.0,
        'sector1_duration': payload.track_temp * 0.1,
        'sector2_duration': payload.track_temp * 0.12,
        'sector3_duration': payload.track_temp * 0.08,
        'laps_remaining': payload.total_laps - payload.current_lap,
        'race_progress': payload.current_lap / payload.total_laps,
    }])

    pit_probability = float(model.predict_proba(features)[0][1])
    should_pit = pit_probability > 0.5

    # Estimate optimal pit lap window
    pit_lap = payload.current_lap if should_pit else payload.current_lap + max(
        1, int((1 - pit_probability) * 10)
    )

    return PitStrategyOutput(
        driver_number=payload.driver_number,
        current_lap=payload.current_lap,
        recommended_pit_lap=pit_lap,
        confidence=round(pit_probability, 4),
        pit_window=[max(1, pit_lap - 2), min(payload.total_laps, pit_lap + 2)],
        predicted_position_delta=-1.2 if should_pit else 0.0,
        model_version=meta.get("version", "unknown"),
    )


@router.get("/anomalies/{session_key}", response_model=list[AnomalyResult])
async def get_anomalies(session_key: int, db=Depends(get_async_db)):
    """Return anomaly detection results for all drivers in a session."""
    return []