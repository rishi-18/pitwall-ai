"""
Unit tests for telemetry normalization.
"""

from modules.ingestion.src.normalizer import (
    normalize_fastf1_telemetry
)


def test_normalize_valid_telemetry(
    mock_telemetry_df
):

    records = normalize_fastf1_telemetry(
        mock_telemetry_df,
        session_key=9158
    )

    assert len(records) == 100

    assert all(
        r.session_key == 9158
        for r in records
    )

    assert all(
        r.driver_number == 1
        for r in records
    )


def test_normalize_drops_invalid_rows():

    import pandas as pd

    df = pd.DataFrame({
        "Date": [None],
        "Speed": [100],
        "driver_number": [1],
    })

    records = normalize_fastf1_telemetry(
        df,
        session_key=1
    )

    assert len(records) == 0
