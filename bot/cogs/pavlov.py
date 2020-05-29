import discord
from discord.ext import commands

from bot.utils import servers
from pavlov import PavlovRCON


async def exec_server_command(server_name: str, command: str):
    server = servers.get(server_name)
    pavlov = PavlovRCON(server.get("ip"), server.get("port"), server.get("password"))
    return await pavlov.send("ServerInfo")


class Pavlov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def servers(self, ctx):
        pass

    @commands.command()
    async def serverinfo(self, ctx, server_name: str):
        data = await exec_server_command(server_name, "ServerInfo")
        await ctx.send(data)


def setup(bot):
    bot.add_cog(Pavlov(bot))
