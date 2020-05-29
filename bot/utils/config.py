import json
import os

default_config = {"prefix": ";", "token": ""}


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

    def store(self):
        c = {"prefix": self.prefix, "token": self.token}
        with open(self.filename, "w") as file:
            json.dump(c, file)
