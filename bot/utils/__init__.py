from .aliases import Aliases
from .config import Config
from .servers import Servers
from .steamplayer import SteamPlayer

config = Config()
servers = Servers()
aliases = Aliases()
SteamPlayer.set_aliases(aliases)
aliases.load_teams()


__all__ = ["config", "servers", "aliases", "SteamPlayer"]
