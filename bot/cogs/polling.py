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
                try:
                    state = await self.player_polling(pollings, server, poll, state)
                except:
                    state = await self.player_polling(pollings, server, poll, 0)
            if pollings.get("type") == "autobalance":
                interval = float(pollings.get("polling_interval")) * 60
                await asyncio.sleep(interval)
                logging.info(f"Executing Task {poll} on server {server}")
                await self.autobalance_polling(pollings, server, poll)

    async def player_polling(self, pollings, server, poll: str, old_state: int):
        channel = self.bot.get_channel(int(pollings.get("polling_channel")))
        ctx = ""
        data = await exec_server_command(ctx, server, "RefreshList")
        new_state = len(data.get("PlayerList"))
        if old_state == new_state:
            # embed = discord.Embed(title=f"`{server}` has not gained/lost players. {new_state} players are on!")
            # await channel.send(embed=embed)
            return new_state
        else:
            if new_state == 1:
                are_is = "is"
                player_players = "player"
            else:
                are_is = "are"
                player_players = "players"
            if old_state - new_state == 1:
                player_players2 = "player"
            else:
                player_players2 = "players"
            if old_state > new_state:
                embed = discord.Embed(
                    title=f"`{server}` lost {old_state - new_state} {player_players2}! {new_state} {player_players} {are_is} on!"
                )
                await channel.send("<@&" + pollings.get("polling_role") + ">", embed=embed)
                return new_state
            elif old_state < new_state:
                embed = discord.Embed(
                    title=f"`{server}` gained {new_state - old_state} new {player_players2}! {new_state} {player_players} {are_is} on!"
                )
                await channel.send("<@&" + pollings.get("polling_role") + ">", embed=embed)
                return new_state

    async def autobalance_polling(self, pollings, server, poll: str):
        channel = self.bot.get_channel(int(pollings.get("polling_channel")))
        ctx = ""
        teamblue, teamred = await get_teams(server)
        kdalist = await get_kda(server)
        for k, v in kdalist.items():
            kda = v.split("/")
            if int(kda[2]) > int(pollings.get("tk_threshold")):
                logging.info(f"Task {poll}: TK threshold triggered for {k}")
                logging.info(f"Task {poll}: Peforming tk action {pollings.get('tk_action')}")
                if pollings.get("tk_action").casefold() == "kick":
                    await exec_server_command(ctx, server, f"Kick {k}")
                elif pollings.get("tk_action").casefold() == "ban":
                    await exec_server_command(ctx, server, f"Ban {k}")
                elif pollings.get("tk_action").casefold() == "test":
                    pass
        if len(teamblue) == len(teamred):
            pass
        elif len(teamred) - 1 == len(teamblue) and len(teamred) == len(teamblue) + 1:
            pass
        elif int(pollings.get("autobalance_min_players")) > len(teamblue) + len(teamred):
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
