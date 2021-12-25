import asyncio
import logging
import random
from typing import Optional

import discord
from discord.ext import commands

from bot.utils import polling, players
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
        polling_type = poll_config.get("type").lower()
        interval = poll_config.get("polling_interval") * 60
        state = None
        while True:
            try:
                await asyncio.sleep(interval)
                logging.info(f"Executing Task {name} on server {server}")
                if polling_type == "player":
                    state = await self.player_polling(poll_config, server, state)
                elif polling_type == "autobalance":
                    await self.autobalance_polling(poll_config, server, name)
            except Exception as e:
                await asyncio.sleep(1)
                logging.info(
                    f"Exception occurred while trying to execute {name} on server {server}! Exception: {e}"
                )

    async def player_polling(
        self,
        poll_config: dict,
        server: str,
        old_state: Optional[str],
    ):
        ctx = None
        channel = self.bot.get_channel(poll_config.get("polling_channel"))
        logging.info(f"Starting poll on {server} with state: {old_state}")
        data, ctx = await exec_server_command(ctx, server, "RefreshList")
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
            return None
        if old_state == new_state:
            logging.info(f"State has not changed.")
            return new_state
        logging.info(f"New state for server is {new_state}")
        embed = discord.Embed(
            title=f"`{server}` has {new_state} population! {player_count} players are on!"
        )
        if poll_config.get("show_scoreboard"):
            players_command = self.bot.all_commands.get("players")
            scoreboard = await players_command(ctx, server)
            embed.description = scoreboard
        await channel.send(p_role, embed=embed)
        return new_state

    async def autobalance_polling(self, poll_config: dict, server: str, poll_name: str):
        channel = self.bot.get_channel(int(poll_config.get("polling_channel")))
        ctx = None
        teamblue, teamred, kdalist, alivelist, scorelist = await players.get_stats(ctx, server)
        for player, score in scorelist.items():
            try:
                score = int(score)
            except ValueError:
                score = 0
            if score < int(poll_config.get("tk_threshold")):
                logging.info(f"Task {poll_name}: TK threshold triggered for {player}")

                tk_action = poll_config.get("tk_action")
                logging.info(f"Task {poll_name}: Performing tk action {tk_action}")

                if tk_action.casefold() == "kick":
                    _, ctx = await exec_server_command(ctx, server, f"Kick {player}")
                    logging.info(
                        f"Player {player} kicked for TK from server {server} at score {score}"
                    )
                elif tk_action.casefold() == "ban":
                    _, ctx = await exec_server_command(ctx, server, f"Ban {player}")
                    logging.info(
                        f"Player {player} banned for TK from server {server} at score {score}"
                    )
                elif tk_action.casefold() == "test":
                    logging.info(
                        f"Player {player} would have been actioned for TK from server {server} at score {score}"
                    )
        blue_count = len(teamblue)
        red_count = len(teamred)
        tolerance = int(poll_config.get("autobalance_tolerance"))
        if tolerance is None or tolerance == 0:
            tolerance = 1
        min_players = int(poll_config.get("autobalance_min_players"))
        logging.info(f"Starting autobalance at {blue_count}/{red_count}")
        while True:
            try:
                if blue_count == red_count:
                    logging.info(f"Exiting autobalance on equal teams")
                    return
                elif (blue_count + red_count) < min_players:
                    logging.info(f"Exiting autobalance, not enough players")
                    return
                elif abs(blue_count - red_count) > tolerance:
                    logging.info(f"Blue:{len(teamblue)} Red: {len(teamred)}")
                    if len(teamblue) > len(teamred):
                        to_switch = random.choice(teamblue)
                        command = f"SwitchTeam {to_switch} 1"
                        logging.info(
                            f"Player {to_switch} moved from blue to red on {server} at player count"
                            f" {blue_count + red_count} ratio {blue_count}/{red_count} "
                        )
                    else:
                        to_switch = random.choice(teamred)
                        command = f"SwitchTeam {to_switch} 0"
                        logging.info(
                            f"Player {to_switch} moved from red to blue on {server} at player count"
                            f" {blue_count + red_count} ratio {blue_count}/{red_count} "
                        )
                    if poll_config.get("autobalance_testing"):
                        logging.info(f"Just testing")
                        return
                    else:
                        _, ctx = await exec_server_command(ctx, server, command)

                    teamblue, teamred, _, _, _ = await players.get_stats(ctx, server)
                    blue_count = len(teamblue)
                    red_count = len(teamred)
            except Exception as ex:
                logging.info(f"Exception occurred, exiting autobalance. ex: {ex}")
                return
            embed = discord.Embed(title=f"Autobalanced `{server}`")
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Polling(bot))
