# realtime/ — Backend Systems Module

## What it does

Realtime race telemetry broadcasting system using:
- OpenF1 polling
- Redis pub/sub
- FastAPI WebSockets

## Architecture

OpenF1 API
    +--? Poller
              +--? Redis Pub/Sub
                        +--? WebSocket Manager
                                  +--? Browser Clients

## Key files

- src/ws_manager.py
- src/router.py
- src/events.py
- src/poller.py
