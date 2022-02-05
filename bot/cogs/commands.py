import logging

import discord
from discord.ext import commands

from bot.utils.commands import Commands

server_commands = Commands()


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def command(self, ctx, command_name: str):
        """`{prefix}command <command_name>` - *Runs a pre-defined shell command on server hosting pavlov-bot*
                **Description**: Runs a pre-defined shell command on server hosting pavlov-bot. These must be setup in commands.json file
                **Requires**: Permissions for the server as defined in commands.json
                **Example**: `{prefix}command restart_all`
                """
        command = server_commands.get(command_name)
        await command(ctx)
        await ctx.send(f"Execution of command `{command_name}` done.")


def setup(bot):
    bot.add_cog(Commands(bot))
