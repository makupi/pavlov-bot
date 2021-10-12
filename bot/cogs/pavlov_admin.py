import logging
import asyncio

import discord
from discord.ext import commands

from bot.utils import SteamPlayer, config
from bot.utils.pavlov import check_perm_admin, exec_server_command


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
        """`{prefix}giveitem <player_id> <item_id> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveitem 89374583439127 tazer servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
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
    async def giveall(
        self,
        ctx,
        item_id: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}giveall <item_id> <server_name>`
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}giveall rl_rpg servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        embed = discord.Embed(description=f"**{item_id} given to all**\n")
        players = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = players.get("PlayerList")
        for player in player_list:
            await asyncio.sleep(0.2)
            data = await exec_server_command(
                ctx, server_name, f"GiveItem {player.get('UniqueId')} {item_id}"
            )
            work = data.get("GiveItem")
            if not work:
                embed.description += f"\n **Failed** to give {item_id} to <{player.get('UniqueId')}>"
            else:
                embed.description += f"\n {item_id} given to <{player.get('UniqueId')}>"
        await ctx.send(embed=embed)
    
    @commands.command()
    async def spsall(
        self,
        ctx,
        skin_id: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}spsall <skin_id> <server_name>`
        **Requires**: Admin permissions for the server
        **Example**: `{prefix}spsall clown servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
        embed = discord.Embed(description=f"**All players skin set to {skin_id}**\n")
        players = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = players.get("PlayerList")
        for player in player_list:
            await asyncio.sleep(0.2)
            data = await exec_server_command(
                ctx, server_name, f"SetPlayerSkin {player.get('UniqueId')} {skin_id}"
            )
            work = data.get("SetPlayerSkin")
            if not work:
                embed.description += f"\n **Failed** to set <{player.get('UniqueId')}>'s skin to {skin_id}"
            else:
                embed.description += f"\n <{player.get('UniqueId')}>'s skin set to {skin_id}"
        await ctx.send(embed=embed)
    
    @commands.command()
    async def givecash(
        self,
        ctx,
        player_arg: str,
        cash_amount: str,
        server_name: str = config.default_server,
    ):
        """`{prefix}givecash <player_id> <cash_amount> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}givecash 89374583439127 5000 servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
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
        """`{prefix}setplayerskin <player_id> <skin_id> <server_name>`

        **Requires**: Admin permissions for the server
        **Example**: `{prefix}setplayerskin 89374583439127 clown servername`
        """
        if not await check_perm_admin(ctx, server_name):
            return
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
