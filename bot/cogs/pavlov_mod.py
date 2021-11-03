import asyncio
import logging
from datetime import datetime

import discord
from discord.ext import commands

from bot.utils import SteamPlayer, config
from bot.utils.pavlov import check_perm_moderator, exec_server_command
from bot.utils.players import (
    exec_command_all_players,
    exec_command_all_players_on_team,
    parse_player_command_results,
    spawn_pselect,
)


class PavlovMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def ban(self, ctx, player_arg: str, server_name: str = config.default_server):
        """`{prefix}ban <player_id> <server_name>`
        **Description**: Adds a player to blacklist.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}ban 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Ban {player.unique_id}")
        embed = discord.Embed(title=f"**Ban {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        await ctx.send(embed=embed)

    @commands.command()
    async def kill(
        self, ctx, player_arg: str, server_name: str = config.default_server, interaction: str = ""
    ):
        """`{prefix}kill <player_id/all/team> <server_name>`
        **Description**: Kills a player.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kill 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, interaction = await spawn_pselect(self, ctx, server_name, interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await interaction.send(embed=embed)
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
                data = await exec_server_command(ctx, server_name, f"Kill {player_arg}")
            else:
                player = SteamPlayer.convert(player_arg)
                data = await exec_server_command(ctx, server_name, f"Kill {player.unique_id} ")
        embed = discord.Embed(title=f"**Kill {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await interaction.send(embed=embed)
            return
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def kick(self, ctx, player_arg: str, server_name: str = config.default_server):
        """`{prefix}kick <player_id> <server_name>`
        **Description**: Kicks a player from the specified server.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}kick 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Kick {player.unique_id}")
        embed = discord.Embed(title=f"**Kick {player_arg} ** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        await ctx.send(embed=embed)

    @commands.command()
    async def unban(self, ctx, player_arg: str, server_name: str = config.default_server):
        """`{prefix}unban <player_id> <server_name>`
        **Description**: Removes a player from blacklist.txt
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}unban 89374583439127 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(ctx, server_name, f"Unban {player.unique_id}")
        embed = discord.Embed(title=f"**Unban {player_arg} ** \n")
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
        data = await exec_server_command(ctx, server_name, f"AddMod {player.unique_id}")
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
        data = await exec_server_command(ctx, server_name, f"RemoveMod {player.unique_id}")
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
        interaction: str = "",
    ):
        """`{prefix}slap <player_id/all/team> <damage_amount> <server_name>`
        **Description**: Slaps a player for a specified damage amount.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}slap 89374583439127 10 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, interaction = await spawn_pselect(self, ctx, server_name, interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await interaction.send(embed=embed)
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
                data = await exec_server_command(ctx, server_name, f"Slap {player_arg} {dmg}")
            else:
                player = SteamPlayer.convert(player_arg)
                data = await exec_server_command(ctx, server_name, f"Slap {player.unique_id} {dmg}")
        embed = discord.Embed(title=f"**Slap {player_arg} {dmg}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        elif ctx.interaction_exec:
            await interaction.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @commands.command()
    async def setpin(self, ctx, pin: str, server_name: str = config.default_server):
        """`{prefix}setpin <pin> <server_name>`
        **Description**: Sets a password for your server. Must be 4-digits.
        **Requires**: Moderator permissions or higher for the server
        **Example**: `{prefix}setpin 0000 servername`
        """
        if not await check_perm_moderator(ctx, server_name):
            return
        if len(pin) == 4 and pin.isdigit():
            data = await exec_server_command(ctx, server_name, f"SetPin {pin}")
        elif pin.lower() == "remove":
            data = await exec_server_command(ctx, server_name, f"SetPin")
        else:
            embed = discord.Embed(title=f"Pin must be either a 4-digit number or remove")
            await ctx.send(embed=embed)
            return
        spin = data.get("Successful")
        if ctx.batch_exec:
            return spin
        if not spin:
            embed = discord.Embed(title=f"**Failed** to set pin {pin}")
        else:
            if pin.lower() == "remove":
                embed = discord.Embed(title=f"Pin removed")
            else:
                embed = discord.Embed(title=f"Pin {pin} successfully set")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PavlovMod(bot))
