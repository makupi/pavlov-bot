import functools
import logging
import re
import sys
import traceback
from asyncio.exceptions import TimeoutError
from datetime import datetime

from async_lru import alru_cache

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from discord import app_commands

from bot.utils import Paginator, aliases, config, servers
from bot.utils.pavlov import exec_server_command
from bot.utils.players import (
    get_stats,
)
from bot.utils.steamplayer import SteamPlayer
from bot.utils.text_to_image import text_to_image

# Admin – GiveItem, GiveCash, GiveTeamCash, SetPlayerSkin
# Mod – Ban, Kick, Unban, RotateMap, SwitchTeam
# Captain – SwitchMap, ResetSND
# Everyone - RefreshList, InspectPlayer, ServerInfo
# Ban – Told to fuck off


ANYONEPLAYING_ROW_FORMAT = (
    "{alias:^15} | {server_name:^36.36} | {map_name:^36.36} "
    "| {map_alias:^15} | {player_count:^6}"
)

PUSHSERVER_ROW_FORMAT = (
    "{server_name:^46.46} | {map_name:^36.36} "
    "| {player_max:^15} | {player_count:^6}"
)

class Pavlov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession = bot.session

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @alru_cache # automatically cache modio api response
    async def get_map_alias(self, map_label: str) -> [str, str]:
        if "UGC" in map_label:
            try:
                map_id = map_label.split("UGC")[1]
                async with self.session as client:
                    async with client.get(f"{config.apiPATH}/games/3959/mods/{map_id}?api_key={config.apiKEY}") as resp:
                        data = await resp.json()
                        map_name = data.get("name")
                        map_image = data.get("logo", {}).get("original")
                        return map_name, map_image
            except Exception as ex:
                logging.error(f"Getting map label {map_label} failed with {ex}")
        return None, None

    @app_commands.command(name="servers")
    @app_commands.guild_only()
    async def list_servers(self, interaction: discord.Interaction):
        """Lists all available servers"""
        server_names = servers.get_names()
        if not server_names:
            return await interaction.response.send_message("No servers found.")
        # embed = discord.Embed(title="Servers", description="\n- ".join([""] + server_names))
        await interaction.response.send_message(f"Available Servers: {", ".join(server_names)}.")

    aliases = app_commands.Group(name="aliases", description="List aliases")

    @aliases.command(name="maps")
    @commands.guild_only()
    async def maps_aliases(self, interaction: discord.Interaction):
        """Lists all map aliases"""
        maps = aliases.get_maps()
        if not maps:
            return await interaction.response.send_message("No map aliases found.")

        msg = ""
        for alias, label in maps.items():
            msg += f"{alias} - {label}\n"
        await interaction.response.send_message(msg)

    @aliases.command(name="players")
    @commands.guild_only()
    async def players_aliases(self, interaction: discord.Interaction):
        """Lists all player aliases"""
        players = aliases.get_players()
        if not players:
            return await interaction.response.send_message("No player aliases found.")

        msg = ""
        for alias, unique_id in players.items():
            msg += f"{alias} - {unique_id}\n"
        await interaction.response.send_message(msg)

    @app_commands.command()
    @commands.guild_only()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.rename(server_name="server-name")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def serverinfo(self, interaction: discord.Interaction, server_name: str = config.default_server):
        """`{prefix}serverinfo <server_name>` - *Provides details on server*

        **Example**: `{prefix}serverinfo rush`
        """
        logging.info(f"Server info for {server_name}")
        data, _ = await exec_server_command(server_name, "ServerInfo")
        server_info = data.get("ServerInfo")
        map_label = server_info.get("MapLabel")
        map_name, map_image = await self.get_map_alias(map_label)
        map_alias = aliases.find_map_alias(map_label)
        embed = discord.Embed(title=f"**ServerInfo** for `{server_name}`")
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
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def banlist(self, interaction: discord.Interaction, server_name: str = config.default_server):
        """`{prefix}banlist <server_name>` - *Lists banned players on a server*

        **Example**: `{prefix}banlist rush`
        """
        data, _ = await exec_server_command(server_name, "Banlist")
        black_list = data.get("BanList")
        embed = discord.Embed(title=f"Banned players on `{server_name}`:")
        paginator = Paginator(max_lines=50)
        if black_list:
            for player in black_list:
                paginator.add_line(f"<{str(player)}>")
            await paginator.create(interaction, embed=embed)
        else:
            embed.description = "No banned players found."
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.describe(player="The player id you want to check")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def checkban(self, interaction: discord.Interaction, player: str, server_name: str = config.default_server):
        """`{prefix}checkban <playerid> <server_name>` - *Lists banned players on a server*

        **Example**: `{prefix}checkban invicta push`
        """
        embed = discord.Embed(title=f"Looking for {player} on `{server_name}` banlist:")
        data, _ = await exec_server_command(server_name, "Banlist")
        black_list = data.get("BanList")
        if black_list:
            if player in black_list:
                embed.description = "Player is banned... naughty boy found."
            else:
                embed.description = "Player is not banned."
        else:
            embed.description = "No banned players found."
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def itemlist(self, interaction: discord.Interaction, server_name: str = config.default_server):
        """`{prefix}itemlist <servername>` - *Lists available items on a server*

        **Example**: `{prefix}itemlist snd1`
        """
        data, _ = await exec_server_command(server_name, "ItemList")
        item_list = data.get("ItemList")
        embed = discord.Embed(title=f"Items available:")
        embed.description = "\n"
        if len(item_list) == 0:
            embed.description = f"Currently no Items available"
        for item in item_list:
            embed.description += f"\n - <{str(item)}>"
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def maplist(self, interaction: discord.Interaction, server_name: str = config.default_server):
        """`{prefix}maplist <server_name>` - *Lists configured maps on a server*

        **Example**: `{prefix}maplist rush`
        """
        data, _ = await exec_server_command(server_name, "MapList")
        map_list = data.get("MapList")
        embed = discord.Embed(title=f"**Active maps** on `{server_name}`:")
        embed.description = "\n"
        if len(map_list) == 0:
            embed.description = f"Currently no active maps on `{server_name}`"
        for _map in map_list:
            map_label = _map.get('MapId')
            map_name, map_image = await self.get_map_alias(map_label)
            embed.description += f"\n {map_name} <{_map.get('GameMode')}>  {_map.get('MapId', '')}"
        # if ctx.batch_exec:
        #     return embed.description
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def players(
            self,
            interaction: discord.Interaction,
            server_name: str = config.default_server,
    ):
        """`{prefix}players <server_name>` - *Provides a scoreboard with player info*

        **Example**: `{prefix}players rush`
        """
        data, _ = await exec_server_command(server_name, "RefreshList")
        server_data, _ = await exec_server_command(server_name, "ServerInfo")
        players = data.get("PlayerList")
        blue_score = server_data.get("ServerInfo").get("Team0Score")
        red_score = server_data.get("ServerInfo").get("Team1Score")
        game_round = server_data.get("ServerInfo").get("Round")
        game_mode = server_data.get("ServerInfo").get("GameMode")
        map_label = server_data.get("ServerInfo").get("MapLabel")
        map_alias = aliases.find_map_alias(map_label)
        map_name = map_label
        if map_alias is not None:
            map_name = map_alias

        embed = discord.Embed(
            title=f"{len(players)} player{'s' if len(players) != 1 else ''} on `{server_name}`\n"
        )
        if game_mode == "SND":
            embed.description = f"Round {game_round} on map {map_name}\n\n"
        else:
            embed.description = f"Playing {game_mode.upper()} on map `{map_name}`\n\n"
        team_blue, team_red, kda_list, alive_list, scores, _ = await get_stats(ctx, server_name)
        if len(team_red) == 0:
            for player in players:
                if player.get("UniqueId") == '' or player.get('Username') == '':
                    continue
                dead = ""
                if alive_list.get(player.get("UniqueId")):
                    dead = ":skull:"
                elif not alive_list.get(player.get("UniqueId")):
                    dead = ":slight_smile:"
                embed.description += (
                    f"- {dead} **{player.get('Username')}** `<{player.get('UniqueId')}>` "
                    f"**KDA**: {kda_list.get(player.get('UniqueId'))}\n"
                )
        else:
            score_name = "Score"
            if game_mode.upper() == "PUSH":
                score_name = "Tickets"

            teams = ["blue", "red"]
            for team in teams:
                embed.description += f"**Team {team.capitalize()} {score_name}: "
                if team == "blue":
                    embed.description += f"{blue_score}**\n"
                if team == "red":
                    embed.description += f"{red_score}**\n"
                team_name = f":{team}_circle:"
                team_list = team_blue if team == "blue" else team_red
                dead = ""
                user_name = "N/A"
                for player in team_list:
                    if alive_list.get(player):
                        dead = ":skull:"
                    elif not alive_list.get(player):
                        dead = ":slight_smile:"
                    for p in players:
                        if player == p.get("UniqueId"):
                            user_name = p.get("Username")
                    embed.description += (
                        f"- {dead} {team_name} **{user_name}** `<{player}>` "
                        f"**KDA**: {kda_list.get(player)}\n"
                    )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(server_name="The name of the server to get info for, if not given chooses default")
    @app_commands.describe(player="The player id you want to check")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def playerinfo(
        self,
        interaction: discord.Interaction,
        player: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}playerinfo <player_id> <server_name>` - *Player details*

        **Example**: `{prefix}playerinfo 89374583439127 rush`
        """
        player = SteamPlayer.convert(player)
        data, _ = await exec_server_command(server_name, f"InspectPlayer {player.unique_id}")
        player_info = data.get("PlayerInfo")
        # if ctx.batch_exec:
        #     return player_info
        if not player_info:
            embed = discord.Embed(
                title=f"Player <{player.unique_id}> not found on `{server_name}`."
            )
        else:
            embed = discord.Embed(title=f"**Player info** for `{player.name}`")
            embed.add_field(name="Name", value=player_info.get("PlayerName"))
            embed.add_field(name="UniqueId", value=player_info.get("UniqueId"))
            embed.add_field(name="KDA", value=player_info.get("KDA"))
            embed.add_field(name="Cash", value=player_info.get("Cash"))
            embed.add_field(name="TeamId", value=player_info.get("TeamId"))
            if hasattr(player, "has_alias"):
                if player.has_alias:
                    embed.add_field(name="Alias", value=player.name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def anyoneplaying(self, interaction: discord.Interaction):
        """`{prefix}anyoneplaying` - *Provides a table with info for all servers*"""
        players_header = ANYONEPLAYING_ROW_FORMAT.format(
            alias="Alias",
            server_name="Server Name",
            map_name="Map Name",
            map_alias="Map Alias",
            player_count="Players",
        )
        desc = f"\n{players_header}\n{'-'*len(players_header)}\n"
        for server_alias in servers.get_names():
            try:
                data, _ = await exec_server_command(server_alias, "ServerInfo")
                server_info = data.get("ServerInfo", {})
                players_count = server_info.get("PlayerCount", "0/0")
                server_name = server_info.get("ServerName", "")
                map_label = server_info.get("MapLabel")
                if map_label.startswith("SVR"):
                    map_name = map_label
                else:
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
        await interaction.response.send_message(file=file)

    @app_commands.command()
    async def pushservers(self, interaction: discord.Interaction):
        """`{prefix}pushservers` - *Provides a table with info for all push servers*"""
        players_header = PUSHSERVER_ROW_FORMAT.format(
            server_name="Server Name",
            map_name="Map Name",
            player_max="Max Players",
            player_count="Players",
        )
        desc = f"\n{players_header}\n{'-' * len(players_header)}\n"

        try:
            async with self.session as client:
                async with client.get(f"{config.pav_push_URL}") as resp:
                    data = await resp.json()
            for server in data.get("servers", []):
                players_count = server["slots"]
                players_max = server["maxSlots"]
                server_name = server["name"]
                map_name = server["mapLabel"]

                desc += PUSHSERVER_ROW_FORMAT.format(
                    server_name=server_name,
                    map_name=map_name,
                    player_max=players_max,
                    player_count=players_count,
                )
                desc += "\n"
        except (ConnectionRefusedError, OSError, TimeoutError):
            desc += PUSHSERVER_ROW_FORMAT.format(
                server_name="SERVER UNAVAILABLE",
                map_name="N/A",
                player_max="N/A",
                player_count="N/A",
            )
            desc += "\n"
        file = text_to_image(desc, "anyoneplaying.png")
        await interaction.response.send_message(file=file)


async def setup(bot):
    await bot.add_cog(Pavlov(bot))
