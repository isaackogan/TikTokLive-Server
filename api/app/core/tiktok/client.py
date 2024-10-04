import itertools

import httpx
from TikTokLive import TikTokLiveClient

from app.core import config
from app.core.tiktok.routes.fetch_sub_info import FetchSubInfoRoute

proxy_cycle = itertools.cycle(config.PROXIES)


class ChatSocketClient(TikTokLiveClient):
    """
    A client that connects to the TikTok WebCast WebSocket

    """

    def __init__(self, unique_id: str, **kwargs):
        super().__init__(
            unique_id=unique_id,
            web_proxy=kwargs.pop('web_proxy', httpx.Proxy(next(proxy_cycle)) if config.PROXIES else None),
            **kwargs
        )

        self._fetch_sub_info = FetchSubInfoRoute(self.web)
        self._sub_info: dict | None = None

    async def fetch_sub_info(self) -> dict | None:
        self._sub_info = self._sub_info or await self._fetch_sub_info(
            room_id=int(self.room_id),
            sec_uid=self.room_info.get('owner', {}).get('sec_uid')
        )
        return self._sub_info

    def set_session_id(self, session_id: str) -> None:
        """
        Set the session ID for the client

        :param session_id: The session ID
        :return: None

        """

        self._web.set_session_id(session_id)
