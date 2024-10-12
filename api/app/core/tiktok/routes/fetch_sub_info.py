from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults
from httpx import Response


class FailedFetchSubInfoError(RuntimeError):
    pass


class FetchSubInfoRoute(ClientRoute):
    """
    Fetch a user's sub info

    """

    async def __call__(
            self,
            room_id: int,
            sec_uid: str
    ) -> dict:
        """
        Fetch a user's sub info.
        WARN: Requires a VALID session_id or else this route fails.

        :param room_id: The room ID to fetch with
        :return: The user's sub info

        """

        self._logger.info(f"Fetching sub info for room '{room_id}' with sec_uid {sec_uid}")

        try:
            response: Response = await self._web.get_response(
                url=WebDefaults.tiktok_webcast_url + "/sub/privilege/get_sub_privilege_detail",
                extra_params={
                    "room_id": room_id,
                    "sec_anchor_id": sec_uid
                }
            )
            return response.json()["data"]
        except Exception as ex:
            raise FailedFetchSubInfoError from ex
