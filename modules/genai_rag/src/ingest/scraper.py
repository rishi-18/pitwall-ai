"""
F1 race corpus builder - uses Wikipedia summary API + manual race data.
Supplements with structured race data we already have in DB.
"""
import httpx
import json
import structlog
from pathlib import Path
from datetime import datetime

log = structlog.get_logger()
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Wikipedia policy requires a descriptive User-Agent string. 
# Replace the email with your own if you want to be completely compliant.
HEADERS = {
    "User-Agent": "F1RaceCorpusBuilder/1.0 (contact: your-email@example.com)"
}

RACES_2024 = [
    ("bahrain",   "2024_Bahrain_Grand_Prix",       1, 9158),
    ("jeddah",    "2024_Saudi_Arabian_Grand_Prix",  2, 9159),
    ("australia", "2024_Australian_Grand_Prix",     3, 9160),
]


def fetch_summary(wiki_title: str) -> str:
    """Fetch article summary via Wikipedia REST API."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
    # Pass headers to the client
    with httpx.Client(timeout=15, headers=HEADERS) as client:
        resp = client.get(url)
        if resp.status_code == 200:
            return resp.json().get("extract", "")
    return ""


def fetch_wiki_content(wiki_title: str) -> str:
    """Fetch article intro via Wikipedia action API - most reliable endpoint."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": wiki_title,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "format": "json",
    }
    # Pass headers to the client
    with httpx.Client(timeout=15, headers=HEADERS) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        pages = resp.json()["query"]["pages"]
        page = next(iter(pages.values()))
        return page.get("extract", "")


def build_race_document(slug: str, wiki_title: str, round_num: int, session_key: int) -> dict:
    """Build a rich document combining Wikipedia + structured race facts."""
    log.info("building_document", slug=slug)

    summary = fetch_summary(wiki_title)
    full_intro = fetch_wiki_content(wiki_title)

    # Race facts we know from our data
    race_facts = {
        "bahrain": {
            "winner": "Max Verstappen",
            "team": "Red Bull Racing",
            "circuit": "Bahrain International Circuit",
            "laps": 57,
            "fastest_lap_driver": "Carlos Sainz",
            "key_events": "Verstappen led from pole. Sainz finished P3 after strong pace. Leclerc P4 after tyre strategy. Alonso strong in P5.",
            "tyre_strategies": "Most drivers used Soft-Medium-Hard. Verstappen pitted laps 15 and 34. Perez used aggressive early stop.",
        },
        "jeddah": {
            "winner": "Max Verstappen",
            "team": "Red Bull Racing",
            "circuit": "Jeddah Corniche Circuit",
            "laps": 50,
            "fastest_lap_driver": "Max Verstappen",
            "key_events": "High speed street circuit. Verstappen dominant. Perez P2. Leclerc P3.",
            "tyre_strategies": "Two-stop race. Soft-Medium strategy most common on this high degradation circuit.",
        },
        "australia": {
            "winner": "Carlos Sainz",
            "team": "Ferrari",
            "circuit": "Albert Park Circuit",
            "laps": 58,
            "fastest_lap_driver": "Carlos Sainz",
            "key_events": "Verstappen retired with mechanical failure. Sainz took victory. Leclerc P2. Hamilton P3. Safety car period mid-race.",
            "tyre_strategies": "Three-stop race due to safety car. Soft tyres critical in first stint. Hamilton strong on Medium compound.",
        },
    }

    facts = race_facts.get(slug, {})

    sections = {
        "summary": summary if summary else f"2024 Formula 1 race at {facts.get('circuit', '')}",
        "race_overview": full_intro[:2000] if full_intro else "",
        "race_result": f"Winner: {facts.get('winner')} ({facts.get('team')}). Circuit: {facts.get('circuit')}. Total laps: {facts.get('laps')}.",
        "key_race_events": facts.get("key_events", ""),
        "tyre_strategy": facts.get("tyre_strategies", ""),
        "fastest_lap": f"Fastest lap set by {facts.get('fastest_lap_driver')} during the race.",
    }

    # Remove empty sections
    sections = {k: v for k, v in sections.items() if v and len(v) > 30}

    return {
        "slug": slug,
        "title": wiki_title.replace("_", " "),
        "url": f"https://en.wikipedia.org/wiki/{wiki_title}",
        "source": "wikipedia+structured",
        "round": round_num,
        "session_key": session_key,
        "scraped_at": datetime.utcnow().isoformat(),
        "sections": sections,
    }


if __name__ == "__main__":
    documents = []
    for slug, wiki_title, round_num, session_key in RACES_2024:
        try:
            doc = build_race_document(slug, wiki_title, round_num, session_key)
            documents.append(doc)
            log.info("built", slug=slug, sections=len(doc["sections"]))
        except Exception as e:
            log.error("failed", slug=slug, error=str(e))

    out = DATA_DIR / "race_reports.json"
    out.write_text(json.dumps(documents, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {len(documents)} documents")
    print(f"Total sections: {sum(len(d['sections']) for d in documents)}")
    for d in documents:
        print(f"  {d['slug']}: {list(d['sections'].keys())}")