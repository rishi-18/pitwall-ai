"""
Data quality and schema drift checks.
"""

import json
import httpx
import structlog

from pathlib import Path

log = structlog.get_logger()

SCHEMA_BASELINE_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "schema_baseline.json"
)


def run_drift_check():
    resp = httpx.get(
        "https://api.openf1.org/v1/laps?session_key=latest&limit=1"
    )

    if resp.status_code != 200:
        log.error(
            "drift_check_api_failed",
            status=resp.status_code
        )

        return False

    current_keys = (
        set(resp.json()[0].keys())
        if resp.json()
        else set()
    )

    if not SCHEMA_BASELINE_PATH.exists():
        SCHEMA_BASELINE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        SCHEMA_BASELINE_PATH.write_text(
            json.dumps(sorted(current_keys))
        )

        log.info("schema_baseline_saved")

        return True

    baseline_keys = set(
        json.loads(
            SCHEMA_BASELINE_PATH.read_text()
        )
    )

    added = current_keys - baseline_keys
    removed = baseline_keys - current_keys

    if added or removed:
        log.warning(
            "schema_drift_detected",
            added=list(added),
            removed=list(removed)
        )

        return False

    log.info(
        "schema_drift_check_passed"
    )

    return True
