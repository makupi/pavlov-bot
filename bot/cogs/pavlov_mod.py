import logging

import discord
import discord_components
from discord.ext import commands

from bot.utils import SteamPlayer, config, servers
from bot.utils.interactions import spawn_player_select
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

    @commands.command()
    async def ban(
        self,
        ctx,
        player_arg: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}ban <player_id> <server_name/all>`
        **Description**: Adds a player to blacklist.txt on a server. If "all" is given, bans on all servers
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}ban 89374583439127 servername`
        """
        if server_name.casefold() != "all":
            if not await check_perm_moderator(ctx, server_name):
                return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
            data, _ = await exec_server_command(ctx, server_name, f"Ban {player_arg}")
        else:
            player = SteamPlayer.convert(player_arg)
            banned_servers = []
            if server_name.casefold() == "all":
                for server in servers.get_names():
                    if not await check_perm_moderator(ctx, server):
                        pass
                    else:
                        data, _ = await exec_server_command(ctx, server, f"Ban {player.unique_id}")
                        banned_servers.append(server)
            else:
                data, _ = await exec_server_command(ctx, server_name, f"Ban {player.unique_id}")
                banned_servers.append(server_name)
        embed = discord.Embed(title=f"**Ban {player_arg} {' '.join(banned_servers)}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def kill(
        self,
        ctx,
        player_arg: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}kill <player_id/all/team> <server_name>`
        **Description**: Kills a player, or a team or all players
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kill 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
        if player_arg.casefold() == "all" or player_arg.startswith("team"):
            if player_arg.casefold() == "all":
                data = await exec_command_all_players(ctx, server_name, f"Kill all ")
            elif player_arg.startswith("team"):
                data = await exec_command_all_players_on_team(
                    ctx, server_name, player_arg, f"Kill team "
                )
        else:
            if ctx.interaction_exec:
                data, _ = await exec_server_command(ctx, server_name, f"Kill {player_arg}")
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(ctx, server_name, f"Kill {player.unique_id} ")
        embed = discord.Embed(title=f"**Kill {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def kick(
        self,
        ctx,
        player_arg: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}kick <player_id> <server_name>`
        **Description**: Kicks a player from the specified server.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kick 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
            data, _ = await exec_server_command(ctx, server_name, f"Kick {player_arg}")
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(ctx, server_name, f"Kick {player.unique_id}")
        embed = discord.Embed(title=f"**Kick {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def unban(
        self,
        ctx,
        player_arg: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}ban <player_id> <server_name>`
        **Description**: Removes a player from blacklist.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}unban 89374583439127 servername`
        """
        if server_name.casefold() != "all":
            if not await check_perm_moderator(ctx, server_name):
                return
        player = SteamPlayer.convert(player_arg)
        unbanned_servers = []
        if server_name.casefold() == "all":
            for server in servers.get_names():
                if not await check_perm_moderator(ctx, server):
                    pass
                else:
                    data, _ = await exec_server_command(ctx, server, f"Unban {player.unique_id}")
                    unbanned_servers.append(server)
        else:
            data, _ = await exec_server_command(ctx, server_name, f"Unban {player.unique_id}")
            unbanned_servers.append(server_name)
        embed = discord.Embed(title=f"**Unban {player_arg} {' '.join(unbanned_servers)}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        await ctx.send(embed=embed)

    @commands.command()
    async def addmod(self, ctx, player_arg: str, server_name: str = config.default_server):
        """`{prefix}addmod <player_id> <server_name>`
        **Description**: Adds a player to mods.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}addmod 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data, _ = await exec_server_command(ctx, server_name, f"AddMod {player.unique_id}")
        embed = discord.Embed(title=f"**AddMod {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        await ctx.send(embed=embed)

    @commands.command()
    async def removemod(self, ctx, player_arg: str, server_name: str = config.default_server):
        """`{prefix}removemod <player_id> <server_name>`
        **Description**: Removes a player from mods.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}removemod 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data, _ = await exec_server_command(ctx, server_name, f"RemoveMod {player.unique_id}")
        embed = discord.Embed(title=f"**RemoveMod {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        await ctx.send(embed=embed)

    @commands.command()
    async def slap(
        self,
        ctx,
        player_arg: str,
        dmg: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}slap <player_id/all/team> <damage_amount> <server_name>`
        **Description**: Slaps a player for a specified damage amount.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}slap 89374583439127 10 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
        if player_arg.casefold() == "all" or player_arg.startswith("team"):
            if player_arg.casefold() == "all":
                data = await exec_command_all_players(ctx, server_name, f"Slap all {dmg}")
            elif player_arg.startswith("team"):
                data = await exec_command_all_players_on_team(
                    ctx, server_name, player_arg, f"Slap team {dmg}"
                )
        else:
            if ctx.interaction_exec:
                data, _ = await exec_server_command(ctx, server_name, f"Slap {player_arg} {dmg}")
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(
                    ctx, server_name, f"Slap {player.unique_id} {dmg}"
                )
        embed = discord.Embed(title=f"**Slap {player_arg} {dmg}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        elif ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def tttsetkarma(
        self,
        ctx,
        player_arg: str,
        karma: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}tttsetkarma <player_id/all> <karma_amount> <server_name>`
        **Description**: Sets the amount of karma a player has.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttsetkarma 89374583439127 1100 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
        if player_arg.casefold() == "all":
            if player_arg.casefold() == "all":
                data = await exec_command_all_players(ctx, server_name, f"tttsetkarma all {karma}")
        else:
            if ctx.interaction_exec:
                data, _ = await exec_server_command(
                    ctx, server_name, f"tttsetkarma {player_arg} {karma}"
                )
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(
                    ctx, server_name, f"tttsetkarma {player.unique_id} {karma}"
                )
        embed = discord.Embed(title=f"**TTTSetKarma {player_arg} {karma}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        elif ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def tttflushkarma(
        self,
        ctx,
        player_arg: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}tttflushkarma <player_id/all> <server_name>`
        **Description**: Resets a player's karma.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttflushkarma 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
        if player_arg.casefold() == "all":
            if player_arg.casefold() == "all":
                data = await exec_command_all_players(ctx, server_name, f"tttflushkarma all ")
        else:
            if ctx.interaction_exec:
                data, _ = await exec_server_command(ctx, server_name, f"tttflushkarma {player_arg}")
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(
                    ctx, server_name, f"tttflushkarma {player.unique_id}"
                )
        embed = discord.Embed(title=f"**tttflushkarma {player_arg}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        elif ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def tttendround(self, ctx, server_name: str = config.default_server):
        """`{prefix}tttendround server_name`
        **Description**: Ends the current TTT round.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttendround servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        data, _ = await exec_server_command(ctx, server_name, f"tttendround")
        if not data:
            data = "No response"
        if ctx.batch_exec:
            return data
        if data.get("TTTEndRound"):
            embed = discord.Embed(title=f"**TTT round ended!** \n")
        else:
            embed = discord.Embed(title=f"**Failed to end TTT round!** \n")
        await ctx.send(embed=embed)

    @commands.command()
    async def tttpausetimer(self, ctx, boolean, server_name: str = config.default_server):
        """`{prefix}tttpausetimer pause/unpause/true/false server_name`
        **Description**: Pauses/unpauses the TTT round timer.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttpausetimer pause servername`
        """
        if boolean.casefold() == "pause":
            boolean = "true"
        elif boolean.casefold() == "unpause":
            boolean = "false"
        if not await check_perm_moderator(ctx, server_name):
            return
        data, _ = await exec_server_command(ctx, server_name, f"TTTPauseTimer {boolean}")
        if not data:
            data = "No response"
        if ctx.batch_exec:
            return data
        if data.get("TTTPauseState"):
            embed = discord.Embed(title=f"**TTT round timer paused!** \n")
        else:
            embed = discord.Embed(title=f"**TTT round timer unpaused!** \n")
        await ctx.send(embed=embed)

    @commands.command()
    async def tttalwaysenableskinmenu(self, ctx, boolean, server_name: str = config.default_server):
        """`{prefix}tttalwaysenableskinmenu enable/disable/true/false server_name`
        **Description**: Enables/disables skin menu during a TTT round.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}tttalwaysenableskinmenu enable servername`
        """
        if boolean.casefold() == "enable":
            boolean = "true"
        elif boolean.casefold() == "disable":
            boolean = "false"
        if not await check_perm_moderator(ctx, server_name):
            return
        data, _ = await exec_server_command(ctx, server_name, f"TTTAlwaysEnableSkinMenu {boolean}")
        if not data:
            data = "No response"
        if ctx.batch_exec:
            return data
        if data.get("TTTSkinMenuState"):
            embed = discord.Embed(title=f"**Skin menu enabled during mid-round!** \n")
        else:
            embed = discord.Embed(title=f"**Skin menu disabled during mid-round!** \n")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(PavlovMod(bot))
