import logging
from bot.utils import servers, polling
from bot.utils.pavlov import exec_server_command
from bot.utils.players import get_teams, get_kda
import discord
import asyncio
import random
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
                logging.info(f"Task {poll} created for server {server}")
                asyncio.create_task(
                    self.new_poll(
                        pollings,
                        server,
                        poll,
                    )
                )

    async def new_poll(self, pollings, server: str, poll: str):
        while True:
            if pollings.get("type") == "player":
                interval = float(pollings.get("polling_interval")) * 60
                await asyncio.sleep(interval)
                logging.info(f"Executing Task {poll} on server {server}")
                await self.player_polling(pollings, server, poll)
            if pollings.get("type") == "autobalance":
                interval = float(pollings.get("polling_interval")) * 60
                await asyncio.sleep(interval)
                logging.info(f"Executing Task {poll} on server {server}")
                await self.autobalance_polling(pollings, server, poll)

    async def player_polling(self, pollings, server, poll: str):
        channel = self.bot.get_channel(int(pollings.get("polling_channel")))
        ctx = ""
        data = await exec_server_command(ctx, server, "RefreshList")
        player_list = data.get("PlayerList")
        t_values = {
            "servername": server,
            "aplayers": len(player_list),
        }
        if len(player_list) >= int(pollings.get("amount_of_players_trigger")):
            embed = discord.Embed(title=pollings.get("polling_message").format(**t_values))
            # embed.add_field(name="Mention", value="<@&" + pollings.get('polling_role') + ">")
            await channel.send(embed=embed)

    async def autobalance_polling(self, pollings, server, poll: str):
        channel = self.bot.get_channel(int(pollings.get("polling_channel")))
        ctx = ""
        teamblue, teamred = await get_teams(server)
        kdalist = await get_kda(server)
        for k, v in kdalist.items():
            kda = v.split("/")
            if int(kda[2]) > int(pollings.get("tk_threshold")):
                if pollings.get("tk_action").casefold() == "kick":
                    await exec_server_command(ctx, server, f"Kick {k}")
                elif pollings.get("tk_action").casefold() == "ban":
                    await exec_server_command(ctx, server, f"Ban {k}")
        if len(teamblue) == len(teamred):
            pass
        elif len(teamred) - 1 == len(teamblue) and len(teamred) == len(teamblue) + 1:
            pass
        else:
            try:
                while True:
                    teamblue, teamred = await get_teams(server)
                    print(len(teamblue) + " " + len(teamred))
                    if len(teamred) - 1 == len(teamblue) and len(teamred) == len(teamblue) + 1:
                        raise Exception
                    elif len(teamblue) > len(teamred):
                        data = await exec_server_command(
                            ctx, server, f"SwitchTeam {random.choice(teamblue)} 1"
                        )
                        print(data)
                    elif len(teamred) > len(teamblue):
                        data = await exec_server_command(
                            ctx, server, f"SwitchTeam {random.choice(teamred)} 0"
                        )
                        print(data)
            except:
                pass
            embed = discord.Embed(title=f"Autobalanced `{server}`")
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Polling(bot))
