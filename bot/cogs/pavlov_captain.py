import asyncio
import logging
import random
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils import SteamPlayer, aliases, config, servers
from bot.utils.pavlov import check_perm_captain, exec_server_command
from bot.utils.players import (
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

    # @app_commands.command()
    # async def gamesetup(self, interaction: discord.Interaction):
    #     """`{prefix}gamesetup` - *Starts a button driven game session in Discord*
    #             **Description**: Starts a button driven game session in Discord.
    #             **Requires**: Captain permissions for the server
    #             """
    #     async def actions(interact, msg, server_name: str = ""):
    #         gamesetup = self.bot.all_commands.get("gamesetup")
    #         await msg.edit(content="")
    #         if server_name == "":
    #             server_name = interact.values[0]
    #         elif "offline" in server_name.lower():
    #             embed = discord.Embed(title="Server is offline.")
    #             await interact.send(embed=embed)
    #             return
    #         if await check_perm_captain(ctx, server_name):
    #             ctx.interaction_exec = True
    #             matchsetup = self.bot.all_commands.get("matchsetup")
    #             resetsnd = self.bot.all_commands.get("resetsnd")
    #             switchmap = self.bot.all_commands.get("switchmap")
    #             embed = discord.Embed(title=f"**{server_name} Match Menu**")
    #             team_one, interact = await spawn_team_select(ctx, interact, 1)
    #             team_two, interact = await spawn_team_select(ctx, interact, 2)
    #             #               if team_one == "empty" and team_two == "empty":
    #             #                 embed.description = (
    #             #                        "**No teams defined in aliases.json! Team buttons disabled.**"
    #             #                    )
    #             #                    await i1.send(
    #             #                        embed=embed,
    #             #                        components=[
    #             #                            self.bot.components_manager.add_callback(
    #             #                                Button(label=f"ResetSND"),
    #             #                                lambda interaction: resetsnd(ctx, server_name, interaction),
    #             #                            )
    #             #                        ],
    #             #                    )
    #             if team_one == team_two:
    #                 embed.description = "**Duplicate teams detected! Team buttons disabled.**"
    #                 await interact.send(
    #                     embed=embed,
    #                     components=[
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"ResetSND",
    #                             ),
    #                             lambda interaction: resetsnd(ctx, server_name, interaction),
    #                         ),
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"Change Settings",
    #                             ),
    #                             lambda interaction: actions(interaction, msg, server_name),
    #                         ),
    #                     ],
    #                 )
    #             #               elif team_one == "empty":
    #             #                   embed.description = "**Missing team one! Team buttons disabled.**"
    #             #                   await i1.send(
    #             #                       embed=embed,
    #             #                       components=[
    #             #                           self.bot.components_manager.add_callback(
    #             #                               Button(label=f"ResetSND"),
    #             #                               lambda interaction: resetsnd(ctx, server_name, interaction),
    #             #                           ),
    #             #                           self.bot.components_manager.add_callback(
    #             #                               Button(label=f"Change Settings"),
    #             #                               lambda interaction: actions(interaction, msg, server_name),
    #             #                           ),
    #             #                       ],
    #             #                   )
    #             #               elif team_two == "empty":
    #             #                   embed.description = "**Missing team two! Team buttons disabled.**"
    #             #                   await i1.send(
    #             #                       embed=embed,
    #             #                       components=[
    #             #                           self.bot.components_manager.add_callback(
    #             #                               Button(label=f"ResetSND"),
    #             #                               lambda interaction: resetsnd(ctx, server_name, interaction),
    #             #                           ),
    #             #                           self.bot.components_manager.add_callback(
    #             #                               Button(label=f"Change Settings"),
    #             #                               lambda interaction: actions(interaction, msg, server_name),
    #             #                           ),
    #             #                      ],
    #             #                   )
    #             else:
    #                 await interact.send(
    #                     embed=embed,
    #                     components=[
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"CT: {team_one} vs T: {team_two}",
    #                             ),
    #                             lambda interaction: matchsetup(
    #                                 ctx, team_one, team_two, server_name, interaction
    #                             ),
    #                         ),
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"CT: {team_two} vs T: {team_one}",
    #                             ),
    #                             lambda interaction: matchsetup(
    #                                 ctx, team_two, team_one, server_name, interaction
    #                             ),
    #                         ),
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"ResetSND",
    #                             ),
    #                             lambda interaction: resetsnd(ctx, server_name, interaction),
    #                         ),
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"Change Settings",
    #                             ),
    #                             lambda interaction: gamesetup(ctx, interaction),
    #                         ),
    #                         self.bot.components_manager.add_callback(
    #                             Button(
    #                                 label=f"Switch Map",
    #                             ),
    #                             lambda interaction: switchmap(
    #                                 ctx, "", "", server_name, interaction
    #                             ),
    #                         ),
    #                     ],
    #                 )
    #         else:
    #             return
    #
    #     options, embed = await spawn_server_select(ctx, "Game Setup Menu")
    #     if ctx.interaction_exec:
    #         message = await __interaction.send(
    #             embed=embed,
    #             components=[
    #                 self.bot.components_manager.add_callback(
    #                     Select(placeholder="Server", options=options),
    #                     lambda interaction: actions(interaction, message),
    #                 )
    #             ],
    #         )
    #     else:
    #         message = await interaction.response.send_message(
    #             embed=embed,
    #             components=[
    #                 self.bot.components_manager.add_callback(
    #                     Select(placeholder="Server", options=options),
    #                     lambda interaction: actions(interaction, message),
    #                 )
    #             ],
    #         )

    @app_commands.command()
    @app_commands.describe(map_id="ID of the map to switch to", game_mode="Game mode for the map")
    @app_commands.rename(server_name="server")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def switchmap(
        self,
        interaction: discord.Interaction,
        map_id: str,
        game_mode: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}switchmap <map_name> <game_mode> <server_name>` - *Switches map
        **Description**: Switches to requested map and mode. Will download map if required.
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}switchmap 89374583439127 servername`
        **Alias**: switchmap can be shortened to just map `{prefix}map 89374583439127 servername`
        """
        if not await check_perm_captain(interaction, server_name):
            return

        map_label = aliases.get_map(map_id)
        data = await exec_server_command(
            server_name, f"SwitchMap {map_label} {game_mode.upper()}"
        )
        switch_map = data.get("SwitchMap")
        if not switch_map:
            embed = discord.Embed(
                title=f"**Failed** to switch map to {map_id} with game mode {game_mode.upper()} on {server_name}."
            )
            await interaction.response.send_message(embed=embed)
            return
        embed = discord.Embed(
            title=f"Switched map to {map_id} with game mode {game_mode.upper()} on {server_name}."
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(server_name="server")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def resetsnd(
        self, interaction: discord.Interaction, server_name: str = config.default_server
    ):
        """`{prefix}resetsnd <server_name>` - *Issues ResetSND command*
        **Description**: Issues ResetSND command that restarts game with same teams
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}resetsnd servername`
        """

        if not await check_perm_captain(interaction, server_name):
            return
        data = await exec_server_command(server_name, "ResetSND")
        reset_snd = data.get("ResetSND")
        if not reset_snd:
            embed = discord.Embed(title=f"**Failed** to reset SND on {server_name}.")
        else:
            embed = discord.Embed(title=f"SND has been successfully reset on {server_name}.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(player_arg="player", team_id="team", server_name="server")
    @app_commands.autocomplete(player_arg=aliases.players_autocomplete, server_name=servers.autocomplete)
    async def switchteam(
        self,
        interaction: discord.Interaction,
        player_arg: str,
        team_id: int,
        server_name: str = config.default_server,
    ):
        """`{prefix}switchteam <player_id> <team_id> <server_name>` - *Moves player to team*
        **Description**: Moves player to requested team
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}resetsnd 89374583439127 0 servername`
        """
        if not await check_perm_captain(interaction, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            server_name, f"SwitchTeam {player.unique_id} {team_id}"
        )
        embed = discord.Embed(title=f"**SwitchTeam {player_arg} {team_id}** \n")
        embed = await parse_player_command_results(data, embed, server_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(server_name="server")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def rotatemap(self, interaction: discord.Interaction, server_name: str = config.default_server):
        """`{prefix}rotatemap <server_name>` - *Changes map to next in rotation*
        **Description**: Changes map to next in Game.ini
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}rotatemap servername`
        **Aliases**: rotatemap can also be called as next `{prefix}next servername`
        """
        if not await check_perm_captain(interaction, server_name):
            return
        data = await exec_server_command(server_name, f"RotateMap")
        rotate_map = data.get("RotateMap")
        if not rotate_map:
            embed = discord.Embed(title=f"**Failed** to rotate map on {server_name}.")
        else:
            embed = discord.Embed(title=f"Rotated map successfully on {server_name}.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(team_a_name="team-a", team_b_name="team-b", server_name="server")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def matchsetup(
        self,
        interaction: discord.Interaction,
        team_a_name: str,
        team_b_name: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}matchsetup <CT team name> <T team name> <server name>` - *Sets up SND match with teams*
        **Description**: Sets up an SND match with teams
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}matchsetup ct_team t_team servername`
        """
        if not await check_perm_captain(interaction, server_name):
            return
        before = datetime.now()
        teams = [aliases.get_team(team_a_name), aliases.get_team(team_b_name)]
        embed = discord.Embed()
        for team in teams:
            embed.add_field(name=f"{team.name} members", value=team.member_repr(), inline=False)
        await interaction.response.send_message(embed=embed)

        for index, team in enumerate(teams):
            for member in team.members:
                await exec_server_command(
                    server_name, f"SwitchTeam {member.unique_id} {index}"
                )
                await asyncio.sleep(RCON_COMMAND_PAUSE)
        embed = discord.Embed(
            title=f"Teams set up. Resetting SND in {MATCH_DELAY_RESETSND} seconds on {server_name}."
        )
        await interaction.response.send_message(embed=embed)

        await asyncio.sleep(MATCH_DELAY_RESETSND)
        await exec_server_command(server_name, "ResetSND")
        embed = discord.Embed(title=f"SND has been reset on {server_name}. Good luck!")
        embed.set_footer(text=f"Execution time: {datetime.now() - before}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.rename(server_name="server")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def flush(
        self,
        interaction: discord.Interaction,
        server_name: str = config.default_server
    ):
        """`{prefix}flush <servername>` - *Randomly kicks a player not in aliases*
        **Description**: Randomly picks player not in aliases and kicks them. Useful for joining full server
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}flush snd1`
        """
        if not await check_perm_captain(interaction, server_name):
            return
        data = await exec_server_command(server_name, "RefreshList")
        player_list = data.get("PlayerList")
        non_alias_player_ids = list()
        for player in player_list:
            check = aliases.find_player_alias(player.get("UniqueId"))
            if check is None:
                non_alias_player_ids.append(player.get("UniqueId"))
        if len(non_alias_player_ids) == 0:
            embed = discord.Embed(title=f"No players to flush on `{server_name}`")
            await interaction.response.send_message(embed=embed)
            return
        to_kick_id = random.choice(non_alias_player_ids)
        data = await exec_server_command(server_name, f"Kick {to_kick_id}")
        kick = data.get("Kick")
        if not kick:
            embed = discord.Embed(title=f"Encountered error while flushing on `{server_name}`")
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title=f"Successfully flushed `{server_name}`")
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(pin="4 digit pin or 'remove' to remove")
    @app_commands.rename(server_name="server")
    @app_commands.autocomplete(server_name=servers.autocomplete)
    async def setpin(self, interaction: discord.Interaction, pin: str, server_name: str = config.default_server):
        """`{prefix}setpin <pin> <server_name>` - *Changes server pin*
        **Description**: Sets a password for your server. Must be 4-digits or Use keyword "remove" to unset
        **Requires**: Captain permissions or higher for the server
        **Example**: `{prefix}setpin 0000 servername`
        """
        if not await check_perm_captain(interaction, server_name):
            return
        if len(pin) == 4 and pin.isdigit():
            data = await exec_server_command(server_name, f"SetPin {pin}")
        elif pin.lower() == "remove":
            data = await exec_server_command(server_name, f"SetPin")
        else:
            embed = discord.Embed(title=f"Pin must be either a 4-digit number or remove")
            await interaction.response.send_message(embed=embed)
            return
        spin = data.get("Successful")
        if not spin:
            embed = discord.Embed(title=f"**Failed** to set pin {pin}")
        else:
            if pin.lower() == "remove":
                embed = discord.Embed(title=f"Pin removed")
            else:
                embed = discord.Embed(title=f"Pin {pin} successfully set")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PavlovCaptain(bot))
