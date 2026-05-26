import asyncio
import sys
sys.path.insert(0, '/app')

from modules.ingestion.src.jolpica_client import get_race_results, get_pit_stops

async def test():
    print('Fetching Bahrain 2024 results...')
    results = await get_race_results(2024, 1)
    for r in results[:5]:
        print(f"P{r['position']} {r['Driver']['code']} - {r['points']} pts - {r['status']}")

    print()
    print('Fetching pit stops...')
    pits = await get_pit_stops(2024, 1)
    for p in pits[:5]:
        print(f"{p['driverId']} lap {p['lap']} stop {p['stop']} duration {p['duration']}")

asyncio.run(test())