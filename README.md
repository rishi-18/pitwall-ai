# PitWall AI 🏎️

> A production-grade F1 intelligence platform combining real-time telemetry ingestion, ML-powered race strategy prediction, and GenAI race analysis — built as a modular monorepo.

---

# System Architecture

```text
pitwall/
├── modules/
│   ├── ingestion/     ← FastF1 + OpenF1 + Jolpica data pipeline → TimescaleDB
│   ├── ml_engine/     ← XGBoost + TFT strategy predictor, Isolation Forest anomaly detection
│   ├── genai_rag/     ← LangChain RAG + LangGraph agent + Groq streaming
│   ├── api/           ← FastAPI REST (JWT, versioned, rate-limited, OpenAPI)
│   ├── realtime/      ← WebSocket live race feed (OpenF1 → Redis pub/sub → clients)
│   ├── frontend/      ← React 18 + TypeScript + D3.js + Zustand
│   ├── infra/         ← Docker Compose, GitHub Actions CI/CD, Prometheus, Grafana
│   └── tests/         ← pytest, Locust load tests, WebSocket integration tests
│
├── shared/            ← Pydantic schemas, SQLAlchemy models, F1 constants
└── docs/              ← PRD, C4 architecture, data dictionary, API contracts
```

---

# Features

- Real-time F1 telemetry streaming
- AI-powered pit strategy prediction
- Driver performance analytics
- Live race visualization dashboard
- WebSocket-based telemetry broadcasting
- GenAI-powered race copilot
- Historical race analysis using RAG pipelines
- Anomaly and incident detection
- Production-grade observability and monitoring
- Scalable modular monorepo architecture

---

# Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Telemetry | FastF1 (300Hz), OpenF1 API (live) | Official F1 telemetry + live session data |
| Historical Data | Jolpica API | Historical race results and standings |
| Time-series DB | TimescaleDB | Optimized telemetry storage and querying |
| Cache / Pub-Sub | Redis | WebSocket fan-out and hot caching |
| Async Jobs | Celery | Scheduled ingestion and background ML jobs |
| ML | XGBoost, TFT, Isolation Forest, SHAP | Prediction, forecasting, explainability |
| GenAI | LangChain, LangGraph, ChromaDB, Groq | RAG pipelines and AI reasoning |
| API | FastAPI + Pydantic v2 | Async-native typed backend |
| Frontend | React 18, Vite, TypeScript, D3.js, Zustand | High-performance realtime dashboard |
| Observability | Prometheus, Grafana, structlog | Monitoring and logging |
| CI/CD | GitHub Actions, Docker Compose | Automated workflows and deployment |

---

# Quickstart

## Clone Repository

```bash
git clone https://github.com/yourname/pitwall.git
cd pitwall
```

## Setup Environment

```bash
cp .env.example .env
```

Fill in required secrets like:

```env
GROQ_API_KEY=your_api_key
```

## Start Services

```bash
docker-compose up --build
```

---

# Services

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API + Swagger Docs | http://localhost:8000/docs |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

---

# Module Overview

## ingestion/
Handles:
- FastF1 ingestion
- OpenF1 live telemetry polling
- ETL pipelines
- Data normalization
- Telemetry persistence

## ml_engine/
Handles:
- Pit strategy prediction
- Forecasting models
- Driver performance analytics
- Tire degradation prediction
- Anomaly detection

## genai_rag/
Handles:
- Retrieval augmented generation
- AI race strategist
- Context-aware race analysis
- Race narration and summarization

## api/
Handles:
- REST APIs
- JWT authentication
- Rate limiting
- Business logic
- OpenAPI documentation

## realtime/
Handles:
- WebSocket broadcasting
- Redis pub/sub
- Live telemetry streams
- Low-latency event propagation

## frontend/
Handles:
- Telemetry visualization
- Interactive dashboards
- Realtime charts
- AI copilot interface
- Race analytics UI

## infra/
Handles:
- Docker orchestration
- Monitoring setup
- CI/CD pipelines
- Logging and observability

## tests/
Handles:
- Unit testing
- Integration testing
- Load testing
- WebSocket testing

---

# Engineering Goals

This project is designed to demonstrate:

- Full-stack engineering
- Distributed systems
- Realtime data systems
- Machine learning engineering
- GenAI integration
- DevOps and observability
- Production architecture design
- Scalable modular systems

---

# Future Improvements

- Reinforcement learning for pit strategy
- Multi-race simulation engine
- Voice-enabled AI race engineer
- Kubernetes deployment
- Advanced telemetry anomaly detection
- Multi-agent race reasoning

---

# License

MIT License