import asyncio
import logging

import discord
import discord_components
from discord.ext import commands
from discord_components import Button, Select, ActionRow

from bot.utils import SteamPlayer, config
from bot.utils.interactions import (
    spawn_player_select,
    spawn_server_select,
    spawn_list_select,
    SpawnListTypes,
    SpawnExceptionListTooLong,
)
from bot.utils.pavlov import check_perm_admin, exec_server_command
from bot.utils.players import (
    exec_command_all_players,
    exec_command_all_players_on_team,
    parse_player_command_results,
)


class PavlovAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def menu(self, ctx):
        """`{prefix}menu`  - *Creates a button driven admin menu*
        **Description**: Creates a button driven admin menu.
        **Requires**: Admin permissions for the server
        """
        async def actions(interact):
            await message.edit(content="")
            server_name = interact.values[0]
            if "offline" in server_name.lower():
                embed = discord.Embed(title="Server is offline.")
                await interact.send(embed=embed)
                return
            data, _ = await exec_server_command(ctx, server_name, "ServerInfo")
            server_info = data.get("ServerInfo")

            if interact.author.id == ctx.author.id:
                embed = discord.Embed(title=f"**{server_name} Admin Menu**")
                ctx.interaction_exec = True
                ctx.batch_exec = False
                (
                    slap,
                    giveitem,
                    kill,
                    kick,
                    givevehicle,
                    players,
                    skinset,
                    flush,
                    ban,
                    inspectplayer,
                    switchmap,
                ) = [
                    self.bot.all_commands.get("slap"),
                    self.bot.all_commands.get("giveitem"),
                    self.bot.all_commands.get("kill"),
                    self.bot.all_commands.get("kick"),
                    self.bot.all_commands.get("givevehicle"),
                    self.bot.all_commands.get("players"),
                    self.bot.all_commands.get("setplayerskin"),
                    self.bot.all_commands.get("flush"),
                    self.bot.all_commands.get("ban"),
                    self.bot.all_commands.get("playerinfo"),
                    self.bot.all_commands.get("switchmap"),
                ]
                if server_info.get("GameMode").casefold() == "ttt":
                    flushkarma, endround, pausetimer = [
                        self.bot.all_commands.get("tttflushkarma"),
                        self.bot.all_commands.get("tttendround"),
                        self.bot.all_commands.get("tttpausetimer"),
                    ]
                components = [
                    ActionRow(
                        self.bot.components_manager.add_callback(
                            Button(label="Godmode"),
                            lambda interaction: slap(
                                ctx, "", "-99999999999999999", server_name, interaction
                            ),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Give Item"),
                            lambda interaction: giveitem(ctx, "", "", server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Kill"),
                            lambda interaction: kill(ctx, "", server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Kick"),
                            lambda interaction: kick(ctx, "", server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Give Vehicle"),
                            lambda interaction: givevehicle(ctx, "", "", server_name, interaction),
                        ),
                    ),
                    ActionRow(
                        self.bot.components_manager.add_callback(
                            Button(label="Players"),
                            lambda interaction: players(ctx, server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Set Player Skin"),
                            lambda interaction: skinset(ctx, "", "", server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Flush"),
                            lambda interaction: flush(ctx, server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Ban"),
                            lambda interaction: ban(ctx, "", server_name, interaction),
                        ),
                        self.bot.components_manager.add_callback(
                            Button(label="Inspect Player"),
                            lambda interaction: inspectplayer(ctx, "", server_name, interaction),
                        ),
                    ),
                    ActionRow(
                        self.bot.components_manager.add_callback(
                            Button(label="Switch Map"),
                            lambda interaction: switchmap(ctx, "", "", server_name, interaction),
                        ),
                    ),
                ]
                await interact.send(
                    embed=embed,
                    components=components,
                )
            else:
                return

        options, menu_embed = await spawn_server_select(ctx, "Admin Menu")
        message = await ctx.send(
            embed=menu_embed,
            components=[
                self.bot.components_manager.add_callback(
                    Select(placeholder="Server", options=options), actions
                )
            ],
        )

    @commands.command()
    async def giveitem(
        self,
        ctx,
        player_arg: str,
        item_id: str,
        server_name: str = config.default_server,
        __interaction: discord_components = None,
    ):
        """`{prefix}giveitem <player_id/all/team> <item_id> <server_name>`
        **Description**: Spawns a item for a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveitem 89374583439127 tazer servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
            try:
                item_id, __interaction, iteml = await spawn_list_select(
                    ctx, __interaction, SpawnListTypes.SPAWN_ITEM_SELECT
                )
            except SpawnExceptionListTooLong:
                embed = discord.Embed(
                    title=f"**Your item list `{iteml}` contains more than 25 items!**",
                    description="**Keep your item list to 25 items or lower.**",
                )
                await __interaction.send(embed=embed)
                return

        if player_arg.casefold() == "all" or player_arg.startswith("team"):
            if player_arg.casefold() == "all":
                if type(item_id) == dict:
                    for i in item_id:
                        await asyncio.sleep(0.1)
                        data = await exec_command_all_players(
                            ctx, server_name, f"GiveItem all {item_id.get(i)}"
                        )
                else:
                    data = await exec_command_all_players(
                        ctx, server_name, f"GiveItem all {item_id}"
                    )
            elif player_arg.startswith("team"):
                if type(item_id) == dict:
                    for i in item_id:
                        await asyncio.sleep(0.1)
                        data = await exec_command_all_players_on_team(
                            ctx, server_name, player_arg, f"GiveItem team {item_id.get(i)}"
                        )
                else:
                    data = await exec_command_all_players_on_team(
                        ctx, server_name, player_arg, f"GiveItem team {item_id}"
                    )
        else:
            if ctx.interaction_exec:
                if type(item_id) == dict:
                    for i in item_id:
                        await asyncio.sleep(0.1)
                        data, _ = await exec_server_command(
                            ctx, server_name, f"GiveItem {player_arg} {item_id.get(i)}"
                        )
                else:
                    data, _ = await exec_server_command(
                        ctx, server_name, f"GiveItem {player_arg} {item_id}"
                    )
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(
                    ctx, server_name, f"GiveItem {player.unique_id} {item_id}"
                )
        if type(item_id) == dict:
            item_id = " ".join(item_id.values())
        embed = discord.Embed(title=f"**GiveItem {player_arg} {item_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def givevehicle(
        self,
        ctx,
        player_arg: str,
        vehicle_id: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}givevehicle <player_id> <vehicle_id> <server_name>`
        **Description**: Spawns a vehicle near a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givevehicle 89374583439127 atv servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
            try:
                vehicle_id, __interaction, iteml = await spawn_list_select(
                    ctx, __interaction, SpawnListTypes.SPAWN_VEHICLE_SELECT
                )
            except SpawnExceptionListTooLong:
                embed = discord.Embed(
                    title=f"**Your item list `{iteml}` contains more than 25 items!**",
                    description="**Keep your item list to 25 items or lower.**",
                )
                await __interaction.send(embed=embed)
                return
        if player_arg.casefold() == "all" or player_arg.startswith("team"):
            if player_arg.casefold() == "all":
                if type(vehicle_id) == dict:
                    for i in vehicle_id:
                        await asyncio.sleep(0.1)
                        data = await exec_command_all_players(
                            ctx, server_name, f"GiveVehicle all {vehicle_id.get(i)}"
                        )
                else:
                    data = await exec_command_all_players(
                        ctx, server_name, f"GiveVehicle all {vehicle_id}"
                    )
            elif player_arg.startswith("team"):
                if type(vehicle_id) == dict:
                    for i in vehicle_id:
                        await asyncio.sleep(0.1)
                        data = await exec_command_all_players_on_team(
                            ctx, server_name, player_arg, f"GiveVehicle team {vehicle_id.get(i)}"
                        )
                else:
                    data = await exec_command_all_players_on_team(
                        ctx, server_name, player_arg, f"GiveVehicle team {vehicle_id}"
                    )
        else:
            if ctx.interaction_exec:
                if type(vehicle_id) == dict:
                    for i in vehicle_id:
                        await asyncio.sleep(0.1)
                        data, _ = await exec_server_command(
                            ctx, server_name, f"GiveVehicle {player_arg} {vehicle_id.get(i)}"
                        )
                else:
                    data, _ = await exec_server_command(
                        ctx, server_name, f"GiveVehicle {player_arg} {vehicle_id}"
                    )
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(
                    ctx, server_name, f"GiveVehicle {player.unique_id} {vehicle_id}"
                )
        embed = discord.Embed(title=f"**GiveVehicle {player_arg} {vehicle_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def givecash(
        self,
        ctx,
        player_arg: str,
        cash_amount: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}givecash <player_id/all> <cash_amount> <server_name>`
        **Description**: Gives a specified cash amount to a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givecash 89374583439127 5000 servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(ctx, server_name, f"GiveCash all {cash_amount}")
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                ctx, server_name, f"GiveCash {player.unique_id} {cash_amount}"
            )
        embed = discord.Embed(title=f"**GiveCash {player_arg} {cash_amount}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def giveteamcash(
        self,
        ctx,
        team_id: str,
        cash_amount: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}giveteamcash <team_id> <cash_amount> <server_name>`
        **Description**: Gives a specified amount cash to a specified team.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveteamcash 0 5000 servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        team_id = team_id.replace("team", "")
        if team_id.casefold() == "blue":
            team_id = "0"
        elif team_id.casefold() == "red":
            team_id = "1"
        data, _ = await exec_server_command(
            ctx, server_name, f"GiveTeamCash {team_id} {cash_amount}"
        )
        embed = discord.Embed(title=f"**GiveTeamCash {team_id} {cash_amount}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def setplayerskin(
        self,
        ctx,
        player_arg: str,
        skin_id: str,
        server_name: str = config.default_server,
        __interaction: discord_components.Interaction = None,
    ):
        """`{prefix}setplayerskin <player_id/all/team> <skin_id> <server_name>`
        **Description**: Sets a player's skin to a specified skin.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}setplayerskin 89374583439127 clown servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, __interaction = await spawn_player_select(ctx, server_name, __interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await __interaction.send(embed=embed)
                return
            try:
                skin_id, __interaction, skinl = await spawn_list_select(
                    ctx, __interaction, SpawnListTypes.SPAWN_SKIN_SELECT
                )
            except SpawnExceptionListTooLong:
                embed = discord.Embed(
                    title=f"**Your skin list `{skinl}` contains more than 25 items!**",
                    description="**Keep your item list to 25 items or lower.**",
                )
                await __interaction.send(embed=embed)
                return
        if player_arg.casefold() == "all" or player_arg.startswith("team"):
            if player_arg.casefold() == "all":
                data = await exec_command_all_players(
                    ctx, server_name, f"SetPlayerSkin all {skin_id}"
                )
            elif player_arg.startswith("team"):
                data = await exec_command_all_players_on_team(
                    ctx, server_name, player_arg, f"SetPlayerSkin team {skin_id}"
                )
        else:
            if ctx.interaction_exec:
                data, _ = await exec_server_command(
                    ctx, server_name, f"SetPlayerSkin {player_arg} {skin_id}"
                )
            else:
                player = SteamPlayer.convert(player_arg)
                data, _ = await exec_server_command(
                    ctx, server_name, f"SetPlayerSkin {player.unique_id} {skin_id}"
                )
        embed = discord.Embed(title=f"**SetPlayerSkin {player_arg} {skin_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await __interaction.send(embed=embed)
            return
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def custom(self, ctx, rcon_command: str, server_name: str = config.default_server):
        """`{prefix}custom "<rcon_command with args>" server_name` - *Telnet-like direct entry to RCON*
        **Description**: Runs a custom RCON command.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}custom ServerInfo servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        data, _ = await exec_server_command(ctx, server_name, rcon_command)
        if not data:
            data = "No response"
        if ctx.batch_exec:
            return data
        embed = discord.Embed()
        embed.add_field(name=rcon_command, value=str(data))
        await ctx.send(embed=embed)

    @commands.command()
    async def nametags(self, ctx, boolean, server_name: str = config.default_server):
        """`{prefix}nametags enable/disable/true/false server_name`
        **Description**: Enables/disables nametags.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}nametags enable servername`
        """
        if boolean.casefold() == "enable":
            boolean = "true"
        elif boolean.casefold() == "disable":
            boolean = "false"
        if not await check_perm_admin(ctx, server_name):
            return
        data, _ = await exec_server_command(ctx, server_name, f"ShowNameTags {boolean}")
        if not data:
            data = "No response"
        if ctx.batch_exec:
            return data
        if data.get("NametagsEnabled"):
            embed = discord.Embed(title=f"**Nametags enabled!** \n")
        else:
            embed = discord.Embed(title=f"**Nametags disabled!** \n")
        await ctx.send(embed=embed)

    @commands.command()
    async def repeat(self, ctx, cmdr: str, aot: str):
        """`{prefix}repeat "<command with args>" amount_of_times server_name`
        **Description**: Repeats a complete pavlov-bot command multiple times.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}repeat "GiveItem 89374583439127 rl_rpg servername" 10`
        """
        _args = cmdr.split(" ")
        cmd = _args[0]
        server_name = _args[-1]
        if not await check_perm_admin(ctx, server_name):
            return
        for i in range(int(aot)):
            command = self.bot.all_commands.get(cmd.lower())
            ctx.batch_exec = True
            await asyncio.sleep(0.2)
            if cmd.lower() == "repeat":
                return
            elif int(aot) > 100:
                return
            else:
                data = await command(ctx, *_args[1:])
            if data is None:
                data = "No response"
        embed = discord.Embed(title=f"Executed '{cmdr}' {aot} times")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PavlovAdmin(bot))
