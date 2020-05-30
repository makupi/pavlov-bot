import discord
from discord.ext import commands

from bot.utils import config, servers
from pavlov import PavlovRCON

# Admin – GiveItem, GiveCash, GiveTeamCash, SetPlayerSkin
# Mod – Ban, Kick, Unban, RotateMap, SwitchTeam
# Captain – SwitchMap, ResetSND
# Everyone - RefreshList, InspectPlayer, ServerInfo
# Ban – Told to fuck off


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

    def check_perm_admin(self):
        async def predicate(ctx):
            return True

        return commands.check(predicate)

    def check_perm_moderator(self):
        async def predicate(ctx):
            return True

        return commands.check(predicate)

    def check_perm_captain(self):
        async def predicate(ctx):
            return True

        return commands.check(predicate)

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

    @commands.command()
    @check_perm_captain()
    async def switchmap(self, ctx, server_name: str, map_name: str, game_mode: str):
        data = await exec_server_command(
            server_name, f"SwitchMap {map_name} {game_mode}"
        )
        await ctx.send(data)

    @commands.command()
    @check_perm_captain()
    async def resetsnd(self, ctx, server_name: str):
        data = await exec_server_command(server_name, "ResetSND")
        await ctx.send(data)

    @commands.command()
    @check_perm_moderator()
    async def ban(self, ctx, server_name: str, unique_id: str):
        data = await exec_server_command(server_name, f"Ban {unique_id}")
        await ctx.send(data)

    @commands.command()
    @check_perm_moderator()
    async def kick(self, ctx, server_name: str, unique_id: str):
        data = await exec_server_command(server_name, f"Kick {unique_id}")
        await ctx.send(data)

    @commands.command()
    @check_perm_moderator()
    async def unban(self, ctx, server_name: str, unique_id: str):
        data = await exec_server_command(server_name, f"Unban {unique_id}")
        await ctx.send(data)

    @commands.command()
    @check_perm_moderator()
    async def switchteam(self, ctx, server_name: str, unique_id: str, team_id: str):
        data = await exec_server_command(
            server_name, f"SwitchTeam {unique_id} {team_id}"
        )
        await ctx.send(data)

    @commands.command()
    @check_perm_admin()
    async def giveitem(self, ctx, server_name: str, unique_id: str, item_id: str):
        data = await exec_server_command(server_name, f"GiveItem {unique_id} {item_id}")
        await ctx.send(data)

    @commands.command()
    @check_perm_admin()
    async def givecash(self, ctx, server_name: str, unique_id: str, cash_amount: str):
        data = await exec_server_command(
            server_name, f"GiveCash {unique_id} {cash_amount}"
        )
        await ctx.send(data)

    @commands.command()
    @check_perm_admin()
    async def givecash(self, ctx, server_name: str, team_id: str, cash_amount: str):
        data = await exec_server_command(
            server_name, f"GiveTeamCash {team_id} {cash_amount}"
        )
        await ctx.send(data)

    @commands.command()
    @check_perm_admin()
    async def setplayerskin(self, ctx, server_name: str, unique_id: str, skin_id: str):
        data = await exec_server_command(
            server_name, f"SetPlayerSkin {unique_id} {skin_id}"
        )
        await ctx.send(data)


def setup(bot):
    bot.add_cog(Pavlov(bot))
