import logging
import asyncio

import discord
from discord.ext import commands

from bot.utils import SteamPlayer, config
from bot.utils.pavlov import check_perm_admin, exec_server_command
from bot.utils.players import exec_command_all_players, exec_command_all_players_on_team


class PavlovAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def giveitem(
        self,
        ctx,
        player_arg: str,
        item_id: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}giveitem <player_id/all/team> <item_id> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveitem 89374583439127 tazer servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if player_arg == 'all':
            data = await exec_command_all_players(ctx, server_name, f"GiveItem all {item_id}")
            if data == "NoPlayers":
                embed = discord.Embed(description=f"No players on {server_name}")
            else:
                embed = discord.Embed(description=f"{data}")
        elif player_arg.startswith('team'):
            data = await exec_command_all_players_on_team(ctx, server_name, player_arg, f"GiveItem team {item_id}")
            if data == "NoPlayers":
                embed = discord.Embed(description=f"No players on {server_name}")
            elif data == "NotValidTeam":
                embed = discord.Embed(description=f"**Invalid team. Must be number team0/team1 or teamblue/teamred**\n")
            else:
                embed = discord.Embed(description=f"{data}")
        else:
            player = SteamPlayer.convert(player_arg)
            data = await exec_server_command(
                ctx, server_name, f"GiveItem {player.unique_id} {item_id}"
            )
            give_team = data.get("GiveItem")
            if ctx.batch_exec:
                return give_team
            if not give_team:
                embed = discord.Embed(
                    description=f"**Failed** to give {item_id} to <{player.unique_id}>"
                )
            else:
                embed = discord.Embed(
                    description=f"{item_id} given to <{player.unique_id}>"
                )
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

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givevehicle 89374583439127 atv servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        player = SteamPlayer.convert(player_arg)
        data = await exec_server_command(
            ctx, server_name, f"GiveVehicle {player.unique_id} {vehicle_id}"
        )
        givev = data.get("GiveVehicle")
        if ctx.batch_exec:
            return givev
        if not givev:
            embed = discord.Embed(
                description=f"**Failed** to give {vehicle_id} to <{player.unique_id}>"
            )
        else:
            embed = discord.Embed(
                description=f"{vehicle_id} given to <{player.unique_id}>"
            )
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

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givecash 89374583439127 5000 servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if player_arg == 'all':
            data = await exec_command_all_players(ctx, server_name, f"GiveCash all {skin_id}")
            if data == "NoPlayers":
                embed = discord.Embed(description=f"No players on {server_name}")
            else:
                embed = discord.Embed(description=f"{data}")
        else:
            player = SteamPlayer.convert(player_arg)
            data = await exec_server_command(
                ctx, server_name, f"GiveCash {player.unique_id} {cash_amount}"
            )
            give_cash = data.get("GiveCash")
            if ctx.batch_exec:
                return give_cash
            if not give_cash:
                embed = discord.Embed(
                    description=f"**Failed** to give {cash_amount} to <{player.unique_id}>"
                )
            else:
                embed = discord.Embed(
                    description=f"{cash_amount} given to <{player.unique_id}>"
                )
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

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveteamcash 0 5000 servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        data = await exec_server_command(
            ctx, server_name, f"GiveTeamCash {team_id} {cash_amount}"
        )
        give_team_cash = data.get("GiveTeamCash")
        if ctx.batch_exec:
            return give_team_cash
        if not give_team_cash:
            embed = discord.Embed(
                description=f"**Failed** to give {cash_amount} to <{team_id}>"
            )
        else:
            embed = discord.Embed(description=f"{cash_amount} given to <{team_id}>")
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

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}setplayerskin 89374583439127 clown servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        if player_arg == 'all':
            data = await exec_command_all_players(ctx, server_name, f"SetPlayerSkin all {skin_id}")
            if data == "NoPlayers":
                embed = discord.Embed(description=f"No players on {server_name}")
            else:
                embed = discord.Embed(description=f"{data}")
        elif player_arg.startswith('team'):
            data = await exec_command_all_players_on_team(ctx, server_name, player_arg, f"SetPlayerSkin team {skin_id}")
            if data == "NoPlayers":
                embed = discord.Embed(description=f"No players on {server_name}")
            elif data == "NotValidTeam":
                embed = discord.Embed(description=f"**Invalid team. Must be number team0/team1 or teamblue/teamred**\n")
            else:
                embed = discord.Embed(description=f"{data}")
        else:
            player = SteamPlayer.convert(player_arg)
            data = await exec_server_command(
                ctx, server_name, f"SetPlayerSkin {player.unique_id} {skin_id}"
            )
            set_player_skin = data.get("SetPlayerSkin")
            if ctx.batch_exec:
                return set_player_skin
            if not set_player_skin:
                embed = discord.Embed(
                    description=f"**Failed** to set <{player.unique_id}>'s skin to {skin_id}"
                )
            else:
                embed = discord.Embed(
                    description=f"<{player.unique_id}>'s skin set to {skin_id}"
                )
        await ctx.send(embed=embed)

    @commands.command()
    async def custom(
        self, ctx, rcon_command: str, server_name: str = config.default_server
    ):
        """`{prefix}custom "<rcon_command with args>" server_name`

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
    async def repeat(
        self, ctx, cmdr: str, aot: str
    ):
        """`{prefix}repeat "<command with args>" amount_of_times server_name`

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
            if cmd.lower() == 'repeat':
                return
            elif int(aot) > 100:
                return
            else:
                data = await command(ctx, *_args[1:])
            if data is None:
                data = "No response"
        embed = discord.Embed(
            description=f"Executed '{cmdr}' {aot} times"
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PavlovAdmin(bot))
