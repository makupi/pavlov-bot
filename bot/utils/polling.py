import json
import os


class PollingSettingsNotFoundError(Exception):
    def __init__(self, settings: str):
        self.settings = settings


class Polling:
    def __init__(self, filename="polling.json"):
        self._filename = filename
        self._settings = {}
        self.PollingSettingsNotFoundError = PollingSettingsNotFoundError
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump({}, file)
        with open(filename) as file:
            self._settings = json.load(file)

    def get(self, name: str):
        setting = self._settings.get(name)
        if setting is None:
            for key in self._settings.keys():
                if key.lower() == name.lower():
                    setting = self._settings.get(key)
                    break
            else:
                raise PollingSettingsNotFoundError(name)
        return setting

    def get_names(self, poll_group: str = None):
        return list(self._settings.keys())
