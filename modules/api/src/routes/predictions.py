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


@router.get("/anomalies/{session_key}")
async def get_anomalies(
    session_key: int,
    driver_number: int | None = None,
    db=Depends(get_async_db),
):
    """
    Run Isolation Forest anomaly detection on session telemetry.
    Returns flagged windows with anomaly scores per driver.
    """
    import numpy as np
    from sqlalchemy import text

    # Load model
    model_files = sorted(MODEL_DIR.glob("isolation_forest_*.joblib"))
    scaler_files = sorted(MODEL_DIR.glob("isolation_forest_scaler_*.joblib"))
    if not model_files or not scaler_files:
        raise HTTPException(status_code=503, detail="Anomaly model not trained yet")

    # Explicitly exclude scaler files from model list
    pure_model_files = [f for f in model_files if "scaler" not in f.name]
    if not pure_model_files or not scaler_files:
        raise HTTPException(status_code=503, detail="Anomaly model not trained yet")
    model = joblib.load(pure_model_files[-1])
    scaler = joblib.load(scaler_files[-1])

    # Load telemetry
    query_filter = "AND driver_number = :driver" if driver_number else ""
    params = {"key": session_key}
    if driver_number:
        params["driver"] = driver_number

    rows = await db.execute(text(f"""
        SELECT driver_number, timestamp, speed, throttle, brake, gear, rpm
        FROM telemetry
        WHERE session_key = :key {query_filter}
        ORDER BY driver_number, timestamp
        LIMIT 50000
    """), params)
    data = rows.mappings().all()

    if not data:
        return {"session_key": session_key, "anomalies": []}

    import pandas as pd
    df = pd.DataFrame([dict(r) for r in data])

    WINDOW_SIZE = 50
    results = []

    for driver_num in df["driver_number"].unique():
        driver_df = df[df["driver_number"] == driver_num].reset_index(drop=True)

        for i in range(0, len(driver_df) - WINDOW_SIZE, WINDOW_SIZE // 2):
            window = driver_df.iloc[i:i + WINDOW_SIZE]
            speed = window["speed"].dropna()
            throttle = window["throttle"].dropna()
            brake = window["brake"].dropna()
            rpm = window["rpm"].dropna()
            gear = window["gear"].dropna()

            if len(speed) < WINDOW_SIZE // 2:
                continue

            features = [[
                float(speed.mean()) if len(speed) > 0 else 0,
                float(speed.std()) if len(speed) > 1 else 0,
                float(speed.min()) if len(speed) > 0 else 0,
                float(throttle.mean()) if len(throttle) > 0 else 0,
                float(throttle.std()) if len(throttle) > 1 else 0,
                float(brake.mean()) if len(brake) > 0 else 0,
                float(rpm.mean()) if len(rpm) > 0 else 0,
                float(rpm.std()) if len(rpm) > 1 else 0,
                float(gear.mean()) if len(gear) > 0 else 0,
            ]]

            scaled = scaler.transform(features)
            score = float(model.decision_function(scaled)[0])
            is_anomaly = bool(model.predict(scaled)[0] == -1)

            if is_anomaly:
                results.append({
                    "driver_number": int(driver_num),
                    "timestamp": str(window["timestamp"].iloc[0]),
                    "anomaly_score": round(score, 4),
                    "is_anomaly": True,
                    "window_index": i,
                })

    results.sort(key=lambda x: x["anomaly_score"])
    return {
        "session_key": session_key,
        "total_anomalies": len(results),
        "anomalies": results[:50],  # return worst 50
    }