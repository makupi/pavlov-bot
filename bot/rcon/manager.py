import asyncio
import logging
from datetime import datetime
from typing import List

from pavlov import PavlovRCON

from bot.utils import Servers
from bot.utils.servers import ServerNotFoundError

STALE_TIMEOUT_SECONDS = 60
RCON_TIMEOUT = 60

class PavlovRCONManager:
    def __init__(self, servers: Servers):
        self._conns = {}
        self._last_used = {}
        for name, server in servers.get_servers().items():
            self._conns[name] = PavlovRCON(ip=server.get("ip"), port=server.get("port"), password=server.get("password"), timeout=RCON_TIMEOUT)

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
            try:
                for name, conn in self._conns.items():
                    if conn.is_connected():
                        last_used = self._last_used.get(name)
                        if not last_used:
                            await conn.close()
                            continue
                        delta = datetime.now() - last_used
                        if delta.seconds > STALE_TIMEOUT_SECONDS:
                            logging.info(f"Closing stale connection for {name} after unused for {delta.seconds} seconds.")
                            await conn.close()
                await asyncio.sleep(5)
            except Exception as ex:
                logging.error(f"__disconnect_stale_conns: {ex}")

    def __mark_last_used_now(self, server_name: str):
        self._last_used[server_name] = datetime.now()