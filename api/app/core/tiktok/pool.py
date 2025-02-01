import asyncio
import logging
import traceback
from typing import Awaitable

from starlette.websockets import WebSocket

from app.core.logger import get_logger
from app.core.tiktok.room import TikTokRoom, RoomClient


class TikTokRoomPool:
    """
    A pool of TikTok rooms. This class manages all the rooms and their connected clients.

    """

    def __init__(
            self,
            clean_up_interval: int,
            session_id: str | None,
            authenticate_ws: bool = False
    ):
        self._rooms: dict[str, TikTokRoom] = {}
        self._clean_up_task: asyncio.Task = asyncio.create_task(self._clean_up_loop(clean_up_interval))
        self._logger = get_logger()
        self._session_id: str | None = session_id
        self._authenticate_ws: bool = authenticate_ws

    async def join(
            self,
            unique_id: str,
            ws: WebSocket
    ) -> tuple[RoomClient, Awaitable[None]]:
        """
        Join a room by unique_id

        :param unique_id: The unique ID of the room
        :return: The live room
        :param ws: The WebSocket to join the Room
        :raises: Exception if fails to connect to the TikTok room

        """

        # If the room DNE, create it
        if not self._rooms.get(unique_id):
            self._logger.info(f"Creating new room: @{unique_id}")
            room: TikTokRoom = await TikTokRoom.create(unique_id=unique_id, session_id=self._session_id, authenticate_ws=self._authenticate_ws)
            self._rooms[unique_id] = room

        # Retrieve the room
        room: TikTokRoom = self._rooms[unique_id]
        client, promise = room.join(ws=ws)

        async def join_room() -> None:
            # Join the room
            await promise
            self._logger.info(f"Client joined room @{unique_id}: {client.id} ({room.clients} client(s))")

        return client, join_room()

    async def leave(
            self,
            client: RoomClient
    ) -> None:
        """
        Leave a room given the

        :param client: The room client that needs to leave
        :return: None

        """

        room: TikTokRoom = self._rooms.get(client.unique_id)

        # If the room doesn't exist, can't do anything.
        if not room:
            return None

        # Leave the room
        await room.leave(client=client)
        self._logger.info(f"Client left room @{room.unique_id}: {client.id} ({room.clients} client(s))")

        # Check if the room is empty. If it is, it's time to end it
        await self.clean_up_room(room=room)

    async def clean_up_room(self, room: TikTokRoom) -> None:
        """
        Clean up a room if it's empty.

        If the room disconnects via DisconnectEvent, this function gets called *eventually* by the clean-up loop.
        Otherwise, if someone leaves & it's the last person, this also gets called, as we don't want to leave empty rooms open.

        :param room: The room to clean
        :return: None

        """

        # Only clean if empty
        if room.clients > 0:
            return

        self._logger.info("Deleting empty room: @" + room.unique_id)

        # Kill the room
        try:
            await room.kill()
        except:
            self._logger.error("Failed to kill empty room: " + traceback.format_exc())

        # Delete it from existence
        self._rooms.pop(room.unique_id, None)

    async def _clean_up_loop(self, interval: int) -> None:
        """
        Clean up empty rooms every 5 minutes

        """

        while True:

            for room in self._rooms.copy().values():
                await self.clean_up_room(room=room)

            await asyncio.sleep(interval)

    def serialize(self) -> dict:
        repr_dict = {}

        for unique_id, room in self._rooms.items():
            repr_dict[unique_id] = room.serialize()

        return repr_dict
