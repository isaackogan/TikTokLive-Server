import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager, Optional

from fastapi import FastAPI
from httpx._client import ClientState
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect, WebSocket

from app.core import config
from app.core.logger import get_logger
from app.core.ws.ws_manager import WebSocketManager


class TikTokLiveReaderAPI(FastAPI):

    def __init__(self, **extra: dict):
        super().__init__(
            lifespan=self.app_lifespan,
            docs_url="/docs" if config.TEST_MODE else None,
            **extra
        )

        # Create the manager
        self.ws_manager: Optional[WebSocketManager] = None
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)

    @staticmethod
    @asynccontextmanager
    async def app_lifespan(self) -> AsyncContextManager[None]:
        """
        Handle the lifespan of the app

        :return: Context manager for Criadex

        """

        self.logger.info(f"Environment file load state: {config.ENV_LOADED}")

        self.ws_manager = WebSocketManager(
            clean_up_interval=config.CLEAN_UP_INTERVAL,
            session_id=config.SESSION_ID
        )

        # Shutdown is after yield
        yield


app: TikTokLiveReaderAPI = TikTokLiveReaderAPI()


def api_key_query(
        api_key: str | None = None
) -> str | None:
    """
    Get the API key from the query

    :param api_key: The API key
    :return: The API key

    """

    return api_key


@app.get(
    "/ws/stats",
    tags=["WebSocket"],
)
async def ws_stats():
    """
    Get the stats of the websocket connections

    :return: The stats

    """

    return JSONResponse(status_code=200, content=app.ws_manager.stats)


@app.websocket(path="/ws")
async def ws_endpoint(
        websocket: WebSocket,
        unique_id: str,
        api_key: str
) -> None:
    """
    Create websocket connections to specific creators

    [WARN] Account name is not validated. You must fork to add this functionality. PRs accepted.

    :param websocket: The WebSocket
    :param unique_id: The unique ID of the creator
    :param api_key: The api key to use.
    :return: The websocket connection

    """

    await websocket.accept()

    async def recv():
        if websocket.client_state == ClientState.CLOSED:
            raise WebSocketDisconnect(1000)
        return await websocket.receive()

    app.logger.info(f"New WebSocket connection. Creating room...")
    room_client, promise = await app.ws_manager.join(account_name=api_key, unique_id=unique_id, ws=websocket)
    app.logger.info(f"Room created for @{unique_id}!")

    # Return none b/c join already handled the failure
    if room_client is None:
        return

    try:

        # Await the join promise
        app.logger.info(f"Awaiting setup of room for @{unique_id}...")
        await promise

        # Loop until disconnected
        while True:
            received_message = await recv()

            if received_message["type"] == "websocket.disconnect" or received_message["type"] == "websocket.close":
                raise WebSocketDisconnect(1000)

            if received_message["type"] != "websocket.receive":
                continue

            match received_message['text']:
                case "operation.room_info":
                    await room_client.room.fetch_room_info(client=room_client)
                case "operation.sub_info":
                    await room_client.room.fetch_sub_info(client=room_client)

        raise WebSocketDisconnect(1000)
    finally:
        app.logger.info(f"Client leaving room for @{unique_id}...")
        websocket.client_state = ClientState.CLOSED
        await app.ws_manager.leave(client=room_client, account_name=api_key)
