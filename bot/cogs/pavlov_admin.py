import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils import SteamPlayer, config
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

    # @commands.command()
    # async def menu(self, ctx):
    #     """`{prefix}menu`  - *Creates a button driven admin menu*
    #     **Description**: Creates a button driven admin menu.
    #     **Requires**: Admin permissions for the server
    #     """
    #     async def actions(interact):
    #         await message.edit(content="")
    #         server_name = interact.values[0]
    #         if "offline" in server_name.lower():
    #             embed = discord.Embed(title="Server is offline.")
    #             await interact.send(embed=embed)
    #             return
    #         data, _ = await exec_server_command(ctx, server_name, "ServerInfo")
    #         server_info = data.get("ServerInfo")
    #
    #         if interact.author.id == ctx.author.id:
    #             embed = discord.Embed(title=f"**{server_name} Admin Menu**")
    #             ctx.interaction_exec = True
    #             ctx.batch_exec = False
    #             (
    #                 slap,
    #                 giveitem,
    #                 kill,
    #                 kick,
    #                 givevehicle,
    #                 players,
    #                 skinset,
    #                 flush,
    #                 ban,
    #                 inspectplayer,
    #                 switchmap,
    #             ) = [
    #                 self.bot.all_commands.get("slap"),
    #                 self.bot.all_commands.get("giveitem"),
    #                 self.bot.all_commands.get("kill"),
    #                 self.bot.all_commands.get("kick"),
    #                 self.bot.all_commands.get("givevehicle"),
    #                 self.bot.all_commands.get("players"),
    #                 self.bot.all_commands.get("setplayerskin"),
    #                 self.bot.all_commands.get("flush"),
    #                 self.bot.all_commands.get("ban"),
    #                 self.bot.all_commands.get("playerinfo"),
    #                 self.bot.all_commands.get("switchmap"),
    #             ]
    #             if server_info.get("GameMode").casefold() == "ttt":
    #                 flushkarma, endround, pausetimer = [
    #                     self.bot.all_commands.get("tttflushkarma"),
    #                     self.bot.all_commands.get("tttendround"),
    #                     self.bot.all_commands.get("tttpausetimer"),
    #                 ]
    #             components = [
    #                 ActionRow(
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Godmode"),
    #                         lambda interaction: slap(
    #                             ctx, "", "-99999999999999999", server_name, interaction
    #                         ),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Give Item"),
    #                         lambda interaction: giveitem(ctx, "", "", server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Kill"),
    #                         lambda interaction: kill(ctx, "", server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Kick"),
    #                         lambda interaction: kick(ctx, "", server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Give Vehicle"),
    #                         lambda interaction: givevehicle(ctx, "", "", server_name, interaction),
    #                     ),
    #                 ),
    #                 ActionRow(
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Players"),
    #                         lambda interaction: players(ctx, server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Set Player Skin"),
    #                         lambda interaction: skinset(ctx, "", "", server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Flush"),
    #                         lambda interaction: flush(ctx, server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Ban"),
    #                         lambda interaction: ban(ctx, "", server_name, interaction),
    #                     ),
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Inspect Player"),
    #                         lambda interaction: inspectplayer(ctx, "", server_name, interaction),
    #                     ),
    #                 ),
    #                 ActionRow(
    #                     self.bot.components_manager.add_callback(
    #                         Button(label="Switch Map"),
    #                         lambda interaction: switchmap(ctx, "", "", server_name, interaction),
    #                     ),
    #                 ),
    #             ]
    #             await interact.send(
    #                 embed=embed,
    #                 components=components,
    #             )
    #         else:
    #             return
    #
    #     options, menu_embed = await spawn_server_select(ctx, "Admin Menu")
    #     message = await interaction.response.send_message(
    #         embed=menu_embed,
    #         components=[
    #             self.bot.components_manager.add_callback(
    #                 Select(placeholder="Server", options=options), actions
    #             )
    #         ],
    #     )

    @app_commands.command()
    @app_commands.describe(item_id="ID of the item")
    @app_commands.rename(player_arg="player", item_id="item-id", server_name="server")
    async def giveitem(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        item_id: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}giveitem <player_id/all/team> <item_id> <server_name>`
        **Description**: Spawns a item for a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveitem 89374583439127 tazer servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(
                server_name, f"GiveItem all {item_id}"
            )
        elif player_arg.startswith("team"):
            data = await exec_command_all_players_on_team(
                server_name, player_arg, f"GiveItem team {item_id}"
            )
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"GiveItem {player.unique_id} {item_id}"
            )
        embed = discord.Embed(title=f"**GiveItem {player_arg} {item_id}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(vehicle_id="ID of the vehicle")
    @app_commands.rename(player_arg="player", vehicle_id="vehicle-id", server_name="server")
    async def givevehicle(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        vehicle_id: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}givevehicle <player_id> <vehicle_id> <server_name>`
        **Description**: Spawns a vehicle near a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givevehicle 89374583439127 atv servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        if player_arg.casefold() == "all":
           data = await exec_command_all_players(
                server_name, f"GiveVehicle all {vehicle_id}"
            )
        elif player_arg.startswith("team"):
            data = await exec_command_all_players_on_team(
                server_name, player_arg, f"GiveVehicle team {vehicle_id}"
            )
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"GiveVehicle {player.unique_id} {vehicle_id}"
            )
        embed = discord.Embed(title=f"**GiveVehicle {player_arg} {vehicle_id}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(cash_amount="Amount of cash")
    @app_commands.rename(player_arg="player", cash_amount="cash", server_name="server")
    async def givecash(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        cash_amount: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}givecash <player_id/all> <cash_amount> <server_name>`
        **Description**: Gives a specified cash amount to a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givecash 89374583439127 5000 servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(server_name, f"GiveCash all {cash_amount}")
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"GiveCash {player.unique_id} {cash_amount}"
            )
        embed = discord.Embed(title=f"**GiveCash {player_arg} {cash_amount}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(cash_amount="Amount of cash")
    @app_commands.rename(team_id="team", cash_amount="cash", server_name="server")
    @app_commands.choices(team_id=[app_commands.Choice(name="blue/0", value=0), app_commands.Choice(name="red/1", value=1)])
    async def giveteamcash(
        self,
        interaction: discord.Interaction,
        team_id: int,
        cash_amount: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}giveteamcash <team_id> <cash_amount> <server_name>`
        **Description**: Gives a specified amount cash to a specified team.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveteamcash 0 5000 servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        data, _ = await exec_server_command(
            server_name, f"GiveTeamCash {team_id} {cash_amount}"
        )
        embed = discord.Embed(title=f"**GiveTeamCash {team_id} {cash_amount}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(skin_id="ID of the skin")
    @app_commands.rename(player_arg="player", skin_id="skin-id", server_name="server")
    async def setplayerskin(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        skin_id: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}setplayerskin <player_id/all/team> <skin_id> <server_name>`
        **Description**: Sets a player's skin to a specified skin.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}setplayerskin 89374583439127 clown servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        if player_arg.casefold() == "all":
            data = await exec_command_all_players(
                server_name, f"SetPlayerSkin all {skin_id}"
            )
        elif player_arg.startswith("team"):
            data = await exec_command_all_players_on_team(
                server_name, player_arg, f"SetPlayerSkin team {skin_id}"
            )
        else:
            player = SteamPlayer.convert(player_arg)
            data, _ = await exec_server_command(
                server_name, f"SetPlayerSkin {player.unique_id} {skin_id}"
            )
        embed = discord.Embed(title=f"**SetPlayerSkin {player_arg} {skin_id}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(rcon_command="RCON command with arguments")
    @app_commands.rename(rcon_command="rcon", server_name="server")
    async def custom(self, interaction: discord.Interaction, rcon_command: str, server_name: str = config.default_server):
        """`{prefix}custom "<rcon_command with args>" server_name` - *Telnet-like direct entry to RCON*
        **Description**: Runs a custom RCON command.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}custom ServerInfo servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, rcon_command)
        if not data:
            data = "No response"
        embed = discord.Embed()
        embed.add_field(name=rcon_command, value=str(data))
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(server_name="server")
    @app_commands.choices(enable=[app_commands.Choice(name="enable", value="true"), app_commands.Choice(name="disable", value="false")])
    async def nametags(self, interaction: discord.Interaction, enable: str, server_name: str = config.default_server):
        """`{prefix}nametags enable/disable/true/false server_name`
        **Description**: Enables/disables nametags.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}nametags enable servername`
        """
        if not await check_perm_admin(interaction, server_name):
            return
        data, _ = await exec_server_command(server_name, f"ShowNameTags {enable}")
        if not data:
            data = "No response"
        if data.get("NametagsEnabled"):
            embed = discord.Embed(title=f"**Nametags enabled!** \n")
        else:
            embed = discord.Embed(title=f"**Nametags disabled!** \n")
        await interaction.response.send_message(embed=embed)

    # @app_commands.command()
    # async def repeat(self, interaction: discord.Interaction, cmdr: str, aot: str):
    #     """`{prefix}repeat "<command with args>" amount_of_times server_name`
    #     **Description**: Repeats a complete pavlov-bot command multiple times.
    #     **Requires**: Admin permissions for the server
    #     **Example**: `{prefix}repeat "GiveItem 89374583439127 rl_rpg servername" 10`
    #     """
    #     _args = cmdr.split(" ")
    #     cmd = _args[0]
    #     server_name = _args[-1]
    #     if not await check_perm_admin(ctx, server_name):
    #         return
    #     for i in range(int(aot)):
    #         command = self.bot.all_commands.get(cmd.lower())
    #         ctx.batch_exec = True
    #         await asyncio.sleep(0.2)
    #         if cmd.lower() == "repeat":
    #             return
    #         elif int(aot) > 100:
    #             return
    #         else:
    #             data = await command(ctx, *_args[1:])
    #         if data is None:
    #             data = "No response"
    #     embed = discord.Embed(title=f"Executed '{cmdr}' {aot} times")
    #     await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PavlovAdmin(bot))
