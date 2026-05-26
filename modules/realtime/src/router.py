from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

import json
import structlog

from modules.realtime.src.ws_manager import (
    ws_manager
)

from shared.utils.redis import (
    get_redis
)

log = structlog.get_logger()

router = APIRouter()


@router.websocket("/ws/live/{session_key}")
async def live_race_feed(
    websocket: WebSocket,
    session_key: int
):

    await ws_manager.connect(
        websocket,
        session_key
    )

    redis = await get_redis()

    pubsub = redis.pubsub()

    await pubsub.subscribe(
        f"live:session:{session_key}"
    )

    log.info(
        "client_subscribed",
        session_key=session_key
    )

    try:

        async for message in pubsub.listen():

            if message["type"] == "message":

                data = json.loads(
                    message["data"]
                )

                await websocket.send_json(data)

    except WebSocketDisconnect:

        log.info(
            "client_disconnected",
            session_key=session_key
        )

    finally:

        await pubsub.unsubscribe(
            f"live:session:{session_key}"
        )

        ws_manager.disconnect(
            websocket,
            session_key
        )
