import asyncio

import discord
import discord_components
from discord.ext import commands
from discord_components import Select, SelectOption

from bot.utils import aliases, lists, servers, user_action_log
from bot.utils.pavlov import exec_server_command


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


async def spawn_item_select(ctx: commands.Context, interaction: discord_components.Interaction):
    options = list()
    itemlists = lists.get_names()
    for item in itemlists:
        alist = lists.get(item)
        if alist.get("type") == "item":
            options.append(SelectOption(label=str(item), value=str(item)))
    component = Select(placeholder="Item Lists", options=options)
    await interaction.send(
        "Select a item list below:",
        components=[component],
    )
    selected_list = await ctx.bot.components_manager.wait_for("select_option", component=component)
    slist = lists.get(selected_list.values[0])
    items = slist.get("list")
    itemsilist = []
    for i in items:
        itemsilist.append(SelectOption(label=str(items.get(i)), value=str(items.get(i))))
    itemsilist.append(SelectOption(label="all", value="all"))
    if len(itemsilist) > 25:
        return "ListTooLong", selected_list, selected_list.values[0]
    component = Select(placeholder="Items", options=itemsilist)
    await interaction.send(
        "Select a item below:",
        components=[component],
    )
    selected_item = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN ITEM SELECTION - {selected_item.values[0]}")
    if selected_item.values[0] == "all":
        return items, selected_item, selected_list.values[0]
    return selected_item.values[0], selected_item, selected_list.values[0]


async def spawn_skin_select(ctx: commands.Context, interaction: discord_components.Interaction):
    options = list()
    itemlists = lists.get_names()
    for item in itemlists:
        alist = lists.get(item)
        if alist.get("type") == "skin":
            options.append(SelectOption(label=str(item), value=str(item)))
    component = Select(placeholder="Skin Lists", options=options)
    await interaction.send(
        "Select a skin list below:",
        components=[component],
    )
    selected_list = await ctx.bot.components_manager.wait_for("select_option", component=component)
    slist = lists.get(selected_list.values[0])
    items = slist.get("list")
    itemsilist = []
    for i in items:
        itemsilist.append(SelectOption(label=str(items.get(i)), value=str(items.get(i))))
    itemsilist.append(SelectOption(label="all", value="all"))
    if len(itemsilist) > 25:
        return "ListTooLong", selected_list, selected_list.values[0]
    component = Select(placeholder="Skins", options=itemsilist)
    await interaction.send(
        "Select a skin below:",
        components=[component],
    )
    selected_skin = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN SKIN SELECTION - {selected_skin.values[0]}")
    if selected_skin.values[0] == "all":
        return items, selected_skin, selected_skin.values[0]
    return selected_skin.values[0], selected_skin, selected_list.values[0]


async def spawn_vehicle_select(ctx: commands.Context, interaction: discord_components.Interaction):
    options = list()
    itemlists = lists.get_names()
    for item in itemlists:
        alist = lists.get(item)
        if alist.get("type") == "vehicle":
            options.append(SelectOption(label=str(item), value=str(item)))

    component = Select(placeholder="Vehicle Lists", options=options)
    await interaction.send(
        "Select a vehicle list below:",
        components=[component],
    )
    selected_list = await ctx.bot.components_manager.wait_for("select_option", component=component)
    slist = lists.get(selected_list.values[0])
    items = slist.get("list")
    itemsilist = []
    for i in items:
        itemsilist.append(SelectOption(label=str(items.get(i)), value=str(items.get(i))))
    itemsilist.append(SelectOption(label="all", value="all"))
    if len(itemsilist) > 25:
        return "ListTooLong", selected_list, selected_list.values[0]
    component = Select(placeholder="Vehicles", options=itemsilist)
    await interaction.send(
        "Select a vehicle below:",
        components=[component],
    )
    selected_vehicle = await ctx.bot.components_manager.wait_for(
        "select_option", component=component
    )
    user_action_log(ctx, f"SPAWN VEHICLE SELECTION - {selected_vehicle.values[0]}")
    if selected_vehicle.values[0] == "all":
        return items, selected_vehicle, selected_list.values[0]
    return selected_vehicle.values[0], selected_vehicle, selected_list.values[0]


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


async def spawn_map_select(ctx: commands.Context, interaction: discord_components.Interaction):
    options = list()
    map_lists = lists.get_by_type("map")
    for list_name, _ in map_lists.items():
        options.append(SelectOption(label=str(list_name), value=str(list_name)))
    component = Select(placeholder="Map Lists", options=options)
    await interaction.send(
        "Select a map list below:",
        components=[component],
    )
    selected_list = await ctx.bot.components_manager.wait_for("select_option", component=component)
    map_list = map_lists.get(selected_list.values[0])
    items = map_list.get("list")
    options = list()
    for item in items:
        options.append(SelectOption(label=str(items.get(item)), value=str(items.get(item))))
    if len(options) > 25:
        return "ListTooLong", selected_list, selected_list.values[0]
    component = Select(placeholder="Map", options=options)
    await interaction.send(
        "Select map below:",
        components=[component],
    )
    selected_map = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN MAP SELECTION - {selected_map.values[0]}")
    return selected_map.values[0], selected_map


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
            SelectOption(label="DM", value="DM"),
            SelectOption(label="KOTH", value="KOTH"),
            SelectOption(label="GUN", value="GUN"),
            SelectOption(label="OITC", value="OITC"),
            SelectOption(label="SND", value="SND"),
            SelectOption(label="TANKTDM", value="TANKTDM"),
            SelectOption(label="TDM", value="TDM"),
            SelectOption(label="TTT", value="TTT"),
            SelectOption(label="WW2GUN", value="WW2GUN"),
            SelectOption(label="ZWV", value="ZWV"),
            SelectOption(label="CUSTOM", value="CUSTOM"),
        ],
    )

    interaction = await interaction.send(
        "Select a gamemode below:",
        components=[component],
    )
    selected = await ctx.bot.components_manager.wait_for("select_option", component=component)
    user_action_log(ctx, f"SPAWN GAME MODE SELECTION - {selected.values[0]}")
    return selected.values[0], selected
