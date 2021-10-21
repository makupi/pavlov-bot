import logging
import sys
import time
from datetime import datetime

import discord
from discord.ext import commands

PY_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now().replace(microsecond=0)

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    @commands.command()
    async def ping(self, ctx):
        """`{prefix}ping` - *Current ping and latency of the bot*"""
        embed = discord.Embed()
        before_time = time.time()
        msg = await ctx.send(embed=embed)
        latency = round(self.bot.latency * 1000)
        elapsed_ms = round((time.time() - before_time) * 1000) - latency
        embed.add_field(name="ping", value=f"{elapsed_ms}ms")
        embed.add_field(name="latency", value=f"{latency}ms")
        await msg.edit(embed=embed)

    @commands.command()
    async def uptime(self, ctx):
        """`{prefix}uptime` - *Current uptime of the bot*"""
        current_time = datetime.now().replace(microsecond=0)
        embed = discord.Embed(
            description=f"Time since I went online: {current_time - self.start_time}."
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def starttime(self, ctx):
        """`{prefix}starttime` - *Start time of the bot*"""
        embed = discord.Embed(description=f"I'm up since {self.start_time}.")
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx):
        """`{prefix}info` - *Shows software versions and status of the bot*"""
        embed = discord.Embed(title="Pavlov-Bot")
        # embed.url = f"https://top.gg/bot/{self.bot.user.id}"
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(
            name="Bot Stats",
            value=f"```py\n"
            f"Guilds: {len(self.bot.guilds)}\n"
            f"Users: {len(self.bot.users)}\n"
            f"Shards: {self.bot.shard_count}\n"
            f"Shard ID: {ctx.guild.shard_id}```",
            inline=False,
        )
        embed.add_field(
            name="Software Versions",
            value=f"```py\n"
            f"Pavlov-Bot: {self.bot.version}\n"
            f"discord.py: {discord.__version__}\n"
            f"Python: {PY_VERSION}```",
            inline=False,
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
