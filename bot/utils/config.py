import json
import os

default_config = {"prefix": ";", "token": "", "default_server": "default", "guilds": []}


class Config:
    def __init__(self, filename="config.json"):
        self.filename = filename
        self.config = {}
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump(default_config, file)
        with open(filename) as file:
            self.config = json.load(file)
        self.prefix = self.config.get("prefix", default_config.get("prefix"))
        self.token = self.config.get("token", default_config.get("token"))
        self.apiPATH = self.config.get("modioAPIPath", default_config.get("modioAPIPath"))
        self.pav_push_URL = self.config.get("pav_push_URL", default_config.get("pav_push_URL"))
        self.apiKEY = self.config.get("modioAPIKey", default_config.get("modioAPIKey"))
        self.default_server = self.config.get(
            "default_server", default_config.get("default_server")
        )
        self.guilds = self.config.get("guilds", default_config.get("guilds"))

    def store(self):
        c = {"prefix": self.prefix, "token": self.token}
        with open(self.filename, "w") as file:
            json.dump(c, file)
