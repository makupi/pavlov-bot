import asyncio
import logging
import random
import sys
from pathlib import Path

import discord
from discord.ext import commands

from bot.utils import config

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

__version__ = "0.1.3"

invite_link = "https://discordapp.com/api/oauth2/authorize?client_id={}&scope=bot&permissions=8192"


async def get_prefix(_bot, message):
    prefix = config.prefix
    # if not isinstance(message.channel, discord.DMChannel):
    #    prefix = get_guild_prefix(_bot, message.guild.id)
    return commands.when_mentioned_or(prefix)(_bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix)
bot.version = __version__
bot.remove_command("help")


@bot.event
async def on_ready():
    bot.invite = invite_link.format(bot.user.id)
    await bot.change_presence(activity=discord.Game(f"v{__version__}"))
    logging.info(
        f"""Logged in as {bot.user}..
        Serving {len(bot.users)} users in {len(bot.guilds)} guilds
        Invite: {invite_link.format(bot.user.id)}
    """
    )


def extensions():
    files = Path("bot", "cogs").rglob("*.py")
    for file in files:
        yield file.as_posix()[:-3].replace("/", ".")


def load_extensions(_bot):
    for ext in extensions():
        try:
            _bot.load_extension(ext)
        except Exception as ex:
            logging.error(f"Failed to load extension {ext} - exception: {ex}")


def run():
    load_extensions(bot)
    bot.run(config.token)
