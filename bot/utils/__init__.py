import logging
from datetime import datetime

from .aliases import Aliases
from .config import Config
from .lists import Lists
from .paginator import Paginator
from .polling import Polling
from .servers import Servers
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
    file_object = open("user_action_log.txt", "a")
    file_object.write(f"{datetime.now()} - USER: {name} <{ctx.author.id}> -- {message}\n")
    file_object.close()


__all__ = [
    "config",
    "servers",
    "aliases",
    "SteamPlayer",
    "Paginator",
    "user_action_log",
    "polling",
    "lists",
]
