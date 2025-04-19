import logging
from pathlib import Path

import aiohttp
import discord
from discord import app_commands, Interaction
from discord._types import ClientT
from discord.ext import commands

from bot.utils import aliases, config, servers, user_action_log


def setup_logger() -> logging.Logger:
    logging.basicConfig(format="%(asctime)s %(name)-16s %(levelname)-8s %(message)s", level=logging.INFO)
    return logging.getLogger()


__version__ = "2.0.0"

invite_link = "https://discord.com/oauth2/authorize?client_id={}"

initial_extensions = (
    'bot.cogs.pavlov',
    'bot.cogs.utility',
    'bot.cogs.teams',
    'bot.cogs.commands'
)


def extensions():
    files = Path("bot", "cogs").rglob("*.py")
    for file in files:
        yield file.as_posix()[:-3].replace("/", ".")


class CommandTree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        logging.error(f"AppCommand Error: {error}")

        embed = discord.Embed()
        if hasattr(error, "original"):
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
        await interaction.response.send_message(embed=embed)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        logging.info(f"INVOKED {interaction.command.name} args: {interaction.extras}")
        return await super().interaction_check(interaction)


class PavlovBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(
            command_prefix="!",
            intents=intents,
            tree_cls=CommandTree
        )

        self.session = None
        self.invite = ""
        self.log = setup_logger()
        self.version = __version__
        self.remove_command("help")


    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.invite = invite_link.format(self.user.id)
        for cog in initial_extensions:
            try:
                await self.load_extension(cog)
            except Exception as e:
                self.log.error(f"Failed to load extension {cog}: {e}")
        for guild in config.guilds:
            g = discord.Object(id=guild)
            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(f"v{__version__}"))
        self.log.info(
            f"""Logged in as {bot.user}..
            Serving {len(bot.users)} users in {len(bot.guilds)} guilds
            Invite: {self.invite}
        """
        )
    #
    # async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
    #     embed = discord.Embed()
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         embed.description = (
    #             f"⚠️ Missing some required arguments.\nPlease use `{config.prefix}help` for more info!"
    #         )
    #     elif hasattr(error, "original"):
    #         if isinstance(error.original, servers.ServerNotFoundError):
    #             embed.description = (
    #                 f"⚠️ Server `{error.original.server_name}` not found.\n "
    #                 f"Please try again or use `{config.prefix}servers` to list the available servers."
    #             )
    #         elif isinstance(error.original, aliases.AliasNotFoundError):
    #             embed.description = (
    #                 f"⚠️ Alias `{error.original.alias}` for `{error.original.alias_type}` not found.\n "
    #                 f"Please try again or use `{config.prefix}aliases` to list the available `{error.original.alias_type}`."
    #             )
    #         elif isinstance(error.original, (ConnectionRefusedError, OSError, TimeoutError)):
    #             embed.description = f"Failed to establish connection to server, please try again later or contact an admin."
    #         else:
    #             raise error
    #     else:
    #         raise error
    #     await interaction.response.send_message(embed=embed)
    #
    # async def before_invoke(self, ctx: commands.Context):
    #     ctx.batch_exec = False
    #     ctx.interaction_exec = False
    #     user_action_log(ctx, f"INVOKED {ctx.command.name.upper():<10} args: {ctx.args[2:]}")

# async def get_prefix(_bot, message):
#     prefix = config.prefix
#     # if not isinstance(message.channel, discord.DMChannel):
#     #    prefix = get_guild_prefix(_bot, message.guild.id)
#     return commands.when_mentioned_or(prefix)(_bot, message)

bot = PavlovBot(intents=discord.Intents.default())

async def run():
    async with bot:
        await bot.start(config.token)
