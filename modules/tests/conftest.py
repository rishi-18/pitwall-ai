"""
Shared pytest fixtures.
"""

import pytest

from fastapi.testclient import TestClient

from modules.api.src.main import app


@pytest.fixture(scope="session")
def api_client():

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_openf1_laps():

    return [
        {
            "session_key": 9158,
            "driver_number": 1,
            "lap_number": 15,
            "lap_duration": 95.234,
            "compound": "MEDIUM",
            "stint_lap_count": 15,
            "position": 1,
        },
        {
            "session_key": 9158,
            "driver_number": 4,
            "lap_number": 15,
            "lap_duration": 95.891,
            "compound": "HARD",
            "stint_lap_count": 8,
            "position": 2,
        },
    ]


@pytest.fixture
def mock_telemetry_df():

    import pandas as pd
    import numpy as np

    from datetime import (
        datetime,
        timedelta
    )

    base_time = datetime(
        2024,
        3,
        2,
        14,
        0,
        0
    )

    n = 100

    return pd.DataFrame({
        "Date": [
            base_time + timedelta(milliseconds=i * 33)
            for i in range(n)
        ],
        "Speed": np.random.uniform(100, 320, n),
        "Throttle": np.random.uniform(0, 100, n),
        "Brake": np.random.choice([True, False], n),
        "nGear": np.random.randint(1, 9, n),
        "RPM": np.random.uniform(8000, 15000, n),
        "DRS": np.random.choice([0, 10, 12], n),
        "X": np.random.uniform(-1000, 1000, n),
        "Y": np.random.uniform(-1000, 1000, n),
        "Z": np.zeros(n),
        "driver_number": [1] * n,
    })


@pytest.fixture
def sample_pit_input():

    from shared.schemas.prediction import (
        PitStrategyInput
    )

    return PitStrategyInput(
        session_key=9158,
        driver_number=1,
        current_lap=25,
        tyre_compound="MEDIUM",
        tyre_age=15,
        gap_ahead=2.3,
        gap_behind=4.1,
        total_laps=57,
        track_temp=42.0,
        air_temp=28.0,
    )
