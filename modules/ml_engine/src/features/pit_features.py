import pandas as pd
import numpy as np


def build_pit_features(
    laps_df: pd.DataFrame
) -> pd.DataFrame:

    df = laps_df.copy()

    df = df.sort_values(
        ["driver_number", "lap_number"]
    )

    df["tyre_deg_rolling"] = (
        df.groupby(
            ["driver_number", "compound"]
        )["lap_duration"]
        .transform(
            lambda x: x.diff()
            .rolling(3, min_periods=1)
            .mean()
        )
    )

    df["laps_remaining"] = (
        df["total_laps"]
        - df["lap_number"]
    )

    df["stint_lap"] = (
        df.groupby(
            ["driver_number", "stint_number"]
        ).cumcount() + 1
    )

    df["gap_ahead_delta"] = (
        df.groupby("driver_number")
        ["gap_ahead"]
        .diff()
    )

    df["undercut_threat"] = (
        df["gap_behind"] < 2.0
    ).astype(int)

    feature_cols = [
        "lap_number",
        "tyre_age_laps",
        "stint_lap",
        "tyre_deg_rolling",
        "gap_ahead",
        "gap_behind",
        "gap_ahead_delta",
        "undercut_threat",
        "laps_remaining",
        "track_temp",
        "air_temp",
        "sector1_duration",
        "sector2_duration",
        "sector3_duration",
        "circuit_key",
    ]

    return df[feature_cols].fillna(0)
