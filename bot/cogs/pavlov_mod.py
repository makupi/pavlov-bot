import asyncio
import logging
from datetime import datetime

import discord
from discord.ext import commands

from bot.utils import SteamPlayer, config
from bot.utils.pavlov import check_perm_moderator, exec_server_command


class PavlovMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def ban(self, ctx, player_arg: str, server_name: str = config.default_server):
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
    async def kill(
        self, ctx, player_arg: str, server_name: str = config.default_server
    ):
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
    async def kick(
        self, ctx, player_arg: str, server_name: str = config.default_server
    ):
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
    async def unban(
        self, ctx, player_arg: str, server_name: str = config.default_server
    ):
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


def setup(bot):
    bot.add_cog(PavlovMod(bot))
