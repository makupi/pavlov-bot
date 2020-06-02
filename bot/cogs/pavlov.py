import discord
from discord.ext import commands

from bot.utils import config, servers
from pavlov import PavlovRCON

# Admin – GiveItem, GiveCash, GiveTeamCash, SetPlayerSkin
# Mod – Ban, Kick, Unban, RotateMap, SwitchTeam
# Captain – SwitchMap, ResetSND
# Everyone - RefreshList, InspectPlayer, ServerInfo
# Ban – Told to fuck off


MODERATOR_ROLE = "Mod-{}"
CAPTAIN_ROLE = "Captain-{}"


async def exec_server_command(server_name: str, command: str):
    server = servers.get(server_name)
    pavlov = PavlovRCON(server.get("ip"), server.get("port"), server.get("password"))
    return await pavlov.send(command)


async def check_banned(ctx):
    pass


async def check_perm_admin(ctx, server_name: str):
    """ Admin permissions are stored per server in the servers.json """
    server = servers.get(server_name)
    if ctx.author.id not in server.get("admins", []):
        await ctx.send(
            embed=discord.Embed(description=f"This command is only for Admins.")
        )
        return False
    return True


async def check_perm_moderator(ctx, server_name: str):
    role_name = MODERATOR_ROLE.format(server_name)
    role = discord.utils.get(ctx.author.roles, name=role_name)
    if role is None:
        await ctx.send(
            embed=discord.Embed(description=f"This command is only for Moderators.")
        )
        return False
    return True


async def check_perm_captain(ctx, server_name: str):
    role_name = CAPTAIN_ROLE.format(server_name)
    role = discord.utils.get(ctx.author.roles, name=role_name)
    if role is None:
        await ctx.send(
            embed=discord.Embed(description=f"This command is only for Captains.")
        )
        return False
    return True


class Pavlov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{type(self).__name__} Cog ready.")

    async def cog_command_error(self, ctx, error):
        embed = discord.Embed()
        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"⚠️ Missing some required arguments.\nPlease use `{config.prefix}help` for more info!"
        elif isinstance(error.original, servers.ServerNotFoundError):
            embed.description = (
                f"⚠️ Server `{error.original.server_name}` not found.\n "
                f"Please try again or use `{config.prefix}servers` to list the available servers."
            )
        else:
            raise error
        await ctx.send(embed=embed)

    async def cog_before_invoke(self, ctx):
        await ctx.trigger_typing()

    @commands.command()
    async def servers(self, ctx):
        server_names = servers.get_names()
        embed = discord.Embed(
            title="Servers", description="\n- ".join([""] + server_names)
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx, server_name: str):
        data = await exec_server_command(server_name, "ServerInfo")
        server_info = data.get("ServerInfo")

        embed = discord.Embed(description=f"**ServerInfo** for `{server_name}`")
        embed.add_field(
            name="Server Name", value=server_info.get("ServerName"), inline=False
        )
        embed.add_field(name="Round State", value=server_info.get("RoundState"))
        embed.add_field(name="Players", value=server_info.get("PlayerCount"))
        embed.add_field(name="Game Mode", value=server_info.get("GameMode"))
        embed.add_field(name="Map Label", value=server_info.get("MapLabel"))
        await ctx.send(embed=embed)

    @commands.command()
    async def players(self, ctx, server_name: str):
        data = await exec_server_command(server_name, "RefreshList")
        player_list = data.get("PlayerList")
        embed = discord.Embed(description=f"**Active players** on `{server_name}`:\n")
        if len(player_list) == 0:
            embed.description = f"Currently no active players on `{server_name}`"
        for player in player_list:
            embed.description += f"\n - {player}"
        await ctx.send(embed=embed)

    @commands.command()
    async def player(self, ctx, player_id: str, server_name: str):
        data = await exec_server_command(server_name, f"InspectPlayer {player_id}")
        await ctx.send(data)

    @commands.command()
    async def switchmap(self, ctx, map_name: str, game_mode: str, server_name: str):
        if not await check_perm_captain(ctx, server_name):
            return
        data = await exec_server_command(
            server_name, f"SwitchMap {map_name} {game_mode}"
        )
        await ctx.send(data)

    @commands.command()
    async def resetsnd(self, ctx, server_name: str):
        if not await check_perm_captain(ctx, server_name):
            return
        data = await exec_server_command(server_name, "ResetSND")
        await ctx.send(data)

    @commands.command()
    async def ban(self, ctx, unique_id: str, server_name: str):
        if not await check_perm_moderator(ctx, server_name):
            return
        data = await exec_server_command(server_name, f"Ban {unique_id}")
        await ctx.send(data)

    @commands.command()
    async def kick(self, ctx, unique_id: str, server_name: str):
        if not await check_perm_moderator(ctx, server_name):
            return
        data = await exec_server_command(server_name, f"Kick {unique_id}")
        await ctx.send(data)

    @commands.command()
    async def unban(self, ctx, unique_id: str, server_name: str):
        if not await check_perm_moderator(ctx, server_name):
            return
        data = await exec_server_command(server_name, f"Unban {unique_id}")
        await ctx.send(data)

    @commands.command()
    async def switchteam(self, ctx, unique_id: str, team_id: str, server_name: str):
        if not await check_perm_moderator(ctx, server_name):
            return
        data = await exec_server_command(
            server_name, f"SwitchTeam {unique_id} {team_id}"
        )
        await ctx.send(data)

    @commands.command()
    async def giveitem(self, ctx, unique_id: str, item_id: str, server_name: str):
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(server_name, f"GiveItem {unique_id} {item_id}")
        await ctx.send(data)

    @commands.command()
    async def givecash(self, ctx, unique_id: str, cash_amount: str, server_name: str):
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(
            server_name, f"GiveCash {unique_id} {cash_amount}"
        )
        await ctx.send(data)

    @commands.command()
    async def givecash(self, ctx, team_id: str, cash_amount: str, server_name: str):
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(
            server_name, f"GiveTeamCash {team_id} {cash_amount}"
        )
        await ctx.send(data)

    @commands.command()
    async def setplayerskin(self, ctx, unique_id: str, skin_id: str, server_name: str):
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(
            server_name, f"SetPlayerSkin {unique_id} {skin_id}"
        )
        await ctx.send(data)


def setup(bot):
    bot.add_cog(Pavlov(bot))
