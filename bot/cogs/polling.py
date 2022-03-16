import asyncio
import logging
import random
from typing import Optional

import discord
from discord.ext import commands

from bot.utils import polling, players
from bot.utils.pavlov import exec_server_command


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
        ctx = None
        while True:
            try:
                await asyncio.sleep(interval)
                logging.info(f"Executing Task {name} on server {server}")
                if polling_type == "player":
                    state, ctx = await self.player_polling(ctx, poll_config, server, state)
                elif polling_type == "autobalance":
                    ctx = await self.autobalance_polling(ctx, poll_config, server, name)
            except Exception as e:
                logging.info(
                    f"Exception occurred while trying to execute {name} on server {server}! Exception: {e}"
                )
                await asyncio.sleep(1)

    async def player_polling(
        self,
        ctx,
        poll_config: dict,
        server: str,
        old_state: Optional[str],
    ):
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

    async def autobalance_polling(self, ctx, poll_config: dict, server: str, poll_name: str):
        channel = self.bot.get_channel(int(poll_config.get("polling_channel")))
        teamblue, teamred, _, _, scoredict, ctx = await players.get_stats(ctx, server)
        for player, score in scoredict.items():
            try:
                score = int(score)

            except ValueError:
                score = 0
            if score < int(poll_config.get("tk_threshold")):
                logging.info(f"Task {poll_name}: TK threshold triggered for {player} on {server}")

                tk_action = poll_config.get("tk_action")
                logging.info(f"Task {poll_name}: Performing tk action {tk_action} on {server}")

                if tk_action.casefold() == "kick":
                    _, ctx = await exec_server_command(ctx, server, f"Kick {player}")
                    logging.info(
                        f"Player {player} kicked for TK from server {server} at score {score}"
                    )
                    embed = discord.Embed(
                        title=f"`TK threshold triggered for {player} on {server} at score {score}. Performing tk action {tk_action}`"
                    )
                    p_role = "<@&" + str(poll_config.get("polling_role")) + ">"
                    await channel.send(p_role, embed=embed)
                    return ctx
                elif tk_action.casefold() == "ban":
                    _, ctx = await exec_server_command(ctx, server, f"Ban {player}")
                    logging.info(
                        f"Player {player} banned for TK from server {server} at score {score}"
                    )
                    embed = discord.Embed(
                        title=f"`TK threshold triggered for {player} on {server} at score {score}. Performing tk action {tk_action}`"
                    )
                    p_role = "<@&" + str(poll_config.get("polling_role")) + ">"
                    await channel.send(p_role, embed=embed)
                    return ctx
                elif tk_action.casefold() == "test":
                    logging.info(
                        f"Player {player} would have been actioned for TK from server {server} at score {score}"
                    )
##        for red_player in teamred:
#            logging.info(f"Red: {red_player}")
#        for blue_player in teamblue:
#            logging.info(f"Blue: {blue_player}")
#        for player, score in scoredict.items():
#            logging.info(f"{player}:{score}")

        scorelist_sorted = sorted(scoredict.items(), key=lambda x: int(x[1]))
#        for player in scorelist_sorted:
#           logging.info(f"{player}")

        playerlist_sorted = [player[0] for player in scorelist_sorted]
#        for player in playerlist_sorted:
#           logging.info(f"{player}")

        blue_count = len(teamblue)
        red_count = len(teamred)
        tolerance = int(poll_config.get("autobalance_tolerance"))
        min_players = int(poll_config.get("autobalance_min_players"))
        logging.info(f"Starting autobalance at {blue_count}/{red_count}")
        while True:
            try:
                if blue_count == red_count:
                    logging.info(f"Exiting autobalance on {server} on equal teams")
                    return ctx
                elif (blue_count + red_count) < min_players:
                    logging.info(f"Exiting autobalance on {server}, not enough players")
                    return ctx
                elif abs(blue_count - red_count) <= tolerance:
                    logging.info(
                        f"Exiting autobalance on {server} Blue:{blue_count} Red: {red_count} within tolerance"
                    )
                    return ctx
                else:
                    logging.info(f"Blue:{blue_count} Red: {red_count} on {server}")
                    if blue_count > red_count:
                        blue_count_int = int(blue_count)
                        logging.info(f"{blue_count_int}")
                        median_number = int(blue_count_int / 2)
#                        logging.info(f"Median: {median_number}")

                        for red_player in teamred:
                            playerlist_sorted.remove(red_player)
                            logging.info(f"Popping reds {red_player}")
                        while median_number > 0:
                            median_pop = playerlist_sorted.pop()
                            median_number -= 1
                            logging.info(f"Pop median: {median_pop}")
                        to_switch = playerlist_sorted.pop()
                        logging.info(f"to_switch: {to_switch}")
                        sw_command = f"SwitchTeam {to_switch} 1"
                        logging.info(
                            f"Player {to_switch} moved from blue to red on {server} at player count"
                            f" {blue_count + red_count} ratio {blue_count}/{red_count} "
                            f"Median number was {median_number}"
                        )
                    else:
                        red_count_int = int(red_count)
                        logging.info(f"{red_count_int}")
                        median_number = int(red_count_int / 2)
#                        logging.info(f"Median: {median_number}")

                        for blue_player in teamblue:
                            playerlist_sorted.remove(blue_player)
                            logging.info(f"Popping blues {blue_player}")
                        while median_number > 0:
                            median_pop = playerlist_sorted.pop()
                            median_number -= 1
                            logging.info(f"Pop median: {median_pop}")
                        to_switch = playerlist_sorted.pop()
                        logging.info(f"to_switch: {to_switch}")
                        sw_command = f"SwitchTeam {to_switch} 0"
                        logging.info(
                            f"Player {to_switch} moved from red to blue on {server} at player count"
                            f" {blue_count + red_count} ratio {blue_count}/{red_count} "
                            f"Median number was {median_number}"
                        )
                if poll_config.get("autobalance_testing"):
                    logging.info(f"Just testing {sw_command}")
                    return ctx
                else:
                    logging.info(f"Executed {sw_command}")
                    _, ctx = await exec_server_command(ctx, server, sw_command)
                    embed = discord.Embed(
                        title=f"`Autobalance of {server} at player count {blue_count + red_count} ratio {blue_count}/{red_count}. Median player moved `"
                    )
                    p_role = "<@&" + str(poll_config.get("polling_role")) + ">"
                    await channel.send(p_role, embed=embed)
                    return ctx
            except Exception as ex:
                logging.info(f"Exception occurred, exiting autobalance. ex: {ex}")
                return ctx


def setup(bot):
    bot.add_cog(Polling(bot))
