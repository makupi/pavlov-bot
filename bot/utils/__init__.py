import logging

from .aliases import Aliases
from .config import Config
from .paginator import Paginator
from .servers import Servers
from .polling import Polling
from .lists import Lists
from .steamplayer import SteamPlayer

config = Config()
servers = Servers()
aliases = Aliases()
SteamPlayer.set_aliases(aliases)
aliases.load_teams()
polling = Polling()
lists = Lists()


def user_action_log(ctx, message, log_level=logging.INFO):
    name = f"{ctx.author.name}#{ctx.author.discriminator}"
    logging.log(log_level, f"USER: {name} <{ctx.author.id}> -- {message}")


__all__ = [
    "config",
    "servers",
    "aliases",
    "SteamPlayer",
    "Paginator",
    "user_action_log",
    "Polling"
]
