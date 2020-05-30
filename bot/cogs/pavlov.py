import discord
from discord.ext import commands

from bot.utils import config, servers
from pavlov import PavlovRCON


class ServerNotFoundError(Exception):
    def __init__(self, server_name: str):
        self.server_name = server_name


async def exec_server_command(server_name: str, command: str):
    server = servers.get(server_name)
    if server is None:
        raise ServerNotFoundError(server_name)
    pavlov = PavlovRCON(server.get("ip"), server.get("port"), server.get("password"))
    return await pavlov.send(command)


class Pavlov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def servers(self, ctx):
        pass

    async def cog_command_error(self, ctx, error):
        if isinstance(error.original, ServerNotFoundError):
            embed = discord.Embed(
                description=f"⚠️ Server `{error.original.server_name}` not found.\n "
                f"Please try again or use `{config.prefix}servers` to list the available servers."
            )
            await ctx.send(embed=embed)
        raise error

    @commands.command()
    async def serverinfo(self, ctx, server_name: str):
        data = await exec_server_command(server_name, "ServerInfo")
        await ctx.send(data)

    @commands.command()
    async def players(self, ctx, server_name: str):
        data = await exec_server_command(server_name, "RefreshList")
        await ctx.send(data)

    @commands.command()
    async def player(self, ctx, server_name: str, player_id: str):
        data = await exec_server_command(server_name, f"InspectPlayer {player_id}")
        await ctx.send(data)


def setup(bot):
    bot.add_cog(Pavlov(bot))
