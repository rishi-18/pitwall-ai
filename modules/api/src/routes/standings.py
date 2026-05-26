"""Standings router - driver and constructor standings from Jolpica."""
from fastapi import APIRouter, Query
from modules.ingestion.src.jolpica_client import (
    get_driver_standings,
    get_constructor_standings,
    get_race_results,
    get_pit_stops,
)

router = APIRouter()


@router.get("/drivers")
async def driver_standings(
    year: int = Query(2024),
    round_number: int | None = Query(None),
):
    """Driver championship standings after a given round."""
    standings = await get_driver_standings(year, round_number)
    return {
        "year": year,
        "round": round_number,
        "standings": [
            {
                "position": s["position"],
                "driver": s["Driver"]["code"],
                "driver_id": s["Driver"]["driverId"],
                "nationality": s["Driver"]["nationality"],
                "team": s["Constructors"][0]["name"] if s["Constructors"] else None,
                "points": float(s["points"]),
                "wins": int(s["wins"]),
            }
            for s in standings
        ]
    }


@router.get("/constructors")
async def constructor_standings(
    year: int = Query(2024),
    round_number: int | None = Query(None),
):
    """Constructor championship standings."""
    standings = await get_constructor_standings(year, round_number)
    return {
        "year": year,
        "round": round_number,
        "standings": [
            {
                "position": s["position"],
                "team": s["Constructor"]["name"],
                "nationality": s["Constructor"]["nationality"],
                "points": float(s["points"]),
                "wins": int(s["wins"]),
            }
            for s in standings
        ]
    }


@router.get("/results/{round_number}")
async def race_results(
    round_number: int,
    year: int = Query(2024),
):
    """Full race results for a specific round."""
    results = await get_race_results(year, round_number)
    return {
        "year": year,
        "round": round_number,
        "results": [
            {
                "position": r["position"],
                "driver": r["Driver"]["code"],
                "team": r["Constructor"]["name"],
                "points": float(r["points"]),
                "status": r["status"],
                "fastest_lap": r.get("FastestLap", {}).get("Time", {}).get("time"),
            }
            for r in results
        ]
    }


@router.get("/pitstops/{round_number}")
async def pit_stops(
    round_number: int,
    year: int = Query(2024),
):
    """Pit stop data for a specific round - used as ML training labels."""
    pits = await get_pit_stops(year, round_number)
    return {
        "year": year,
        "round": round_number,
        "pit_stops": [
            {
                "driver_id": p["driverId"],
                "lap": int(p["lap"]),
                "stop": int(p["stop"]),
                "duration_seconds": float(p["duration"]) if p["duration"].replace('.','',1).isdigit() else None,
            }
            for p in pits
        ]
    }