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

SUPER_MODERATOR = "Mod-bot"
SUPER_CAPTAIN = "Captain-bot"

RCON_TIMEOUT = 5

MATCH_DELAY_RESETSND = 10
RCON_COMMAND_PAUSE = 100 / 1000  # milliseconds

ANYONEPLAYING_ROW_FORMAT = (
    "{alias:^15} | {server_name:^36.36} | {map_name:^36.36} "
    "| {map_alias:^15} | {player_count:^6}"
)


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
    if not server_name:
        return False
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


async def check_perm_moderator(ctx, server_name: str = None, sub_check=False):
    if await check_perm_admin(ctx, server_name, sub_check=True):
        return True
    role = None
    if server_name:
        role_name = MODERATOR_ROLE.format(server_name)
        role = discord.utils.get(ctx.author.roles, name=role_name)
    super_role = discord.utils.get(ctx.author.roles, name=SUPER_MODERATOR)
    if role is None and super_role is None:
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


async def check_perm_captain(ctx, server_name: str = None):
    if await check_perm_moderator(ctx, server_name, sub_check=True):
        return True
    role = None
    if server_name is not None:
        role_name = CAPTAIN_ROLE.format(server_name)
        role = discord.utils.get(ctx.author.roles, name=role_name)
    super_role = discord.utils.get(ctx.author.roles, name=SUPER_CAPTAIN)
    if role is None and super_role is None:
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

    @commands.group(invoke_without_command=True, pass_context=True, aliases=["alias"])
    async def aliases(self, ctx):
        """`{prefix}aliases` - *Lists available aliases*"""
        await self.maps_aliases(ctx)
        await self.players_aliases(ctx)
        await self.teams_aliases(ctx)

    @aliases.command(name="maps")
    async def maps_aliases(self, ctx):
        """`{prefix}aliases maps` - *Lists all map aliases*"""
        embed = discord.Embed(title="Maps Aliases")
        maps = aliases.get_maps()
        if maps:
            maps_str = "```"
            for alias, label in maps.items():
                maps_str += f"{alias:<15} - {label}\n"
            maps_str += "```"
            embed.description = maps_str
        else:
            embed.description = "No aliases exist for maps."
        await ctx.send(embed=embed)

    @aliases.command(name="players")
    async def players_aliases(self, ctx):
        """`{prefix}aliases players` - *Lists all player aliases*"""
        embed = discord.Embed(title="Player Aliases")
        players = aliases.get_players()

        if players:
            players_str = "```"
            for alias, unique_id in players.items():
                players_str += f"{alias:<15} <{unique_id}>\n"
            players_str += "```"
            embed.description = players_str
        else:
            embed.description = "No aliases exist for players."
        await ctx.send(embed=embed)

    @aliases.command(name="teams")
    async def teams_aliases(self, ctx):
        """`{prefix}aliases teams` - *Lists all teams like* `{prefix}teams`"""
        teams_cog = self.bot.get_cog("Teams")
        await teams_cog.teams(ctx)

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
    async def blacklist(self, ctx, server_name: str):
        """`{prefix}blacklist <server_name>` 

        **Example**: `{prefix}blacklist rush`
        """
        data = await exec_server_command(ctx, server_name, "Blacklist")
        black_list = data.get("BlackList")
        embed = discord.Embed(description=f"**Blacklisted players** on `{server_name}`:\n")
        if len(black_list) == 0:
            embed.description = f"Currently no Blacklisted players on `{server_name}`"
        for player in black_list:
            embed.description += (
                f"\n - <{str(player)}>"
            )
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def itemlist(self, ctx, server_name: str):
        """`{prefix}itemlist <servername>` 

        **Example**: `{prefix}itemlist snd1`
        """
        data = await exec_server_command(ctx, server_name, "ItemList")
        item_list = data.get("ItemList")
        embed = discord.Embed(description=f"Items available:\n")
        if len(item_list) == 0:
            embed.description = f"Currently no Items available"
        for item in item_list:
            embed.description += (
                f"\n - <{str(item)}>"
            )
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def maplist(self, ctx, server_name: str):
        """`{prefix}maplist <server_name>`

        **Example**: `{prefix}maplist rush`
        """
        data = await exec_server_command(ctx, server_name, "MapList")
        map_list = data.get("MapList")
        embed = discord.Embed(description=f"**Active maps** on `{server_name}`:\n")
        if len(map_list) == 0:
            embed.description = f"Currently no active maps on `{server_name}`"
        for map in map_list:
            embed.description += (
                f"\n - {map.get('MapId', '')} <{map.get('GameMode')}>"
            )
        if ctx.batch_exec:
            return embed.description
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

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}rotatemap rush`
        """
        if not await check_perm_captain(ctx, server_name):
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
    async def kill(self, ctx, player_arg: str, server_name: str):
        """`{prefix}kill <player_id> <server_name>`

        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kill 89374583439127 rush`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Kill {player.unique_id}")
        kill = data.get("Kill")
        if ctx.batch_exec:
            return kill
        if not kill:
            embed = discord.Embed(
                description=f"**Failed** to kill <{player.unique_id}>"
            )
        else:
            embed = discord.Embed(
                description=f"<{player.unique_id}> successfully killed"
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
        """`{prefix}matchsetup <CT team name> <T team name> <server name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}matchsetup ct_team t_team rush`
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
                    ctx, server_name, f"SwitchTeam {member.unique_id} {index}"
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
            try:
                data = await exec_server_command(ctx, server_alias, "ServerInfo")
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
                    server_name=server_name,
                    map_name=map_name,
                    map_alias=map_alias,
                    player_count=players_count,
                )
                desc += "\n"
            except (ConnectionRefusedError, OSError, TimeoutError):
                desc += ANYONEPLAYING_ROW_FORMAT.format(
                    alias=server_alias,
                    server_name="SERVER UNAVAILABLE",
                    map_name="N/A",
                    map_alias="N/A",
                    player_count="N/A",
                )
                desc += "\n"
        file = text_to_image(desc, "anyoneplaying.png")
        await ctx.send(file=file)


def setup(bot):
    bot.add_cog(Pavlov(bot))
