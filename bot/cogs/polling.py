import logging
from bot.utils import servers, polling
from bot.utils.pavlov import exec_server_command
from bot.utils.players import get_stats
from collections import namedtuple
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
                try:
                    state = await self.player_polling(pollings, server, state)
                except:
                    state = await self.player_polling(pollings, server, '')
            if pollings.get("type") == "autobalance":
                interval = float(pollings.get("polling_interval")) * 60
                await asyncio.sleep(interval)
                logging.info(f"Executing Task {poll} on server {server}")
                await self.autobalance_polling(pollings, server, poll)

    async def player_polling(self, pollings, server, old_state: str):
        channel = self.bot.get_channel(int(pollings.get("polling_channel")))
        ctx = 'noctx'
        logging.info(f"Starting poll with state: {old_state}")
        data = await exec_server_command(ctx, server, "RefreshList")
        amt = len(data.get("PlayerList"))
        logging.info(f"Server has {amt} players")
        lows, meds, highs = pollings.get("low_threshold"), pollings.get("medium_threshold"), pollings.get("high_threshold")
        if int(highs) <= amt:
            new_state = 'high'
            logging.info(f"New state is {new_state}")
            embed = discord.Embed(title=f"`{server}` has high population! {amt} players are on!")
            if old_state == new_state:
                return new_state
            else:
                await channel.send(pollings.get('polling_role'),embed=embed)
                return new_state
        elif int(meds) <= amt:
            new_state = 'medium'
            logging.info(f"New state is {new_state}")
            embed = discord.Embed(title=f"`{server}` has medium population! {amt} players are on!")
            if old_state == new_state:
                return new_state
            else:
                await channel.send(pollings.get('polling_role'),embed=embed)
                return new_state
        elif int(lows) <= amt:
            new_state = 'low'
            logging.info(f"New state is {new_state}")
            embed = discord.Embed(title=f"`{server}` has low population! {amt} players are on!")
            if old_state == new_state:
                return new_state
            else:
                await channel.send(pollings.get('polling_role'),embed=embed)
                return new_state
                

    async def autobalance_polling(self, pollings, server, poll: str):
        channel = self.bot.get_channel(int(pollings.get("polling_channel")))
        ctx = 'noctx'
        teamblue, teamred, kdalist, alivelist = await get_stats(ctx, server)
        for k, v in kdalist.items():
            if v == "None":
                v = "0/0/0"
            kda = v.split("/")
            score = int(kda[2])  
            if score < int(pollings.get("tk_threshold")):
                logging.info(f"Task {poll}: TK threshold triggered for {k}")
                logging.info(f"Task {poll}: Peforming tk action {pollings.get('tk_action')}")
                if pollings.get("tk_action").casefold() == "kick":
                    await exec_server_command(ctx, server, f"Kick {k}")
                    logging.info(f"Player {k} kicked for TK from server {server} at score {score}")
                elif pollings.get("tk_action").casefold() == "ban":
                    await exec_server_command(ctx, server, f"Ban {k}")
                    logging.info(f"Player {k} banned for TK from server {server} at score {score}")
                elif pollings.get("tk_action").casefold() == "test":
                    logging.info(f"Player {k} would have been actioned for TK from server {server} at score {score}")
                    pass
        logging.info(f"Starting autobalance at {len(teamblue)}/{len(teamred)}")
        if len(teamblue) == len(teamred):
            logging.info(f"Exiting autobalance on equal teams")
            pass
        elif len(teamred) - 1 == len(teamblue) or len(teamred) + 1 == len(teamblue):
            logging.info(f"Exiting autobalance on odd number equal teams")
            pass
        elif int(pollings.get("autobalance_min_players")) > len(teamblue) + len(teamred):
            logging.info(f"Exiting autobalance on min players")
            pass
        elif int(pollings.get("autobalance_tolerance")) < abs(len(teamblue) - len(teamred)):
            try:
                while True:
                    teamblue, teamred, kdalist, alivelist = await get_stats(ctx, server)
                    print(len(teamblue) + " " + len(teamred))
                    if len(teamred) - 1 == len(teamblue) and len(teamred) == len(teamblue) + 1:
                        raise Exception
                    elif len(teamblue) > len(teamred):
                        switcher = random.choice(teamblue)
                        logging.info(f"Player {switcher} moved from blue to red on {server} at playercount {len(teamblue) + len(teamred)} ratio {len(teamblue)}/{len(teamred)} ")
                        if pollings.get("autobalance_testing"):
                            logging.info(f"Just testing")
                            pass
                        else:
                            data = await exec_server_command(
                                ctx, server, f"SwitchTeam {switcher} 1"
                            )
                            print(data)
                    elif len(teamred) > len(teamblue):
                        switcher = random.choice(teamred)
                        logging.info(f"Player {switcher} moved from red to blue on {server} at playercount {len(teamblue) + len(teamred)} ratio {len(teamblue)}/{len(teamred)} ")
                        if pollings.get("autobalance_testing"):
                            logging.info(f"Just testing")
                            pass
                        else:
                            data = await exec_server_command(
                                ctx, server, f"SwitchTeam {switcher} 0"
                            )
                            print(data)
            except:
                pass
            embed = discord.Embed(title=f"Autobalanced `{server}`")
            await channel.send(embed=embed)
        else:
            logging.info(f"Exiting autobalance on tolerence players")

def setup(bot):
    bot.add_cog(Polling(bot))
