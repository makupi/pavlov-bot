import json
import os
from typing import List

import discord
from discord import app_commands



class ServerNotFoundError(Exception):
    def __init__(self, server_name: str):
        self.server_name = server_name


class Servers:
    def __init__(self, filename="servers.json"):
        self._filename = filename
        self._servers = {}
        self.ServerNotFoundError = ServerNotFoundError
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump({}, file)
        with open(filename) as file:
            self._servers = json.load(file)

    def get(self, name: str):
        server = self._servers.get(name)
        if server is None:
            for key in self._servers.keys():
                if key.lower() == name.lower():
                    server = self._servers.get(key)
                    break
            else:
                raise ServerNotFoundError(name)
        return server

    def get_names(self, server_group: str = None):
        return list(self._servers.keys())

    def get_servers(self, server_group: str = None):
        return self._servers

    async def autocomplete(self, interaction: discord.Interaction, current: str)  -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=s, value=s)
            for s in self._servers.keys() if current.lower() in s.lower()
        ]