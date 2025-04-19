import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils.commands import Commands

server_commands = Commands()


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @app_commands.command()
    @app_commands.describe(command_name="The name of the command")
    @app_commands.rename(command_name="command")
    @app_commands.autocomplete(command_name=server_commands.autocomplete)
    async def command(self, interaction: discord.Interaction, command_name: str):
        """`{prefix}command <command_name>` - *Runs a pre-defined shell command on server hosting pavlov-bot*
                **Description**: Runs a pre-defined shell command on server hosting pavlov-bot. These must be setup in commands.json file
                **Requires**: Permissions for the server as defined in commands.json
                **Example**: `{prefix}command restart_all`
                """
        command = server_commands.get(command_name)
        await command(interaction)
        await interaction.response.send_message(f"Execution of command `{command_name}` done.")


async def setup(bot):
    await bot.add_cog(Commands(bot))
