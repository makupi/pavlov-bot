from .aliases import Aliases
from .config import Config
from .servers import Servers

config = Config()
servers = Servers()
aliases = Aliases()


class SteamPlayer:
    def __init__(self, name: str, unique_id: str):
        self.name = name
        self.unique_id = unique_id

    @classmethod
    def convert(cls, argument):
        """argument is either unique_id or name"""
        unique_id = aliases.get_player(argument)
        name = unique_id
        if unique_id == argument:
            alias = aliases.find_player_alias(argument)
            if alias:
                name = alias
        return cls(name, unique_id)

    @property
    def has_alias(self):
        return self.name != self.unique_id


__all__ = ["config", "servers", "aliases", "SteamPlayer"]
