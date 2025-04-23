import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils import SteamPlayer, aliases, config, servers
from bot.utils.pavlov import check_perm_captain, exec_server_command


class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @app_commands.command()
    @app_commands.describe(players_arg="List of comma separated player ids",
                           team_name="The team you want to add the player to")
    @app_commands.rename(players_arg="players", team_name="team")
    @app_commands.autocomplete(team_name=aliases.teams_autocomplete)
    async def teamsetup(self, interaction: discord.Interaction, players_arg: str, team_name: str):
        """`{prefix}teamsetup <comma seperated list of unique_id or alias> <team_name>`
        **Description**: Takes a list of aliases or IDs and puts them on a team after wiping player list
        **Requires**: Captain permissions or higher for the server
        **Examples**: `{prefix}teamsetup maku,invicta team_a`"""
        if not await check_perm_captain(interaction, global_check=True):
            return
        team = aliases.get_team(team_name)
        team.ringers_reset()
        players = players_arg.split(",")
        for player in players:
            player = SteamPlayer.convert(player)
            team.ringer_add(player)
        embed = discord.Embed(description=f"Player list {players_arg} added to team {team.name}.")
        await interaction.response.send_message(embed=embed)

    ringers = app_commands.Group(name="ringers", description="Ringers Commands")

    @ringers.command()
    @app_commands.describe(player_arg="The player id you want to add", team_name="The team you want to add the player to")
    @app_commands.rename(player_arg="player", team_name="team")
    @app_commands.autocomplete(player_arg=aliases.players_autocomplete, team_name=aliases.teams_autocomplete)
    async def add(self, interaction: discord.Interaction, player_arg: str, team_name: str):
        """`{prefix}ringers add <unique_id or alias> <team_name>`
        **Description**: Adds a single player to a team. Can be called by ID or alias
        **Requires**: Captain permissions or higher for the server
        **Examples**: `{prefix}ringers add maku team_a`"""
        if not await check_perm_captain(interaction, global_check=True):
            return
        team = aliases.get_team(team_name)
        player = SteamPlayer.convert(player_arg)
        team.ringer_add(player)
        await interaction.response.send_message(
            embed=discord.Embed(description=f"Ringer {player.name} added to team {team.name}.")
        )

    @ringers.command()
    @app_commands.describe(team_name="The team you want to populate", server_name="The name of the server")
    @app_commands.rename(team_name="team", server_name="server")
    @app_commands.autocomplete(team_name=aliases.teams_autocomplete, server_name=servers.autocomplete)
    async def populate(self, interaction: discord.Interaction, team_name: str, server_name: str = config.default_server):
        """`{prefix}ringers populate <team_name> <server_name>`
        **Description**: Takes all players on a server not in aliases and puts them on a team.
        **Requires**: Captain permissions or higher for the server
        **Examples**: `{prefix}ringers populate random_team tdm_server`"""
        if not await check_perm_captain(interaction, global_check=True):
            return
        data = await exec_server_command(interaction, server_name, "RefreshList")
        player_list = data.get("PlayerList")
        team = aliases.get_team(team_name)
        players_added = []
        for player in player_list:
            check = aliases.find_player_alias(player.get("UniqueId"))
            if check is None:
                if player.get("Username") == player.get("UniqueId"):
                    playerm = SteamPlayer.convert("q-" + player.get("UniqueId"))
                else:
                    playerm = SteamPlayer.convert(player.get("UniqueId"))
                team.ringer_add(playerm)
                players_added.append(player.get("Username"))
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Ringer {' '.join(players_added)} added to team {team.name}."
            )
        )

    @ringers.command()
    @app_commands.describe(team_name="The team you want to reset")
    @app_commands.rename(team_name="team")
    @app_commands.autocomplete(team_name=aliases.teams_autocomplete)
    async def reset(self, interaction: discord.Interaction, team_name: str):
        """`{prefix}ringers reset <team_name>`
        **Description**: Removes all ringers on a team.
        **Requires**: Captain permissions or higher for the server
        **Examples**: `{prefix}ringers reset team_a`"""
        if not await check_perm_captain(interaction, global_check=True):
            return
        team = aliases.get_team(team_name)
        team.ringers_reset()
        await interaction.response.send_message(embed=discord.Embed(description=f"Ringers for team {team.name} reset."))

    @ringers.command()
    @app_commands.describe(player_arg="The player id you want to remove",
                           team_name="The team you want to remove the player from")
    @app_commands.rename(player_arg="player", team_name="team")
    @app_commands.autocomplete(player_arg=aliases.players_autocomplete, team_name=aliases.teams_autocomplete)
    async def delete(self, interaction: discord.Interaction, player_arg: str, team_name: str):
        """`{prefix}ringers delete <unique_id or alias> <team_name>`
        **Description**: Removes a specific ringer from a team.
        **Requires**: Captain permissions or higher for the server
        **Examples**: `{prefix}ringers delete maku team_a`"""
        if not await check_perm_captain(interaction, global_check=True):
            return
        team = aliases.get_team(team_name)
        player = SteamPlayer.convert(player_arg)
        team.ringer_delete(player)
        await interaction.response.send_message(
            embed=discord.Embed(description=f"Ringer {player.name} removed from team {team.name}.")
        )

    @app_commands.command()
    @app_commands.describe(team_name="The team you want to remove the player from")
    @app_commands.rename(team_name="team")
    @app_commands.autocomplete(team_name=aliases.teams_autocomplete)
    async def teams(self, interaction: discord.Interaction, team_name: str = None):
        """`{prefix}teams [team_name]`
        **Description**: Lists players assigned to teams
        **Requires**: Captain permissions or higher for the server
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
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Teams(bot))
