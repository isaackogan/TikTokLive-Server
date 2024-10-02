from typing import Dict, List

from app.core.tiktok.room import RoomClient


class ClientStore:

    def __init__(self):

        # Map<account_name, List[RoomClient]>
        self._clients: Dict[str, List[RoomClient]] = {}

    def add(self, account_name: str, client: RoomClient) -> None:

        if account_name not in self._clients:
            self._clients[account_name] = []

        self._clients[account_name].append(client)

    def remove(self, account_name: str, client: RoomClient) -> None:

        if account_name not in self._clients:
            return

        self._clients[account_name].remove(client)

        if not self._clients[account_name]:
            self._clients.pop(account_name, None)

    def get_account(self, account_name: str) -> List[RoomClient]:
        return self._clients.get(account_name, [])

    def get(self, account_name: str, client_id: str) -> RoomClient | None:

        for client in self.get_account(account_name):
            if client.id == client_id:
                return client

        return None

    def count(self, account_name: str) -> int:
        return len(self.get_account(account_name))

    def serialize(self) -> dict:
        repr_dict = {}

        for account_name, clients in self._clients.items():
            repr_dict[account_name] = [client.model_dump(exclude={"ws"}) for client in clients]

        return repr_dict
