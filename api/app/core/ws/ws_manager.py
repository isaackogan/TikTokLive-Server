import logging
import traceback
from typing import TypedDict

from starlette.websockets import WebSocket

from app.core.logger import get_logger
from app.core.tiktok.pool import TikTokRoomPool
from app.core.tiktok.room import RoomClient
from app.core.ws.client_store import ClientStore


class WebSocketManagerStats(TypedDict):
    client_data: dict
    pool_data: dict


class WebSocketManager:

    def __init__(
            self,
            clean_up_interval: int
    ):
        # Map<account_id, ChatSocketClient[]>
        self._clients: ClientStore = ClientStore()

        # Logger
        self._logger = get_logger()
        self._logger.setLevel(logging.INFO)

        # Create the pool
        self._pool: TikTokRoomPool = TikTokRoomPool(
            clean_up_interval=clean_up_interval
        )

    async def join(
            self,
            account_name: str,
            unique_id: str,
            ws: WebSocket
    ) -> RoomClient | None:

        # Otherwise try to join the room
        try:
            client: RoomClient = await self._pool.join(unique_id=unique_id, ws=ws)
        except Exception as e:
            self._logger.error("Failed to get room: " + traceback.format_exc())
            return await ws.close(code=4_500, reason=f"Failed to get room: {e.__class__.__name__}")

        # Add the client to the store
        self._clients.add(account_name=account_name, client=client)
        return client

    async def leave(
            self,
            client: RoomClient,
            account_name: str
    ) -> None:

        # Remove the client from the store
        self._clients.remove(account_name=account_name, client=client)

        # Leave the room
        await self._pool.leave(client=client)

    @property
    def stats(self) -> WebSocketManagerStats:
        """
        Get the stats of the WebSocket manager

        :return: The stats for the manager

        """

        return {
            "client_data": self._clients.serialize(),
            "pool_data": self._pool.serialize()
        }
