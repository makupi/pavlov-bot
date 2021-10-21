import asyncio
import logging
import random
from datetime import datetime

import discord
from discord.ext import commands

from bot.utils import SteamPlayer, aliases, config
from bot.utils.pavlov import check_perm_captain, exec_server_command
from bot.utils.players import (
    exec_command_all_players,
    exec_command_all_players_on_team,
    parse_player_command_results,
)


MATCH_DELAY_RESETSND = 10
RCON_COMMAND_PAUSE = 100 / 1000  # milliseconds


class PavlovCaptain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command(aliases=["map"])
    async def switchmap(
        self,
        ctx,
        map_name: str,
        game_mode: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}switchmap <map_name> <game_mode> <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}switchmap 89374583439127 servername`
        **Alias**: switchmap can be shortened to just map `{prefix}map 89374583439127 servername`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        map_label = aliases.get_map(map_name)
        data = await exec_server_command(
            ctx, server_name, f"SwitchMap {map_label} {game_mode.upper()}"
        )
        switch_map = data.get("SwitchMap")
        if ctx.batch_exec:
            return switch_map
        if not switch_map:
            embed = discord.Embed(
                title=f"**Failed** to switch map to {map_name} with game mode {game_mode.upper()}"
            )
        else:
            embed = discord.Embed(
                title=f"Switched map to {map_name} with game mode {game_mode.upper()}"
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def resetsnd(self, ctx, server_name: str = config.default_server):
        """`{prefix}resetsnd <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}resetsnd servername`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        data = await exec_server_command(ctx, server_name, "ResetSND")
        reset_snd = data.get("ResetSND")
        if ctx.batch_exec:
            return reset_snd
        if not reset_snd:
            embed = discord.Embed(title=f"**Failed** reset SND")
        else:
            embed = discord.Embed(title=f"SND successfully reset")
        await ctx.send(embed=embed)

    @commands.command()
    async def switchteam(
        self,
        ctx,
        player_arg: str,
        team_id: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}switchteam <player_id> <team_id> <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}resetsnd 89374583439127 0 servername`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"SwitchTeam {player.unique_id} {team_id}"
        )
        embed = discord.Embed(title=f"**SwitchTeam {player_arg} {team_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        await ctx.send(embed=embed)

    @commands.command(aliases=["next"])
    async def rotatemap(self, ctx, server_name: str = config.default_server):
        """`{prefix}rotatemap <server_name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}rotatemap servername`
        **Aliases**: rotatemap can also be called as next `{prefix}next servername`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        data = await exec_server_command(ctx, server_name, f"RotateMap")
        rotate_map = data.get("RotateMap")
        if ctx.batch_exec:
            return rotate_map
        if not rotate_map:
            embed = discord.Embed(title=f"**Failed** to rotate map")
        else:
            embed = discord.Embed(title=f"Rotated map successfully")
        await ctx.send(embed=embed)

    @commands.command()
    async def matchsetup(
        self,
        ctx,
        team_a_name: str,
        team_b_name: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}matchsetup <CT team name> <T team name> <server name>`

        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}matchsetup ct_team t_team servername`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        before = datetime.now()
        teams = [aliases.get_team(team_a_name), aliases.get_team(team_b_name)]
        embed = discord.Embed()
        for team in teams:
            embed.add_field(name=f"{team.name} members", value=team.member_repr(), inline=False)
        await ctx.send(embed=embed)

        for index, team in enumerate(teams):
            for member in team.members:
                await exec_server_command(
                    ctx, server_name, f"SwitchTeam {member.unique_id} {index}"
                )
                await asyncio.sleep(RCON_COMMAND_PAUSE)

        await ctx.send(
            embed=discord.Embed(
                title=f"Teams set up. Resetting SND in {MATCH_DELAY_RESETSND} seconds."
            )
        )
        await asyncio.sleep(MATCH_DELAY_RESETSND)
        await exec_server_command(ctx, server_name, "ResetSND")
        embed = discord.Embed(title="Reset SND. Good luck!")
        embed.set_footer(text=f"Execution time: {datetime.now() - before}")
        await ctx.send(embed=embed)

    @commands.command()
    async def flush(self, ctx: commands.Context, server_name: str = config.default_server):
        """`{prefix}flush <servername>`
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}flush snd1`
        """
        if not await check_perm_captain(ctx, server_name):
            return
        data = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = data.get("PlayerList")
        non_alias_player_ids = list()
        for player in player_list:
            check = aliases.find_player_alias(player.get("UniqueId"))
            if check is None:
                non_alias_player_ids.append(player.get("UniqueId"))
        if len(non_alias_player_ids) == 0:
            await ctx.send(embed=discord.Embed(title=f"No players to flush on `{server_name}`"))
            return
        to_kick_id = random.choice(non_alias_player_ids)
        data = await exec_server_command(ctx, server_name, f"Kick {to_kick_id}")
        kick = data.get("Kick")
        if not kick:
            await ctx.send(
                embed=discord.Embed(title=f"Encountered error while flushing on `{server_name}`")
            )
        else:
            await ctx.send(embed=discord.Embed(title=f"Successfully flushed `{server_name}`"))


def setup(bot):
    bot.add_cog(PavlovCaptain(bot))
