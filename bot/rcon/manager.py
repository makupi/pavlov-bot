import asyncio
from datetime import datetime
from typing import List

from pavlov import PavlovRCON

from bot.utils import Servers
from bot.utils.servers import ServerNotFoundError

STALE_TIMEOUT_SECONDS = 60

class PavlovRCONManager:
    def __init__(self, servers: Servers):
        self._conns = {}
        self._last_used = {}
        for name, server in servers.get_servers():
            self._conns[name] = PavlovRCON(ip=server.get("ip"), port=server.get("port"), password=server.get("password"))

        asyncio.create_task(self.__disconnect_stale_conns())

    async def send(self, server_name: str, command: str) -> dict:
        conn = self._conns.get(server_name)
        if not conn:
            raise ServerNotFoundError
        if not conn.is_connected():
            await conn.open()
        data = await conn.send(command)
        self.__mark_last_used_now(server_name)
        return data

    async def __disconnect_stale_conns(self):
        while True:
            for name, conn in self._conns:
                if conn.is_connected():
                    last_used = self._last_used.get(name)
                    if not last_used:
                        await conn.close()
                    delta = datetime.now() - last_used
                    if delta.seconds > 60:
                        await conn.close()
            await asyncio.sleep(5)

    def __mark_last_used_now(self, server_name: str):
        self._last_used[server_name] = datetime.now()