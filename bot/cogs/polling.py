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
        polls = polling.get_names()
        for poll in polls:
            pollings = polling.get(poll)
            servers = pollings.get("servers").split(" ")
            for server in servers:
                if pollings.get("type") == "player":
                    logging.info(f"Task {poll} created for server {server}")
                    asyncio.create_task(
                        self.new_player_poll(
                            float(pollings.get("player_polling_interval")) * 60,
                            pollings,
                            server,
                            poll,
                        )
                    )

    async def new_player_poll(self, interval: float, pollings, server: str, poll: str):
        while True:
            await asyncio.sleep(interval)
            await self.player_polling(pollings, server, poll)

    async def player_polling(self, pollings, server, poll: str):
        logging.info(f"Executing Task {poll} on server {server}")
        channel = self.bot.get_channel(int(pollings.get("player_polling_channel")))
        ctx = ""
        data = await exec_server_command(ctx, server, "RefreshList")
        player_list = data.get("PlayerList")
        t_values = {
            "servername": server,
            "aplayers": len(player_list),
        }
        if len(player_list) >= int(pollings.get("amount_of_players_trigger")):
            embed = discord.Embed(title=pollings.get("player_polling_message").format(**t_values))
            # embed.add_field(name="Mention", value="<@&" + pollings.get('player_polling_role') + ">")
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Polling(bot))
