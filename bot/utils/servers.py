import json
import os


class Servers:
    def __init__(self, filename="servers.json"):
        self._filename = filename
        self._servers = {}
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump("{}", file)
        with open(filename) as file:
            self._servers = json.load(file)

    def get(self, name: str):
        return self._servers.get(name)

    def get_names(self):
        return list(self._servers.keys())
