import logging
import sys
from pathlib import Path
import asyncio

import aiohttp
import discord
from discord.ext import commands

from bot.utils import aliases, config, servers, user_action_log

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

__version__ = "0.7.3"

invite_link = "https://discordapp.com/api/oauth2/authorize?client_id={}&scope=bot&permissions=8192"


async def get_prefix(_bot, message):
    prefix = config.prefix
    return commands.when_mentioned_or(prefix)(_bot, message)


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = commands.AutoShardedBot(command_prefix=get_prefix, case_insensitive=True, intents=intents)
bot.version = __version__
bot.remove_command("help")


class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


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
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"⚠️ Missing required arguments. Use `{config.prefix}help` for more info!"
        )
    elif hasattr(error, "original"):
        if isinstance(error.original, servers.ServerNotFoundError):
            await ctx.send(
                f"⚠️ Server `{error.original.server_name}` not found.\n"
                f"Use `{config.prefix}servers` to list available servers."
            )
        elif isinstance(error.original, aliases.AliasNotFoundError):
            await ctx.send(
                f"⚠️ Alias `{error.original.alias}` for `{error.original.alias_type}` not found.\n"
                f"Use `{config.prefix}aliases` to list available `{error.original.alias_type}`."
            )
        elif isinstance(error.original, (ConnectionRefusedError, OSError, TimeoutError)):
            await ctx.send("Failed to establish connection to server. Try again later or contact an admin.")
        else:
            raise error
    else:
        raise error


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


async def load_extensions(_bot):
    for ext in extensions():
        try:
            await _bot.load_extension(ext)
        except Exception as ex:
            logging.error(f"Failed to load extension {ext} - exception: {ex}")


async def main():
    await load_extensions(bot)
    await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())

