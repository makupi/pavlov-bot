import logging
import sys
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands

from bot.utils import aliases, config, servers, user_action_log
from discord_components import DiscordComponents, ComponentsBot, Button

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

__version__ = "0.5.1"

invite_link = "https://discordapp.com/api/oauth2/authorize?client_id={}&scope=bot&permissions=8192"


async def get_prefix(_bot, message):
    prefix = config.prefix
    # if not isinstance(message.channel, discord.DMChannel):
    #    prefix = get_guild_prefix(_bot, message.guild.id)
    return commands.when_mentioned_or(prefix)(_bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, case_insensitive=True)
bot.version = __version__
bot.remove_command("help")
DiscordComponents(bot)

@bot.event
async def on_ready():
    bot.invite = invite_link.format(bot.user.id)
    bot.aiohttp = aiohttp.ClientSession()
    await bot.change_presence(activity=discord.Game(f"v{__version__}"))
    logging.info(
        f"""Logged in as {bot.user}..
        Serving {len(bot.users)} users in {len(bot.guilds)} guilds
        Invite: {invite_link.format(bot.user.id)}
    """
    )


@bot.event
async def on_command_error(ctx, error):
    embed = discord.Embed()
    if isinstance(error, commands.MissingRequiredArgument):
        embed.description = (
            f"⚠️ Missing some required arguments.\nPlease use `{config.prefix}help` for more info!"
        )
    elif hasattr(error, "original"):
        if isinstance(error.original, servers.ServerNotFoundError):
            embed.description = (
                f"⚠️ Server `{error.original.server_name}` not found.\n "
                f"Please try again or use `{config.prefix}servers` to list the available servers."
            )
        elif isinstance(error.original, aliases.AliasNotFoundError):
            embed.description = (
                f"⚠️ Alias `{error.original.alias}` for `{error.original.alias_type}` not found.\n "
                f"Please try again or use `{config.prefix}aliases` to list the available `{error.original.alias_type}`."
            )
        elif isinstance(error.original, (ConnectionRefusedError, OSError, TimeoutError)):
            embed.description = f"Failed to establish connection to server, please try again later or contact an admin."
        else:
            raise error
    else:
        raise error
    await ctx.send(embed=embed)


@bot.before_invoke
async def before_invoke(ctx):
    ctx.batch_exec = False
    ctx.interaction_exec = False
    await ctx.trigger_typing()
    user_action_log(ctx, f"INVOKED {ctx.command.name.upper():<10} args: {ctx.args[2:]}")


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
