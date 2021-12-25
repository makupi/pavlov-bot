import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from bot.utils import polling
from bot.utils.pavlov import exec_server_command

CHECK_INTERVAL = 15


class Polling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._tasks = dict()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")
        polls = polling.get_names()
        for poll in polls:
            poll_config = polling.get(poll)
            poll_servers = poll_config.get("servers")
            for server in poll_servers:
                logging.info(f"Task {poll} created for server {server}")
                task = asyncio.create_task(
                    self.new_poll(
                        poll_config,
                        server,
                        poll,
                    )
                )
                self._tasks[poll] = task

    async def new_poll(self, poll_config: dict, server: str, name: str):
        if poll_config.get("type").lower() == "player":
            interval = poll_config.get("polling_interval") * 60
            state = None
            ctx = None

            while True:
                try:
                    await asyncio.sleep(interval)
                    logging.info(f"Executing Task {name} on server {server}")
                    state, ctx = await self.player_polling(ctx, poll_config, server, state)
                    # if poll_config.get("type") == "autobalance":
                    #    interval = float(poll_config.get("polling_interval")) * 60
                    #    await asyncio.sleep(interval)
                    #    logging.info(f"Executing Task {poll} on server {server}")
                    #    await self.autobalance_polling(poll_config, server, poll)
                except Exception as e:
                    await asyncio.sleep(1)
                    logging.info(
                        f"Exception occurred while trying to execute {name} on server {server}! Exception: {e}"
                    )
                    pass

    async def player_polling(
        self,
        ctx: Optional[commands.Context],
        poll_config: dict,
        server: str,
        old_state: Optional[str],
    ):
        channel = self.bot.get_channel(poll_config.get("polling_channel"))
        logging.info(f"Starting poll on {server} with state: {old_state}")
        data, ctx = await exec_server_command(ctx, server, "RefreshList", True)
        player_count = len(data.get("PlayerList"))
        p_role = "<@&" + str(poll_config.get("polling_role")) + ">"
        logging.info(f"{server} has {player_count} players")
        lows, meds, highs = (
            poll_config.get("low_threshold"),
            poll_config.get("medium_threshold"),
            poll_config.get("high_threshold"),
        )
        if player_count > highs:
            new_state = "high"
        elif player_count > meds:
            new_state = "medium"
        elif player_count > lows:
            new_state = "low"
        else:
            return None, ctx
        if old_state == new_state:
            logging.info(f"State has not changed.")
            return new_state, ctx
        logging.info(f"New state for server is {new_state}")
        embed = discord.Embed(
            title=f"`{server}` has {new_state} population! {player_count} players are on!"
        )
        if poll_config.get("show_scoreboard"):
            players_command = self.bot.all_commands.get("players")
            scoreboard = await players_command(ctx, server)
            embed.description = scoreboard
        await channel.send(p_role, embed=embed)
        return new_state, ctx

    # async def autobalance_polling(self, poll_config, server, poll: str):
    #    channel = self.bot.get_channel(int(poll_config.get("polling_channel")))
    #    ctx = 'noctx'
    #    teamblue, teamred, kdalist, alivelist, scorelist = await get_stats(ctx, server)
    #    for k, v in scorelist.items():
    #        if v is None:
    #            score = 0
    #        score = int(v)
    #        if score < int(poll_config.get("tk_threshold")):
    #            logging.info(f"Task {poll}: TK threshold triggered for {k}")
    #            logging.info(f"Task {poll}: Peforming tk action {poll_config.get('tk_action')}")
    #            if poll_config.get("tk_action").casefold() == "kick":
    #                await exec_server_command(ctx, server, f"Kick {k}")
    #                logging.info(f"Player {k} kicked for TK from server {server} at score {score}")
    #            elif poll_config.get("tk_action").casefold() == "ban":
    #                await exec_server_command(ctx, server, f"Ban {k}")
    #                logging.info(f"Player {k} banned for TK from server {server} at score {score}")
    #            elif poll_config.get("tk_action").casefold() == "test":
    #                logging.info(f"Player {k} would have been actioned for TK from server {server} at score {score}")
    #                pass
    #    logging.info(f"Starting autobalance at {len(teamblue)}/{len(teamred)}")
    #    if len(teamblue) == len(teamred):
    #        logging.info(f"Exiting autobalance on equal teams")
    #        pass
    #    elif len(teamred) - 1 == len(teamblue) or len(teamred) + 1 == len(teamblue):
    #        logging.info(f"Exiting autobalance on odd number equal teams")
    #        pass
    #    elif int(poll_config.get("autobalance_min_players")) > len(teamblue) + len(teamred):
    #        logging.info(f"Exiting autobalance on min players")
    #        pass
    #    elif int(poll_config.get("autobalance_tolerance")) < abs(len(teamblue) - len(teamred)):
    #        try:
    #            while True:
    #                teamblue, teamred, kdalist, alivelist, scorelist = await get_stats(ctx, server)
    #                logging.info(f"Blue:{len(teamblue)} Red: {len(teamred)}")
    #                if len(teamred) == len(teamblue):
    #                    raise Exception
    #                elif len(teamred) - 1 == len(teamblue) or len(teamred) + 1 == len(teamblue):
    #                    raise Exception
    #                elif len(teamblue) > len(teamred):
    #                    switcher = random.choice(teamblue)
    #                    logging.info(f"Player {switcher} moved from blue to red on {server} at playercount {len(teamblue) + len(teamred)} ratio {len(teamblue)}/{len(teamred)} ")
    #                    if poll_config.get("autobalance_testing"):
    #                        logging.info(f"Just testing")
    #                        pass
    #                    else:
    #                        await exec_server_command(ctx, server, f"SwitchTeam {switcher} 1")
    #                elif len(teamred) > len(teamblue):
    #                    switcher = random.choice(teamred)
    #                    logging.info(f"Player {switcher} moved from red to blue on {server} at playercount {len(teamblue) + len(teamred)} ratio {len(teamblue)}/{len(teamred)} ")
    #                    if poll_config.get("autobalance_testing"):
    #                        logging.info(f"Just testing")
    #                        pass
    #                    else:
    #                        data = await exec_server_command(ctx, server, f"SwitchTeam {switcher} 0")
    #        except:
    #            logging.info(f"exiting autobalance")
    #            pass
    #        embed = discord.Embed(title=f"Autobalanced `{server}`")
    #        await channel.send(embed=embed)
    #    else:
    #        logging.info(f"Exiting autobalance on tolerence players")


def setup(bot):
    bot.add_cog(Polling(bot))
