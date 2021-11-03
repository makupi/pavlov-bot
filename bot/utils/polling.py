import json
import os


class PollingSettingsNotFoundError(Exception):
    def __init__(self, PollingSettings: str):
        self.pollingsettings = ""


class Polling:
    def __init__(self, filename="polling.json"):
        self._filename = filename
        self._pollingsettings = {}
        self.PollingSettingsNotFoundError = PollingSettingsNotFoundError
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump("{}", file)
        with open(filename) as file:
            self._pollingsettings = json.load(file)

    def get(self, name: str):
        pollingsettings = self._pollingsettings.get(name)
        if pollingsettings is None:
            for key in self._pollingsettings.keys():
                if key.lower() == name.lower():
                    pollingsettings = self._pollingsettings.get(key)
                    break
            else:
                raise PollingSettingsNotFoundError(name)
        return pollingsettings

    def get_names(self, poll_group: str = None):
        if self._pollingsettings.keys() is None:
            return 'NoPolls'
        return list(self._pollingsettings.keys())
