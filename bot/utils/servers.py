import json
import os


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
                json.dump("{}", file)
        with open(filename) as file:
            self._servers = json.load(file)

    def get(self, name: str):
        server = self._servers.get(name)
        if server is None:
            raise ServerNotFoundError(name)
        return server

    def get_names(self):
        return list(self._servers.keys())
