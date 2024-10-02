import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager, Optional

from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect, WebSocketState, WebSocket

from app.core import config
from app.core.logger import get_logger
from app.core.tiktok.room import RoomClient
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

        self.ws_manager = WebSocketManager(
            clean_up_interval=config.CLEAN_UP_INTERVAL
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

    :param api_key: The API key
    :return: The stats

    """

    return JSONResponse(status_code=200, content=app.ws_manager.stats)


@app.websocket(
    path="/ws",
)
async def ws_endpoint(
        websocket: WebSocket,
        unique_id: str,
        account_name: str
) -> None:
    """
    Create websocket connections to specific creators

    [WARN] Account name is not validated. You must fork to add this functionality. PRs accepted.

    :param websocket: The WebSocket
    :param unique_id: The unique ID of the creator
    :param account_name: The account name to use.
    :return: The websocket connection

    """

    await websocket.accept()
    connect_data: RoomClient | None = await app.ws_manager.join(account_name=account_name, unique_id=unique_id, ws=websocket)

    # Return none b/c join already handled the failure
    if connect_data is None:
        return

    # Loop until disconnected
    try:
        while websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.receive()
        raise WebSocketDisconnect(1000)
    except WebSocketDisconnect:
        # Leave when disconnected
        await app.ws_manager.leave(client=connect_data[0], account_name=account_name)
