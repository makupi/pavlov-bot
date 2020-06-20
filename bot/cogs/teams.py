import logging

import discord
from discord.ext import commands

from bot.utils import aliases
from bot.utils.steamplayer import SteamPlayer


class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.group(invoke_without_command=True, pass_context=True, aliases=["ringer"])
    async def ringers(self, ctx):
        pass

    @ringers.command()
    async def add(self, ctx, player_arg: str, team_name: str):
        """`{prefix}ringers add <unique_id or alias> <team_name>`

        **Examples**: `{prefix}ringers add maku team_a`"""
        team = aliases.get_team(team_name)
        player = SteamPlayer.convert(player_arg)
        team.ringer_add(player)
        await ctx.send(
            embed=discord.Embed(
                description=f"Ringer {player.name} added to team {team.name}."
            )
        )

    @ringers.command()
    async def reset(self, ctx, team_name: str):
        """`{prefix}ringers reset <team_name>`

        **Examples**: `{prefix}ringers reset team_a`"""
        team = aliases.get_team(team_name)
        team.ringers_reset()
        await ctx.send(
            embed=discord.Embed(description=f"Ringers for team {team.name} reset.")
        )

    @commands.command()
    async def teaminfo(self, ctx, team_name: str):
        """`{prefix}teaminfo <team_name>`"""
        team = aliases.get_team(team_name)
        embed = discord.Embed(title=team.name, description=team.member_repr())
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Teams(bot))
