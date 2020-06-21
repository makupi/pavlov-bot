import asyncio
import logging
import re
import sys
import traceback
from asyncio.exceptions import TimeoutError
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands

from bot.utils import aliases, config, servers
from bot.utils.steamplayer import SteamPlayer
from bot.utils.text_to_image import text_to_image
from bs4 import BeautifulSoup
from pavlov import PavlovRCON

# Admin – GiveItem, GiveCash, GiveTeamCash, SetPlayerSkin
# Mod – Ban, Kick, Unban, RotateMap, SwitchTeam
# Captain – SwitchMap, ResetSND
# Everyone - RefreshList, InspectPlayer, ServerInfo
# Ban – Told to fuck off


MODERATOR_ROLE = "Mod-{}"
CAPTAIN_ROLE = "Captain-{}"
RCON_TIMEOUT = 5

MATCH_DELAY_RESETSND = 10
RCON_COMMAND_PAUSE = 100 / 1000  # milliseconds

SERVERNAME_LENGTH = 36
MAP_NAME_LENGTH = 40
ANYONEPLAYING_ROW_FORMAT = "{alias:^10} | {server_name:^36} | {map_name:^40} | {map_alias:^15} | {player_count:^6}"


async def check_banned(ctx):
    pass


async def fetch(session, url):
    response = await session.get(url)
    try:
        return await response.text()
    except aiohttp.ContentTypeError:
        return None


async def check_perm_admin(ctx, server_name: str, sub_check=False):
    """ Admin permissions are stored per server in the servers.json """
    server = servers.get(server_name)
    if ctx.author.id not in server.get("admins", []):
        if not sub_check:
            user_action_log(
                ctx,
                f"ADMIN CHECK FAILED for server {server_name}",
                log_level=logging.WARNING,
            )
            if not ctx.batch_exec:
                await ctx.send(
                    embed=discord.Embed(description=f"This command is only for Admins.")
                )
        return False
    return True


async def check_perm_moderator(ctx, server_name: str, sub_check=False):
    if await check_perm_admin(ctx, server_name, sub_check=True):
        return True
    role_name = MODERATOR_ROLE.format(server_name)
    role = discord.utils.get(ctx.author.roles, name=role_name)
    if role is None:
        if not sub_check:
            user_action_log(
                ctx,
                f"MOD CHECK FAILED for server {server_name}",
                log_level=logging.WARNING,
            )
            if not ctx.batch_exec:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"This command is only for Moderators and above."
                    )
                )
        return False
    return True


async def check_perm_captain(ctx, server_name: str):
    if await check_perm_moderator(ctx, server_name, sub_check=True):
        return True
    role_name = CAPTAIN_ROLE.format(server_name)
    role = discord.utils.get(ctx.author.roles, name=role_name)
    if role is None:
        user_action_log(
            ctx,
            f"CAPTAIN CHECK FAILED for server {server_name}",
            log_level=logging.WARNING,
        )
        if not ctx.batch_exec:
            await ctx.send(
                embed=discord.Embed(
                    description=f"This command is only for Captains and above."
                )
            )
        return False
    return True


def user_action_log(ctx, message, log_level=logging.INFO):
    name = f"{ctx.author.name}#{ctx.author.discriminator}"
    logging.log(log_level, f"USER: {name} <{ctx.author.id}> -- {message}")


async def exec_server_command(ctx, server_name: str, command: str):
    pavlov = None
    if hasattr(ctx, "pavlov"):
        pavlov = ctx.pavlov.get(server_name)
    if not hasattr(ctx, "pavlov") or pavlov is None:
        server = servers.get(server_name)
        pavlov = PavlovRCON(
            server.get("ip"),
            server.get("port"),
            server.get("password"),
            timeout=RCON_TIMEOUT,
        )
        if not hasattr(ctx, "pavlov"):
            ctx.pavlov = {server_name: pavlov}
        else:
            ctx.pavlov[server_name] = pavlov
    data = await pavlov.send(command)
    return data


class Pavlov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._map_aliases = {}

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    async def get_map_alias(self, map_label: str) -> [str, str]:
        if map_label in self._map_aliases:
            _map = self._map_aliases.get(map_label)
            return _map.get("name"), _map.get("image")
        try:
            map_id = map_label.split("UGC")[1]
            data = await fetch(
                self.bot.aiohttp,
                f"https://steamcommunity.com/sharedfiles/filedetails/?id={map_id}",
            )
            soup = BeautifulSoup(data, "html.parser")
            # url_regex = r"/(\b(https?|ftp|file):\/\/[-A-Z0-9+&Q#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig"
            regex = r"(https:\/\/steamuserimages-a\.akamaihd\.net\/ugc\/[A-Z0-9\/]*)"
            match = re.findall(regex, data)[0]
            map_image = match
            map_name = soup.title.string.split("::")[1]
            self._map_aliases[map_label] = {"name": map_name, "image": map_image}
            return map_name, map_image
        except Exception as ex:
            logging.error(f"Getting map label failed with {ex}")
        return None, None

    async def cog_before_invoke(self, ctx):
        ctx.batch_exec = False
        await ctx.trigger_typing()
        user_action_log(
            ctx, f"INVOKED {ctx.command.name.upper():<10} args: {ctx.args[2:]}"
        )

    @commands.command()
    async def servers(self, ctx):
        """`{prefix}servers` - *Lists available servers*"""
        server_names = servers.get_names()
        embed = discord.Embed(
            title="Servers", description="\n- ".join([""] + server_names)
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def aliases(self, ctx):
        """`{prefix}aliases` - *Lists available aliases*"""
        embed = discord.Embed()
        maps = aliases.get_maps()
        maps_str = "```"
        for alias, label in maps.items():
            maps_str += f"{alias:<15} - {label}\n"
        maps_str += "```"
        if maps:
            embed.add_field(name="Maps", value=maps_str, inline=False)
        players = aliases.get_players()
        players_str = "```"
        for alias, unique_id in players.items():
            players_str += f"{alias:<15} <{unique_id}>\n"
        players_str += "```"
        if players_str:
            embed.add_field(name="Players", value=players_str, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx, server_name: str):
        """`{prefix}serverinfo <server_name>`

        **Example**: `{prefix}serverinfo rush`
        """
        data = await exec_server_command(ctx, server_name, "ServerInfo")
        server_info = data.get("ServerInfo")
        map_label = server_info.get("MapLabel")
        map_name, map_image = await self.get_map_alias(map_label)
        map_alias = aliases.find_map_alias(map_label)
        if ctx.batch_exec:
            map_alias_str = ""
            if map_alias:
                map_alias_str = f"Map Alias:   {map_alias}\n"
            return (
                f"```"
                f'Server Name: {server_info.get("ServerName")}\n'
                f'Round State: {server_info.get("RoundState")}\n'
                f'Players:     {server_info.get("PlayerCount")}\n'
                f'Game Mode:   {server_info.get("GameMode")}\n'
                f"Map:         {map_name}\n"
                f"{map_alias_str}"
                f"Map Label:   {map_label}```"
            )
        embed = discord.Embed(description=f"**ServerInfo** for `{server_name}`")
        if map_image:
            embed.set_thumbnail(url=map_image)
        embed.add_field(
            name="Server Name", value=server_info.get("ServerName"), inline=False
        )
        embed.add_field(name="Round State", value=server_info.get("RoundState"))
        embed.add_field(name="Players", value=server_info.get("PlayerCount"))
        embed.add_field(name="Game Mode", value=server_info.get("GameMode"))
        if map_name:
            embed.add_field(name="Map", value=f"{map_name}", inline=False)
        embed.add_field(name="Map Label", value=map_label, inline=False)
        if map_alias:
            embed.add_field(name="Map Alias", value=map_alias)
        await ctx.send(embed=embed)

    @commands.command()
    async def players(self, ctx, server_name: str):
        """`{prefix}players <server_name>`

        **Example**: `{prefix}players rush`
        """
        data = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = data.get("PlayerList")
        embed = discord.Embed(description=f"**Active players** on `{server_name}`:\n")
        if len(player_list) == 0:
            embed.description = f"Currently no active players on `{server_name}`"
        for player in player_list:
            embed.description += (
                f"\n - {player.get('Username', '')} <{player.get('UniqueId')}>"
            )
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def playerinfo(self, ctx, player_arg: str, server_name: str):
        """`{prefix}playerinfo <player_id> <server_name>`

        **Example**: `{prefix}playerinfo 89374583439127 rush`
        """
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"InspectPlayer {player.unique_id}"
        )
        player_info = data.get("PlayerInfo")
        if ctx.batch_exec:
            return player_info
        if not player_info:
            embed = discord.Embed(
                description=f"Player <{player.unique_id}> not found on `{server_name}`."
            )
        else:
            embed = discord.Embed(description=f"**Player info** for `{player.name}`")
            embed.add_field(name="Name", value=player_info.get("PlayerName"))
            embed.add_field(name="UniqueId", value=player_info.get("UniqueId"))
            embed.add_field(name="KDA", value=player_info.get("KDA"))
            embed.add_field(name="Cash", value=player_info.get("Cash"))
            embed.add_field(name="TeamId", value=player_info.get("TeamId"))
            if player.has_alias:
                embed.add_field(name="Alias", value=player.name)
        await ctx.send(embed=embed)

    @commands.command()
    async def switchmap(self, ctx, map_name: str, game_mode: str, server_name: str):
        """`{prefix}switchmap <map_name> <game_mode> <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}switchmap 89374583439127 rush`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        map_label = aliases.get_map(map_name)
        data = await exec_server_command(
            ctx, server_name, f"SwitchMap {map_label} {game_mode}"
        )
        switch_map = data.get("SwitchMap")
        if ctx.batch_exec:
            return switch_map
        if not switch_map:
            embed = discord.Embed(
                description=f"**Failed** to switch map to {map_name} with game mode {game_mode}"
            )
        else:
            embed = discord.Embed(
                description=f"Switched map to {map_name} with game mode {game_mode}"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def resetsnd(self, ctx, server_name: str):
        """`{prefix}resetsnd <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}resetsnd rush`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        data = await exec_server_command(ctx, server_name, "ResetSND")
        reset_snd = data.get("ResetSND")
        if ctx.batch_exec:
            return reset_snd
        if not reset_snd:
            embed = discord.Embed(description=f"**Failed** reset SND")
        else:
            embed = discord.Embed(description=f"SND successfully reset")
        await ctx.send(embed=embed)

    @commands.command()
    async def switchteam(self, ctx, player_arg: str, team_id: str, server_name: str):
        """`{prefix}switchteam <player_id> <team_id> <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}resetsnd 89374583439127 0 rush`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"SwitchTeam {player.unique_id} {team_id}"
        )
        switch_team = data.get("SwitchTeam")
        if ctx.batch_exec:
            return switch_team
        if not switch_team:
            embed = discord.Embed(
                description=f"**Failed** to switch <{player.unique_id}> to team {team_id}"
            )
        else:
            embed = discord.Embed(
                description=f"<{player.unique_id}> switched to team {team_id}"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def rotatemap(self, ctx, server_name: str):
        """`{prefix}rotatemap <server_name>`

        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}rotatemap rush`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        data = await exec_server_command(ctx, server_name, f"RotateMap")
        rotate_map = data.get("RotateMap")
        if ctx.batch_exec:
            return rotate_map
        if not rotate_map:
            embed = discord.Embed(description=f"**Failed** to rotate map")
        else:
            embed = discord.Embed(description=f"Rotated map successfully")
        await ctx.send(embed=embed)

    @commands.command()
    async def ban(self, ctx, player_arg: str, server_name: str):
        """`{prefix}ban <player_id> <server_name>`

        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}ban 89374583439127 rush`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Ban {player.unique_id}")
        ban = data.get("Ban")
        if ctx.batch_exec:
            return ban
        if not ban:
            embed = discord.Embed(description=f"**Failed** to ban <{player.unique_id}>")
        else:
            embed = discord.Embed(
                description=f"<{player.unique_id}> successfully banned"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def kick(self, ctx, player_arg: str, server_name: str):
        """`{prefix}kick <player_id> <server_name>`

        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kick 89374583439127 rush`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Kick {player.unique_id}")
        kick = data.get("Kick")
        if ctx.batch_exec:
            return kick
        if not kick:
            embed = discord.Embed(
                description=f"**Failed** to kick <{player.unique_id}>"
            )
        else:
            embed = discord.Embed(
                description=f"<{player.unique_id}> successfully kicked"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def unban(self, ctx, player_arg: str, server_name: str):
        """`{prefix}unban <player_id> <server_name>`

        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}unban 89374583439127 rush`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Unban {player.unique_id}")
        unban = data.get("Unban")
        if ctx.batch_exec:
            return unban
        if not unban:
            embed = discord.Embed(
                description=f"**Failed** to unban <{player.unique_id}>"
            )
        else:
            embed = discord.Embed(
                description=f"<{player.unique_id}> successfully unbanned"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def giveitem(self, ctx, player_arg: str, item_id: str, server_name: str):
        """`{prefix}giveitem <player_id> <item_id> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveitem 89374583439127 tazer rush`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"GiveItem {player.unique_id} {item_id}"
        )
        give_team = data.get("GiveItem")
        if ctx.batch_exec:
            return give_team
        if not give_team:
            embed = discord.Embed(
                description=f"**Failed** to give {item_id} to <{player.unique_id}>"
            )
        else:
            embed = discord.Embed(
                description=f"{item_id} given to <{player.unique_id}>"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def givecash(self, ctx, player_arg: str, cash_amount: str, server_name: str):
        """`{prefix}givecash <player_id> <cash_amount> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givecash 89374583439127 5000 rush`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"GiveCash {player.unique_id} {cash_amount}"
        )
        give_cash = data.get("GiveCash")
        if ctx.batch_exec:
            return give_cash
        if not give_cash:
            embed = discord.Embed(
                description=f"**Failed** to give {cash_amount} to <{player.unique_id}>"
            )
        else:
            embed = discord.Embed(
                description=f"{cash_amount} given to <{player.unique_id}>"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def giveteamcash(self, ctx, team_id: str, cash_amount: str, server_name: str):
        """`{prefix}giveteamcash <team_id> <cash_amount> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveteamcash 0 5000 rush`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(
            ctx, server_name, f"GiveTeamCash {team_id} {cash_amount}"
        )
        give_team_cash = data.get("GiveTeamCash")
        if ctx.batch_exec:
            return give_team_cash
        if not give_team_cash:
            embed = discord.Embed(
                description=f"**Failed** to give {cash_amount} to <{team_id}>"
            )
        else:
            embed = discord.Embed(description=f"{cash_amount} given to <{team_id}>")
        await ctx.send(embed=embed)

    @commands.command()
    async def setplayerskin(self, ctx, player_arg: str, skin_id: str, server_name: str):
        """`{prefix}setplayerskin <player_id> <skin_id> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}setplayerskin 89374583439127 clown rush`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"SetPlayerSkin {player.unique_id} {skin_id}"
        )
        set_player_skin = data.get("SetPlayerSkin")
        if ctx.batch_exec:
            return set_player_skin
        if not set_player_skin:
            embed = discord.Embed(
                description=f"**Failed** to set <{player.unique_id}>'s skin to {skin_id}"
            )
        else:
            embed = discord.Embed(
                description=f"<{player.unique_id}>'s skin set to {skin_id}"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def batch(self, ctx, *batch_commands):
        """`{prefix}batch "<command with arguments>" "<command with args>"`

        **Example**: `{prefix}batch "rotatemap rush" "serverinfo rush"`
        """
        embed = discord.Embed(title="batch execute")
        before = datetime.now()
        for args in batch_commands:
            _args = args.split(" ")
            cmd = _args[0]
            command = self.bot.all_commands.get(cmd.lower())
            ctx.batch_exec = True
            if command:
                # await ctx.send(f"batch execute: `{args}`.. ")
                try:
                    # await ctx.trigger_typing()
                    data = await command(ctx, *_args[1:])
                    if data is None:
                        embed.add_field(
                            name=args,
                            value="Command failed due to lack of permissions.",
                            inline=False,
                        )
                    else:
                        embed.add_field(name=args, value=data, inline=False)
                except Exception as ex:
                    logging.error(f"BATCH: {command} failed with {ex}")
                    traceback.print_exc(file=sys.stdout)
                    embed.add_field(name=args, value="execution failed", inline=False)
            else:
                embed.add_field(
                    name=args,
                    value="execution failed - command not found",
                    inline=False,
                )
        embed.set_footer(text=f"Execution time: {datetime.now() - before}")
        await ctx.send(embed=embed)

    @commands.command()
    async def matchsetup(
        self, ctx, team_a_name: str, team_b_name: str, server_name: str
    ):
        """`{prefix}matchsetup <team a name> <team b name> <server name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}matchsetup team_a team_b rush`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        before = datetime.now()
        teams = [aliases.get_team(team_a_name), aliases.get_team(team_b_name)]
        embed = discord.Embed()
        for team in teams:
            embed.add_field(
                name=f"{team.name} members", value=team.member_repr(), inline=False
            )
        await ctx.send(embed=embed)

        for index, team in enumerate(teams):
            for member in team.members:
                await exec_server_command(
                    ctx, server_name, f"SwitchTeam {member} {index}"
                )
                await asyncio.sleep(RCON_COMMAND_PAUSE)

        await ctx.send(
            embed=discord.Embed(
                description=f"Teams set up. Resetting SND in {MATCH_DELAY_RESETSND} seconds."
            )
        )
        await asyncio.sleep(MATCH_DELAY_RESETSND)
        await exec_server_command(ctx, server_name, "ResetSND")
        embed = discord.Embed(description="Reset SND. Good luck!")
        embed.set_footer(text=f"Execution time: {datetime.now() - before}")
        await ctx.send(embed=embed)

    @commands.command()
    async def anyoneplaying(self, ctx, server_group: str = None):
        """`{prefix}anyoneplaying [server_group]`"""
        # before = datetime.now()
        # embed = discord.Embed()
        ctx.batch_exec = True
        players_header = ANYONEPLAYING_ROW_FORMAT.format(
            alias="Alias",
            server_name="Server Name",
            map_name="Map Name",
            map_alias="Map Alias",
            player_count="Players",
        )
        desc = f"\n{players_header}\n{'-'*len(players_header)}\n"
        for server_alias in servers.get_names(server_group):
            data = await exec_server_command(ctx, server_alias, "ServerInfo")
            # players = await self.players(ctx, server_name)
            server_info = data.get("ServerInfo", {})
            players_count = server_info.get("PlayerCount", "0/0")
            server_name = server_info.get("ServerName", "")
            map_label = server_info.get("MapLabel")
            map_name, map_image = await self.get_map_alias(map_label)
            map_alias = aliases.find_map_alias(map_label)
            if not map_alias:
                map_alias = ""
            desc += ANYONEPLAYING_ROW_FORMAT.format(
                alias=server_alias,
                server_name=server_name[:SERVERNAME_LENGTH],
                map_name=map_name[:MAP_NAME_LENGTH],
                map_alias=map_alias,
                player_count=players_count,
            )
            desc += "\n"
        # embed.description = f"```{desc}```"
        # embed.set_footer(text=f"Execution time: {datetime.now()-before}")
        # await ctx.send(embed=embed)
        # await ctx.send(f"```{desc}```")
        file = text_to_image(desc)
        await ctx.send(file=file)


def setup(bot):
    bot.add_cog(Pavlov(bot))
