from bot.utils.pavlov import exec_server_command, check_perm_admin
import asyncio
import logging
import discord
from bot.utils import lists, aliases, servers
from discord_components import Button, Select, SelectOption


async def spawn_pselect(self, ctx: str, server: str, interaction):
    logging.info(
        f"Spawning player selection menu for {interaction.author.name}#{interaction.author.discriminator}!"
    )
    plist = []
    data = await exec_server_command(ctx, server, "RefreshList")
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
            plist.append(
                SelectOption(label=str(player.get("Username")), value=str(player.get("UniqueId")))
            )
        for k, v in extras.items():
            plist.append(SelectOption(label=k, value=v))
        await interaction.send(
            "Select a player below:", components=[Select(placeholder="Players", options=plist)]
        )
        interaction = await self.bot.wait_for("select_option")
        return interaction.values[0], interaction


async def spawn_iselect(self, ctx: str, server: str, interaction):
    logging.info(
        f"Spawning item selection menu for {interaction.author.name}#{interaction.author.discriminator}!"
    )
    i_list = []
    itemlists = lists.get_names()
    for item in itemlists:
        alist = lists.get(item)
        if alist.get("type") == "item":
            i_list.append(SelectOption(label=str(item), value=str(item)))
    await interaction.send(
        "Select a item list below:",
        components=[Select(placeholder="Item Lists", options=i_list)],
    )
    interaction1 = await self.bot.wait_for("select_option")
    slist = lists.get(interaction1.values[0])
    items = slist.get("list")
    itemsilist = []
    for i in items:
        itemsilist.append(SelectOption(label=str(items.get(i)), value=str(items.get(i))))
    itemsilist.append(SelectOption(label="all", value="all"))
    if len(itemsilist) > 25:
        return "ListTooLong", interaction1, interaction1.values[0]
    await interaction1.send(
        "Select a item below:",
        components=[Select(placeholder="Items", options=itemsilist)],
    )
    interaction2 = await self.bot.wait_for("select_option")
    if interaction2.values[0] == "all":
        return items, interaction2, interaction1.values[0]
    return interaction2.values[0], interaction2, interaction1.values[0]


async def spawn_vselect(self, ctx: str, server: str, interaction):
    logging.info(
        f"Spawning vehicle selection menu for {interaction.author.name}#{interaction.author.discriminator}!"
    )
    i_list = []
    itemlists = lists.get_names()
    for item in itemlists:
        alist = lists.get(item)
        if alist.get("type") == "vehicle":
            i_list.append(SelectOption(label=str(item), value=str(item)))
    await interaction.send(
        "Select a vehicle list below:",
        components=[Select(placeholder="Vehicle Lists", options=i_list)],
    )
    interaction1 = await self.bot.wait_for("select_option")
    slist = lists.get(interaction1.values[0])
    items = slist.get("list")
    itemsilist = []
    for i in items:
        itemsilist.append(SelectOption(label=str(items.get(i)), value=str(items.get(i))))
    itemsilist.append(SelectOption(label="all", value="all"))
    if len(itemsilist) > 25:
        return "ListTooLong", interaction1, interaction1.values[0]
    await interaction1.send(
        "Select a vehicle below:",
        components=[Select(placeholder="Vehicles", options=itemsilist)],
    )
    interaction2 = await self.bot.wait_for("select_option")
    if interaction2.values[0] == "all":
        return items, interaction2, interaction1.values[0]
    return interaction2.values[0], interaction2, interaction1.values[0]


async def spawn_tselect(self, ctx: str, server: str, interaction, team_num):
    logging.info(
        f"Spawning team selection menu for {interaction.author.name}#{interaction.author.discriminator}!"
    )
    team_options = []
    teams = aliases.get_teams_list()
    for team in teams:
        team_options.append(SelectOption(label=str(team.name), value=str(team.name)))
    if len(team_options) == 0:
        return "empty", interaction
    else:
        await interaction.send(
            f"Select Team {team_num} below:",
            components=[
                Select(placeholder="Teams", options=team_options)
                # self.bot.components_manager.add_callback(
                #    Button(label="Next", custom_id="next"), switchlist
                # ),
            ],
        )
        interaction1 = await self.bot.wait_for("select_option")
        return interaction1.values[0], interaction1


async def spawn_mselect(self, ctx: str, server: str, interaction):
    logging.info(
        f"Spawning map selection menu for {interaction.author.name}#{interaction.author.discriminator}!"
    )
    i_list = []
    itemlists = lists.get_names()
    for item in itemlists:
        alist = lists.get(item)
        if alist.get("type") == "map":
            i_list.append(SelectOption(label=str(item), value=str(item)))
    await interaction.send(
        "Select a map list below:",
        components=[Select(placeholder="Map Lists", options=i_list)],
    )
    interaction1 = await self.bot.wait_for("select_option")
    slist = lists.get(interaction1.values[0])
    items = slist.get("list")
    itemsilist = []
    for i in items:
        itemsilist.append(SelectOption(label=str(items.get(i)), value=str(items.get(i))))
    if len(itemsilist) > 25:
        return "ListTooLong", interaction1, interaction1.values[0]
    await interaction1.send(
        "Select map below:",
        components=[Select(placeholder="Map", options=itemsilist)],
    )
    interaction1 = await self.bot.wait_for("select_option")
    return interaction1.values[0], interaction1


async def spawn_serselect(self, ctx: str):
    options = []
    for i in servers.get_names():
        ctx.batch_exec = True
        try:
            data = await exec_server_command(ctx, i, "RefreshList")
            plist = data.get("PlayerList")
            options.append(SelectOption(label=f"{i} ({len(plist)})", value=str(i)))
        except:
            options.append(SelectOption(label=f"{i} (OFFLINE)", value="OFFLINE"))
    embed = discord.Embed(title="**Select a server below:**")
    embed.set_author(name=ctx.author.display_name, url="", icon_url=ctx.author.avatar_url)
    return options, embed
