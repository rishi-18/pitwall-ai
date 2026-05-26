"""
Jolpica API client - replaces Ergast (shut down end of 2024).
Pulls race results, standings, and pit stop data.
Identical endpoint structure to Ergast.
"""
import httpx
import structlog
from typing import Optional

log = structlog.get_logger()
BASE_URL = "https://api.jolpi.ca/ergast/f1"


async def get_race_results(year: int, round_number: int) -> list[dict]:
    """Fetch finishing positions, points, status for all drivers."""
    url = f"{BASE_URL}/{year}/{round_number}/results.json"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            return []
        return races[0]["Results"]


async def get_pit_stops(year: int, round_number: int) -> list[dict]:
    """
    Fetch pit stop summary - lap number, duration, stop number per driver.
    Critical for XGBoost training labels - ground truth of when drivers pitted.
    """
    url = f"{BASE_URL}/{year}/{round_number}/pitstops.json?limit=100"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            return []
        return races[0].get("PitStops", [])


async def get_driver_standings(year: int, round_number: Optional[int] = None) -> list[dict]:
    """Fetch driver championship standings after a given round."""
    if round_number:
        url = f"{BASE_URL}/{year}/{round_number}/driverStandings.json"
    else:
        url = f"{BASE_URL}/{year}/driverStandings.json"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not lists:
            return []
        return lists[0]["DriverStandings"]


async def get_constructor_standings(year: int, round_number: Optional[int] = None) -> list[dict]:
    """Fetch constructor championship standings after a given round."""
    if round_number:
        url = f"{BASE_URL}/{year}/{round_number}/constructorStandings.json"
    else:
        url = f"{BASE_URL}/{year}/constructorStandings.json"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not lists:
            return []
        return lists[0]["ConstructorStandings"]