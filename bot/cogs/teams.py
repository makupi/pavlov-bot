import logging

import discord
from discord.ext import commands

from bot.utils import SteamPlayer, aliases, config
from bot.utils.pavlov import check_perm_captain


class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.group(pass_context=True, aliases=["ringer"])
    async def ringers(self, ctx):
        pass

    @commands.command()
    async def teamsetup(self, ctx, players_arg: str, team_name: str):
        """`{prefix}teamsetup <comma seperated list of unique_id or alias> <team_name>`

        **Examples**: `{prefix}teamsetup maku,invicta team_a`"""
        if not await check_perm_captain(ctx, global_check=True):
            return
        team = aliases.get_team(team_name)
        team.ringers_reset()
        players = players_arg.split(",")
        for player in players:
            player = SteamPlayer.convert(player)
            team.ringer_add(player)
        await ctx.send(
            embed=discord.Embed(description=f"Player list {players_arg} added to team {team.name}.")
        )

    @ringers.command()
    async def add(self, ctx, player_arg: str, team_name: str):
        """`{prefix}ringers add <unique_id or alias> <team_name>`

        **Examples**: `{prefix}ringers add maku team_a`"""
        if not await check_perm_captain(ctx, global_check=True):
            return
        team = aliases.get_team(team_name)
        player = SteamPlayer.convert(player_arg)
        team.ringer_add(player)
        await ctx.send(
            embed=discord.Embed(description=f"Ringer {player.name} added to team {team.name}.")
        )

    @ringers.command()
    async def reset(self, ctx, team_name: str):
        """`{prefix}ringers reset <team_name>`

        **Examples**: `{prefix}ringers reset team_a`"""
        if not await check_perm_captain(ctx, global_check=True):
            return
        team = aliases.get_team(team_name)
        team.ringers_reset()
        await ctx.send(embed=discord.Embed(description=f"Ringers for team {team.name} reset."))

    @ringers.command(aliases=["remove"])
    async def delete(self, ctx, player_arg: str, team_name: str):
        """`{prefix}ringers delete <unique_id or alias> <team_name>`

        **Examples**: `{prefix}ringers delete maku team_a`"""
        if not await check_perm_captain(ctx, global_check=True):
            return
        team = aliases.get_team(team_name)
        player = SteamPlayer.convert(player_arg)
        team.ringer_delete(player)
        await ctx.send(
            embed=discord.Embed(description=f"Ringer {player.name} removed from team {team.name}.")
        )

    @commands.command()
    async def teams(self, ctx, team_name: str = None):
        """`{prefix}teams [team_name]`

        team_name is optional. Without it will list all possible teams."""
        if not team_name:
            teams = aliases.get_teams_list()
            embed = discord.Embed(title="Teams")
            desc = ""
            for team in teams:
                desc += f"- {team.name}\n"
            embed.description = desc
            embed.set_footer(
                text=f"Use {config.prefix}teams [team_name] for more infos about a team."
            )
        else:
            team = aliases.get_team(team_name)
            embed = discord.Embed(title=team.name, description=team.member_repr())
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Teams(bot))
