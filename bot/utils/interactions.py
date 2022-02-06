import asyncio
from enum import Enum

import discord
import discord_components
from discord.ext import commands
from discord_components import Select, SelectOption

from bot.utils import aliases, lists, servers, user_action_log
from bot.utils.pavlov import exec_server_command


class SpawnExceptionListTooLong(Exception):
    def __init__(self, list_name: str):
        self.list = list_name


class SpawnListTypes(Enum):
    SPAWN_ITEM_SELECT = "item"
    SPAWN_SKIN_SELECT = "skin"
    SPAWN_VEHICLE_SELECT = "vehicle"
    SPAWN_MAP_SELECT = "map"


async def spawn_list_select(
    ctx: commands.Context, interaction: discord_components.Interaction, list_type: SpawnListTypes
):
    options = list()
    _lists = lists.get_by_type(list_type.value)
    for name, _ in _lists.items():
        options.append(SelectOption(label=str(name), value=str(name)))
    if len(options) > 25:
        raise SpawnExceptionListTooLong(list_type.value)
    component = Select(placeholder=f"{list_type.value.capitalize()} Lists", options=options)
    await interaction.send(
        f"Select a {list_type.value} list below:",
        components=[component],
    )
    selected_list = await ctx.bot.components_manager.wait_for("select_option", component=component)
    items = lists.get(selected_list.values[0]).get("list")
    options = list()
    for item in items:
        options.append(SelectOption(label=str(items.get(item)), value=str(items.get(item))))
    options.append(SelectOption(label="all", value="all"))
    if len(options) > 25:
        raise SpawnExceptionListTooLong(list_type.value)
    component = Select(placeholder="Items", options=options)
    await selected_list.send(
        f"Select a {list_type.value} below:",
        components=[component],
    )
    selected_item = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN {list_type.value.upper()} SELECTION - {selected_item.values[0]}")
    if selected_item.values[0] == "all":
        return items, selected_item, selected_list.values[0]
    return selected_item.values[0], selected_item, selected_list.values[0]


async def spawn_player_select(
    ctx: commands.Context,
    server: str,
    interaction: discord_components.Interaction,
    enable_extra_options: bool = True,
):
    options = list()
    data, _ = await exec_server_command(ctx, server, "RefreshList")
    player_list = data.get("PlayerList")
    extras = {
        "all": "all",
        "teamblue/team0": "teamblue",
        "teamred/team1": "teamred",
    }
    if len(player_list) == 0:
        return "NoPlayers", interaction
    else:
        for player in player_list:
            if player.get("UniqueId") == "" or player.get("Username") == "":
                continue
            else:
                options.append(
                    SelectOption(
                        label=str(player.get("Username")), value=str(player.get("UniqueId"))
                    )
                )
        if enable_extra_options:
            for k, v in extras.items():
                options.append(SelectOption(label=k, value=v))
        component = Select(placeholder="Players", options=options)
        await interaction.send("Select a player below:", components=[component])
        selected = await ctx.bot.components_manager.wait_for("select_option", component=component)
        user_action_log(ctx, f"SPAWN PLAYER SELECTION - {selected.values[0]}")
        return selected.values[0], selected


async def spawn_team_select(
    ctx: commands.Context, interaction: discord_components.Interaction, team_index: int
):
    team_options = []
    teams = aliases.get_teams_list()
    for team in teams:
        team_options.append(SelectOption(label=str(team.name), value=str(team.name)))
    if len(team_options) == 0:
        return "empty", interaction

    component = Select(placeholder="Teams", options=team_options)
    await interaction.send(
        f"Select Team {team_index} below:",
        components=[component],
    )
    selected_team = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN TEAM SELECTION - {selected_team.values[0]}")
    return selected_team.values[0], selected_team


async def spawn_server_select(ctx: commands.Context, description: str = ""):
    user_action_log(ctx, f"SPAWN SERVER SELECTION")
    options = list()
    for server in servers.get_names():
        ctx.batch_exec = True
        try:
            data, _ = await exec_server_command(ctx, server, "RefreshList")
            players = data.get("PlayerList")
            options.append(SelectOption(label=f"{server} ({len(players)})", value=str(server)))

        except (ConnectionRefusedError, asyncio.TimeoutError):
            options.append(SelectOption(label=f"{server} (OFFLINE)", value=f"{server} OFFLINE"))
    embed = discord.Embed(title=f"**({description}) Select a server below:**")
    embed.set_author(name=ctx.author.display_name, url="", icon_url=ctx.author.avatar_url)
    print(", ".join([f"{o.label}: {o.value}" for o in options]))
    return options, embed


async def spawn_gamemode_select(ctx: commands.Context, interaction: discord_components.Interaction):
    component = Select(
        placeholder="Gamemodes",
        options=[
            SelectOption(label="SND", value="SND"),
            SelectOption(label="DeathMatch", value="DM"),
            SelectOption(label="King of the Hill", value="KOTH"),
            SelectOption(label="GunGame", value="GUN"),
            SelectOption(label="One in the chamber", value="OITC"),
            SelectOption(label="PUSH", value="PUSH"),
            SelectOption(label="TANK Team Deathmatch", value="TANKTDM"),
            SelectOption(label="Team Deathmatch", value="TDM"),
            SelectOption(label="TTT", value="TTT"),
            SelectOption(label="WW2 Gun Game", value="WW2GUN"),
            SelectOption(label="Zombies", value="ZWV"),
            SelectOption(label="Hide", value="HIDE"),
            SelectOption(label="Prophunt", value="PH"),
        ],
    )

    interaction = await interaction.send(
        "Select a gamemode below:",
        components=[component],
    )
    selected = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN GAME MODE SELECTION - {selected.values[0]}")
    return selected.values[0], selected
