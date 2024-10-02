import itertools

import httpx
from TikTokLive import TikTokLiveClient

from app.core import config

proxy_cycle = itertools.cycle(config.PROXIES)


class ChatSocketClient(TikTokLiveClient):
    """
    A client that connects to the TikTok WebCast WebSocket

    """

    def __init__(self, unique_id: str, **kwargs):
        super().__init__(
            unique_id=unique_id,
            web_proxy=kwargs.pop('web_proxy', httpx.Proxy(next(proxy_cycle) if config.PROXIES else None)),
            **kwargs
        )
