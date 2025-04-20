import logging

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from bot.utils import SteamPlayer, config, servers
from bot.utils.pavlov import check_perm_moderator, exec_server_command
from bot.utils.players import (
    exec_command_all_players,
    exec_command_all_players_on_team,
    parse_player_command_results,
)


class PavlovMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def ban(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}ban <player_id> <server_name/all>`
        **Description**: Adds a player to blacklist.txt on a server. If "all" is given, bans on all servers
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}ban 89374583439127 servername`
        """
        if server_name.casefold() != "all":
            if not await check_perm_moderator(interaction, server_name):
                return

        player = SteamPlayer.convert(player_arg)
        banned_servers = []
        if server_name.casefold() == "all":
            for server in servers.get_names():
                if not await check_perm_moderator(interaction, server):
                    pass
                else:
                    data, _ = await exec_server_command(server, f"Ban {player.unique_id}")
                    banned_servers.append(server)
        else:
            data, _ = await exec_server_command(server_name, f"Ban {player.unique_id}")
            banned_servers.append(server_name)
        embed = discord.Embed(title=f"**Ban {player_arg} {' '.join(banned_servers)}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def kill(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}kill <player_id/all/team> <server_name>`
        **Description**: Kills a player, or a team or all players
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kill 89374583439127 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return

        if player_arg.casefold() == "all":
            data = await exec_command_all_players(server_name, f"Kill all ")
        elif player_arg.startswith("team"):
            data = await exec_command_all_players_on_team(
                server_name, player_arg, f"Kill team "
            )
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(server_name, f"Kill {player.unique_id} ")
        embed = discord.Embed(title=f"**Kill {player_arg} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def kick(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}kick <player_id> <server_name>`
        **Description**: Kicks a player from the specified server.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kick 89374583439127 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data, _ = await exec_server_command(server_name, f"Kick {player.unique_id}")
        embed = discord.Embed(title=f"**Kick {player_arg} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def unban(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}ban <player_id> <server_name>`
        **Description**: Removes a player from blacklist.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}unban 89374583439127 servername`
        """
        if server_name.casefold() != "all":
            if not await check_perm_moderator(interaction, server_name):
                return
        player = SteamPlayer.convert(player_arg)
        unbanned_servers = []
        if server_name.casefold() == "all":
            for server in servers.get_names():
                if not await check_perm_moderator(interaction, server):
                    pass
                else:
                    data, _ = await exec_server_command(server, f"Unban {player.unique_id}")
                    unbanned_servers.append(server)
        else:
            data, _ = await exec_server_command(server_name, f"Unban {player.unique_id}")
            unbanned_servers.append(server_name)
        embed = discord.Embed(title=f"**Unban {player_arg} {' '.join(unbanned_servers)}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def gag(self, interaction: discord.Interaction, player_arg: str, server_name: str = config.default_server):
        """`{prefix}gag <player_id> <server_name>`
        **Description**: Globally mutes a player
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}gag 89374583439127 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data, _ = await exec_server_command(server_name, f"Gag {player.unique_id}")
        embed = discord.Embed(title=f"**Gag {player_arg} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def addmod(self, interaction: discord.Interaction, player_arg: str, server_name: str = config.default_server):
        """`{prefix}addmod <player_id> <server_name>`
        **Description**: Adds a player to mods.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}addmod 89374583439127 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data, _ = await exec_server_command(server_name, f"AddMod {player.unique_id}")
        embed = discord.Embed(title=f"**AddMod {player_arg} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def removemod(self, interaction: discord.Interaction, player_arg: str, server_name: str = config.default_server):
        """`{prefix}removemod <player_id> <server_name>`
        **Description**: Removes a player from mods.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}removemod 89374583439127 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data, _ = await exec_server_command(server_name, f"RemoveMod {player.unique_id}")
        embed = discord.Embed(title=f"**RemoveMod {player_arg} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(dmg="The amount of damage the slap should do")
    @app_commands.rename(player_arg="player", server_name="server")
    async def slap(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        dmg: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}slap <player_id/all/team> <damage_amount> <server_name>`
        **Description**: Slaps a player for a specified damage amount.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}slap 89374583439127 10 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(server_name, f"Slap all {dmg}")
        elif player_arg.startswith("team"):
            data = await exec_command_all_players_on_team(
                server_name, player_arg, f"Slap team {dmg}"
            )
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"Slap {player.unique_id} {dmg}"
            )
        embed = discord.Embed(title=f"**Slap {player_arg} {dmg}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(karma="The amount of karma")
    @app_commands.rename(player_arg="player", server_name="server")
    async def tttsetkarma(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        karma: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}tttsetkarma <player_id/all> <karma_amount> <server_name>`
        **Description**: Sets the amount of karma a player has.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttsetkarma 89374583439127 1100 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(server_name, f"tttsetkarma all {karma}")
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"tttsetkarma {player.unique_id} {karma}"
            )
        embed = discord.Embed(title=f"**TTTSetKarma {player_arg} {karma}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", server_name="server")
    async def tttflushkarma(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}tttflushkarma <player_id/all> <server_name>`
        **Description**: Resets a player's karma.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttflushkarma 89374583439127 servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(server_name, f"tttflushkarma all ")
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"tttflushkarma {player.unique_id}"
            )
        embed = discord.Embed(title=f"**tttflushkarma {player_arg}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(server_name="server")
    async def tttendround(self, interaction: discord.Interaction, server_name: str = config.default_server):
        """`{prefix}tttendround server_name`
        **Description**: Ends the current TTT round.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttendround servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, f"tttendround")
        if not data:
            data = "No response"
        if data.get("TTTEndRound"):
            embed = discord.Embed(title=f"**TTT round ended!** \n")
        else:
            embed = discord.Embed(title=f"**Failed to end TTT round!** \n")
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(pause="Whether to pause or unpause the timer")
    @app_commands.rename(server_name="server")
    @app_commands.choices(pause=[app_commands.Choice(name="pause", value="true"), app_commands.Choice(name="unpause", value="false")])
    async def tttpausetimer(self, interaction: discord.Interaction, pause: str, server_name: str = config.default_server):
        """`{prefix}tttpausetimer pause/unpause/true/false server_name`
        **Description**: Pauses/unpauses the TTT round timer.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttpausetimer pause servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, f"TTTPauseTimer {pause}")
        if not data:
            data = "No response"
        if data.get("TTTPauseState"):
            embed = discord.Embed(title=f"**TTT round timer paused!** \n")
        else:
            embed = discord.Embed(title=f"**TTT round timer unpaused!** \n")
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(enable="Whether to enable or disable the skin menu")
    @app_commands.rename(server_name="server")
    @app_commands.choices(enable=[app_commands.Choice(name="enable", value="true"), app_commands.Choice(name="disable", value="false")])
    async def tttalwaysenableskinmenu(self, interaction: discord.Interaction, enable: str, server_name: str = config.default_server):
        """`{prefix}tttalwaysenableskinmenu enable/disable/true/false server_name`
        **Description**: Enables/disables skin menu during a TTT round.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttalwaysenableskinmenu enable servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, f"TTTAlwaysEnableSkinMenu {enable}")
        if not data:
            data = "No response"
        if data.get("TTTSkinMenuState"):
            embed = discord.Embed(title=f"**Skin menu enabled during mid-round!** \n")
        else:
            embed = discord.Embed(title=f"**Skin menu disabled during mid-round!** \n")
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(map_id="ID of the map to add", game_mode="Game mode for the map")
    @app_commands.rename(server_name="server")
    async def addmap(self, interaction: discord.Interaction, map_id: int, game_mode: str, server_name: str = config.default_server):
        """`{prefix}addmap <map_id> <gamemode> <server_name>`
        **Description**: Adds map to game rotation
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}addmap UGC12345657 PUSH servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, f"AddMapRotation {map_id} {game_mode}")
        embed = discord.Embed(title=f"**AddMapRotation {map_id} {game_mode} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(map_id="ID of the map to remove", game_mode="Game mode for the map")
    @app_commands.rename(server_name="server")
    async def removemap(self, interaction: discord.Interaction, map_id: str, game_mode: str, server_name: str = config.default_server):
        """`{prefix}removemap <map_id> <gamemode> <server_name>`
        **Description**: Removes map from game rotation
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}removemap UGC12345657 PUSH servername`
        """
        if not await check_perm_moderator(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, f"RemoveMapRotation {map_id} {game_mode}")
        embed = discord.Embed(title=f"**RemoveMapRotation {map_id} {game_mode} ** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PavlovMod(bot))
