"""F1 domain constants ï¿½ single source of truth across all modules."""

TYRE_COMPOUNDS = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]

DRIVER_CODES = {
    "VER": "Max Verstappen", "PER": "Sergio Perez",
    "LEC": "Charles Leclerc", "SAI": "Carlos Sainz",
    "HAM": "Lewis Hamilton",  "RUS": "George Russell",
    "NOR": "Lando Norris",    "PIA": "Oscar Piastri",
    "ALO": "Fernando Alonso", "STR": "Lance Stroll",
    "GAS": "Pierre Gasly",    "OCO": "Esteban Ocon",
    "TSU": "Yuki Tsunoda",    "ALB": "Alexander Albon",
    "BOT": "Valtteri Bottas", "ZHO": "Guanyu Zhou",
    "MAG": "Kevin Magnussen", "HUL": "Nico Hulkenberg",
}

TEAMS = [
    "Red Bull Racing", "Ferrari", "Mercedes", "McLaren",
    "Aston Martin", "Alpine", "RB", "Williams", "Sauber", "Haas F1 Team",
]

POINTS_SYSTEM = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8,  7: 6,  8: 4,  9: 2,  10: 1,
}

FASTEST_LAP_POINT = 1

SESSION_TYPES = ["FP1", "FP2", "FP3", "Q", "SQ", "R", "S"]

TELEMETRY_CHANNELS = [
    "Speed",
    "Throttle",
    "Brake",
    "nGear",
    "RPM",
    "DRS",
    "X",
    "Y",
    "Z"
]

OPENF1_POLL_INTERVAL_SECONDS = 2
TIMESCALE_CHUNK_INTERVAL = "1 day"
