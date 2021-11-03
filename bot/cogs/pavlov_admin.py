import logging
import asyncio
from os import kill

import discord
from discord.ext import commands
from discord_components import Button, Select, SelectOption, ComponentsBot, ActionRow

from bot.utils import SteamPlayer, config, servers
from bot.utils.pavlov import check_perm_admin, exec_server_command
from bot.utils.players import (
    exec_command_all_players,
    exec_command_all_players_on_team,
    parse_player_command_results,
    spawn_pselect,
    spawn_iselect,
)


class PavlovAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def menu(self, ctx):
        async def actions(i1):
            await message.edit(content="")
            server_name = i1.values[0]
            if await check_perm_admin(ctx, server_name):
                embed = discord.Embed(title=f"**{server_name} Admin Menu**")
                ctx.interaction_exec = True
                slap = self.bot.all_commands.get("slap")
                giveitem = self.bot.all_commands.get("giveitem")
                kill = self.bot.all_commands.get("kill")
                components = [
                    self.bot.components_manager.add_callback(
                        Button(label="Godmode", custom_id="godmode"),
                        lambda interaction: slap(
                            ctx, "", "-99999999999999999", server_name, interaction
                        ),
                    ),
                    self.bot.components_manager.add_callback(
                        Button(label="Give Item", custom_id="giveitem"),
                        lambda interaction: giveitem(ctx, "", "", server_name, interaction),
                    ),
                    self.bot.components_manager.add_callback(
                        Button(label="Kill", custom_id="kill"),
                        lambda interaction: kill(ctx, "", server_name, interaction),
                    ),
                ]
                await i1.send(
                    embed=embed,
                    components=components,
                )
            else:
                return

        options = []
        for i in servers.get_names():
            options.append(SelectOption(label=str(i), value=str(i)))
        embed = discord.Embed(title="**Select a server below:**")
        # embed.set_author(name=ctx.author.display_name, url="", icon_url=ctx.author.avatar_url)
        message = await ctx.send(
            embed=embed,
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
        interaction: str = "",
    ):
        """`{prefix}giveitem <player_id/all/team> <item_id> <server_name>`
        **Description**: Spawns a item for a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveitem 89374583439127 tazer servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if ctx.interaction_exec:
            player_arg, interaction = await spawn_pselect(self, ctx, server_name, interaction)
            if player_arg == "NoPlayers":
                embed = discord.Embed(title=f"**No players on `{server_name}`**")
                await interaction.send(embed=embed)
                return
            item_id, interaction, iteml = await spawn_iselect(self, ctx, server_name, interaction)
            if item_id == "ListTooLong":
                embed = discord.Embed(
                    title=f"**Your item list `{iteml}` contains more than 25 items!**",
                    description="**Keep your item list to 25 items or lower.**",
                )
                await interaction.send(embed=embed)
                return

        if player_arg.casefold() == "all" or player_arg.startswith("team"):
            if player_arg.casefold() == "all":
                data = await exec_command_all_players(ctx, server_name, f"GiveItem all {item_id}")
            elif player_arg.startswith("team"):
                data = await exec_command_all_players_on_team(
                    ctx, server_name, player_arg, f"GiveItem team {item_id}"
                )
        else:
            if ctx.interaction_exec:
                data = await exec_server_command(
                    ctx, server_name, f"GiveItem {player_arg} {item_id}"
                )
            else:
                player = SteamPlayer.convert(player_arg)
                data = await exec_server_command(
                    ctx, server_name, f"GiveItem {player.unique_id} {item_id}"
                )
        embed = discord.Embed(title=f"**GiveItem {player_arg} {item_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.interaction_exec:
            await interaction.send(embed=embed)
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
    ):
        """`{prefix}givevehicle <player_id> <vehicle_id> <server_name>`
        **Description**: Spawns a vehicle near a player.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givevehicle 89374583439127 atv servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"GiveVehicle {player.unique_id} {vehicle_id}"
        )
        embed = discord.Embed(title=f"**GiveVehicle {player_arg} {vehicle_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
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
            data = await exec_server_command(
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
        data = await exec_server_command(ctx, server_name, f"GiveTeamCash {team_id} {cash_amount}")
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
    ):
        """`{prefix}setplayerskin <player_id/all/team> <skin_id> <server_name>`
        **Description**: Sets a player's skin to a specified skin.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}setplayerskin 89374583439127 clown servername`
        """
        if not await check_perm_admin(ctx, server_name):
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
            player = SteamPlayer.convert(player_arg)
            data = await exec_server_command(
                ctx, server_name, f"SetPlayerSkin {player.unique_id} {skin_id}"
            )
        embed = discord.Embed(title=f"**SetPlayerSkin {player_arg} {skin_id}** \n")
        embed = await parse_player_command_results(ctx, data, embed, server_name)
        if ctx.batch_exec:
            return embed.description
        await ctx.send(embed=embed)

    @commands.command()
    async def custom(self, ctx, rcon_command: str, server_name: str = config.default_server):
        """`{prefix}custom "<rcon_command with args>" server_name`
        **Description**: Runs a custom RCON command.
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}custom ServerInfo servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(ctx, server_name, rcon_command)
        if not data:
            data = "No response"
        if ctx.batch_exec:
            return data
        embed = discord.Embed()
        embed.add_field(name=rcon_command, value=str(data))
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
