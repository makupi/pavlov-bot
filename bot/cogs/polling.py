import logging
from bot.utils import servers
from bot.utils.pavlov import exec_server_command
import discord
import asyncio
from discord.ext import tasks, commands


class Polling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")
        lservers = servers.get_names()
        for i in lservers:
            server = servers.get(i)
            if server.get("player_polling") == "True":
                asyncio.create_task(self.new_player_poll(float(servers.get('default').get('PPInterval') ) * 60, i ))


    async def new_player_poll(self, interval: float, server_name: str):
        while True:
            await asyncio.sleep(interval)
            await self.player_polling(server_name)

    async def player_polling(self, server_name):
        channel = self.bot.get_channel(int(servers.get(server_name).get('player_polling_channel')))
        ctx = ''
        data = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = data.get("PlayerList")
        if len(player_list) == 0:
            embed = discord.Embed(title=f"{len(player_list)} players on `{server_name}`\n")
        else:
            if len(player_list) == 1:
                embed = discord.Embed(title=f"{len(player_list)} player on `{server_name}`:\n")
            else:
                embed = discord.Embed(title=f"{len(player_list)} players on `{server_name}`:\n")
            embed.description = '\n'
            for player in player_list:
                await asyncio.sleep(0.1)
                data2 = await exec_server_command(ctx, server_name, f"InspectPlayer {player.get('UniqueId')}")
                team_id = data2.get("PlayerInfo").get("TeamId")
                dead = data2.get("PlayerInfo").get("Dead")
                if team_id == "0":
                    team_name = ":blue_square:"
                elif team_id == "1":
                    team_name = ":red_square:"
                if dead == True:
                    dead = ':skull:'
                elif dead == False:
                    dead = ':slight_smile:'
                embed.description += f"\n - {dead} {team_name} {player.get('Username', '')} <{player.get('UniqueId')}>"
        await channel.send(embed=embed)



def setup(bot):
    bot.add_cog(Polling(bot))
