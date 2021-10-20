import logging
from bot.utils import servers, polling
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
            pollings = polling.get(i)
            if pollings.get("player_polling") == "True":
                asyncio.create_task(self.new_player_poll(float(polling.get(i).get('player_polling_interval')) * 60, i ))


    async def new_player_poll(self, interval: float, server_name: str):
        while True:
            await asyncio.sleep(interval)
            await self.player_polling(server_name)

    async def player_polling(self, server_name):
        channel = self.bot.get_channel(int(polling.get(server_name).get('player_polling_channel')))
        ctx = ''
        data = await exec_server_command(ctx, server_name, "RefreshList")
        player_list = data.get("PlayerList")
        t_values = {
        'servername': server_name,
        'aplayers': len(player_list),
        }
        if len(player_list) >= int(polling.get(server_name).get('amount_of_players_trigger')):
            embed = discord.Embed(title=polling.get(server_name).get('player_polling_message').format(**t_values))
            await channel.send(embed=embed)



def setup(bot):
    bot.add_cog(Polling(bot))
