import json
import os


class ListsSettingsNotFoundError(Exception):
    def __init__(self, ListsSettings: str):
        self.Listssettings = ""


class Lists:
    def __init__(self, filename="lists.json"):
        self._filename = filename
        self._Listssettings = {}
        self.ListsSettingsNotFoundError = ListsSettingsNotFoundError
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump("{}", file)
        with open(filename) as file:
            self._Listssettings = json.load(file)

    def get(self, name: str):
        Listssettings = self._Listssettings.get(name)
        if Listssettings is None:
            for key in self._Listssettings.keys():
                if key.lower() == name.lower():
                    server = self._Listssettings.get(key)
                    break
            else:
                raise ListsSettingsNotFoundError(name)
        return Listssettings

    def get_names(self, poll_group: str = None):
        return list(self._Listssettings.keys())
