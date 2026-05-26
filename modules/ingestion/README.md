# ingestion/ — Data Engineering Module

## What it does

Pulls F1 telemetry and historical race data from multiple sources, normalizes it, and stores it in TimescaleDB and PostgreSQL.

---

# Sources

- **FastF1** → 300Hz car telemetry and historical sessions
- **OpenF1 API** → Live session telemetry
- **Jolpica API** → Historical race results and standings

---

# Architecture

```text
FastF1 ──────────────────┐
OpenF1 API ──────────────┼──► Normalizer ──► TimescaleDB
Jolpica API ─────────────┘                ──► PostgreSQL
                                          ──► Redis
```

---

# Responsibilities

- Telemetry ingestion
- Historical race ingestion
- ETL pipelines
- Data normalization
- Schema validation
- Bulk database writes
- Cache synchronization
- Retry-safe ingestion jobs

---

# Key Files

| File | Responsibility |
|---|---|
| `src/fastf1_client.py` | FastF1 session loader |
| `src/openf1_client.py` | Live telemetry polling |
| `src/jolpica_client.py` | Historical race ingestion |
| `src/normalizer.py` | Schema normalization |
| `src/writer.py` | Bulk DB inserts |
| `src/quality.py` | Data quality validation |
| `src/tasks.py` | Celery scheduled jobs |

---

# Engineering Highlights

- Built a time-series telemetry ingestion pipeline using TimescaleDB hypertables
- Designed retry-safe ingestion with Redis-backed deduplication
- Implemented schema drift detection for evolving external APIs
- Optimized bulk inserts for high-frequency telemetry streams