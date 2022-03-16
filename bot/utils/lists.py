import json
import os


class ListsSettingsNotFoundError(Exception):
    def __init__(self, list_settings: str):
        self.list_settings = list_settings


class Lists:
    def __init__(self, filename="lists.json"):
        self._filename = filename
        self.__list_settings = {}
        self.ListsSettingsNotFoundError = ListsSettingsNotFoundError
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump("{}", file)
        with open(filename) as file:
            self.__list_settings = json.load(file)

    def get(self, name: str):
        list_settings = self.__list_settings.get(name)
        if list_settings is None:
            for key in self.__list_settings.keys():
                if key.lower() == name.lower():
                    list_settings = self.__list_settings.get(key)
                    break
            else:
                raise ListsSettingsNotFoundError(name)
        return list_settings

    def get_by_type(self, _type: str):
        result = dict()
        for name, list_setting in self.__list_settings.items():
            if list_setting.get("type").lower() == _type.lower():
                result[name] = list_setting
        return result

    def get_names(self, poll_group: str = None):
        return list(self.__list_settings.keys())
