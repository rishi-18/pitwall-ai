# api/ — Backend Development Module

## What it does

Versioned FastAPI backend exposing:
- telemetry
- sessions
- ML predictions
- GenAI endpoints
- standings
- health metrics

## Endpoints

- GET /v1/sessions
- POST /v1/predictions/pit-strategy
- POST /v1/rag/query
- GET /health
- GET /metrics

## Features

- JWT authentication
- Redis-backed rate limiting
- Prometheus metrics
- OpenAPI docs
- async DB access
- SSE streaming
