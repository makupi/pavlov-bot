import logging
import random
import re
import sys
import traceback
from asyncio.exceptions import TimeoutError
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands

from bot.utils import Paginator, aliases, servers, config
from bot.utils.pavlov import exec_server_command
from bot.utils.steamplayer import SteamPlayer
from bot.utils.text_to_image import text_to_image
from bs4 import BeautifulSoup

# Admin – GiveItem, GiveCash, GiveTeamCash, SetPlayerSkin
# Mod – Ban, Kick, Unban, RotateMap, SwitchTeam
# Captain – SwitchMap, ResetSND
# Everyone - RefreshList, InspectPlayer, ServerInfo
# Ban – Told to fuck off


ANYONEPLAYING_ROW_FORMAT = (
    "{alias:^15} | {server_name:^36.36} | {map_name:^36.36} "
    "| {map_alias:^15} | {player_count:^6}"
)


async def fetch(session, url):
    response = await session.get(url)
    try:
        return await response.text()
    except aiohttp.ContentTypeError:
        return None


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
            logging.error(f"Getting map label {map_label} failed with {ex}")
        return None, None

    @commands.command()
    async def servers(self, ctx):
        """`{prefix}servers` - *Lists available servers*"""
        server_names = servers.get_names()
        embed = discord.Embed(title="Servers", description="\n- ".join([""] + server_names))
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
        paginator = Paginator(max_lines=20)
        if maps:
            for alias, label in maps.items():
                paginator.add_line(f"{alias:<15} - {label}")
            await paginator.create(ctx, embed=embed)
        else:
            embed.description = "No aliases exist for maps."
            await ctx.send(embed=embed)

    @aliases.command(name="players")
    async def players_aliases(self, ctx):
        """`{prefix}aliases players` - *Lists all player aliases*"""
        embed = discord.Embed(title="Player Aliases")
        players = aliases.get_players()
        paginator = Paginator(max_lines=20)
        if players:
            for alias, unique_id in players.items():
                paginator.add_line(f"{alias:<15} <{unique_id}>")
            await paginator.create(ctx, embed=embed)
        else:
            embed.description = "No player aliases found."
            await ctx.send(embed=embed)

    @aliases.command(name="teams")
    async def teams_aliases(self, ctx):
        """`{prefix}aliases teams` - *Lists all teams like* `{prefix}teams`"""
        teams_cog = self.bot.get_cog("Teams")
        await teams_cog.teams(ctx)

    @commands.command()
    async def serverinfo(self, ctx, server_name: str = config.default_server):
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
        embed.add_field(name="Server Name", value=server_info.get("ServerName"), inline=False)
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
    async def blacklist(self, ctx, server_name: str = config.default_server):
        """`{prefix}blacklist <server_name> - Lists blacklisted players on a server`

        **Example**: `{prefix}blacklist rush`
        """
        data = await exec_server_command(ctx, server_name, "Blacklist")
        black_list = data.get("BlackList")
        embed = discord.Embed(title=f"Blacklisted players on `{server_name}`:")
        paginator = Paginator(max_lines=50)
        if black_list:
            for player in black_list:
                paginator.add_line(f"<{str(player)}>")
            await paginator.create(ctx, embed=embed)
        else: 
            embed.description = "No blacklist players found."
            await ctx.send(embed=embed)
           

    @commands.command()
    async def itemlist(self, ctx, server_name: str = config.default_server):
        """`{prefix}itemlist <servername>`

        **Example**: `{prefix}itemlist snd1`
        """
        data = await exec_server_command(ctx, server_name, "ItemList")
        item_list = data.get("ItemList")
        embed = discord.Embed(description=f"Items available:\n")
        if len(item_list) == 0:
            embed.description = f"Currently no Items available"
        for item in item_list:
            embed.description += f"\n - <{str(item)}>"
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()  # Exceeds Helptext embed, maplist hidden for now
    async def maplist(self, ctx, server_name: str = config.default_server):
        """`{prefix}maplist <server_name>`

        **Example**: `{prefix}maplist rush`
        """
        data = await exec_server_command(ctx, server_name, "MapList")
        map_list = data.get("MapList")
        embed = discord.Embed(description=f"**Active maps** on `{server_name}`:\n")
        if len(map_list) == 0:
            embed.description = f"Currently no active maps on `{server_name}`"
        for _map in map_list:
            embed.description += f"\n - {_map.get('MapId', '')} <{_map.get('GameMode')}>"
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def players(self, ctx, server_name: str = config.default_server):
        """`{prefix}players <server_name>`

        **Example**: `{prefix}players rush`
        """
        data = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = data.get("PlayerList")
        embed = discord.Embed(description=f"**Active players** on `{server_name}`:\n")
        if len(player_list) == 0:
            embed.description = f"Currently no active players on `{server_name}`"
        for player in player_list:
            embed.description += f"\n - {player.get('Username', '')} <{player.get('UniqueId')}>"
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def playerinfo(self, ctx, player_arg: str, server_name: str = config.default_server):
        """`{prefix}playerinfo <player_id> <server_name>`

        **Example**: `{prefix}playerinfo 89374583439127 rush`
        """
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"InspectPlayer {player.unique_id}")
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
                map_name, _ = await self.get_map_alias(map_label)
                map_alias = aliases.find_map_alias(map_label)
                if not map_name:
                    map_name = ""
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
