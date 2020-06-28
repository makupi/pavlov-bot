import logging

import discord
from discord.ext import commands

from bot.utils import config

COG_ORDER = ["Pavlov", "PavlovCaptain", "PavlovMod", "PavlovAdmin"]


async def create_bot_help(embed, mapping, prefix=";"):
    for cog, cmds in mapping.items():
        cmd_str = ""
        split_count = 1
        for cmd in cmds:
            if not cmd.hidden:
                tmp_str = f"{cmd.short_doc.format(prefix=prefix)}\n"
                if len(cmd_str) + len(tmp_str) >= 1024:
                    embed.add_field(
                        name=f"**__{cog.qualified_name} {split_count}__**",
                        value=cmd_str,
                        inline=False,
                    )
                    split_count += 1
                    cmd_str = ""
                cmd_str += f"{cmd.short_doc.format(prefix=prefix)}\n"
        if cmd_str:
            name = f"**__{cog.qualified_name}__**"
            if split_count > 1:
                name = f"**__{cog.qualified_name} {split_count}__**"
            embed.add_field(name=name, value=cmd_str, inline=False)
    return embed


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"{type(self).__name__} Cog ready.")

    def ordered_cogs(self):
        cogs = self.bot.cogs
        ordered = list()
        for cog_name in COG_ORDER:
            if cog_name in cogs:
                ordered.append(cogs.get(cog_name))
        for k, v in cogs.items():
            if k not in COG_ORDER:
                ordered.append(v)
        return ordered

    def get_bot_mapping(self):
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""
        cogs = self.ordered_cogs()
        mapping = {cog: list(cog.walk_commands()) for cog in cogs}
        # mapping[None] = [c for c in bot.all_commands.values() if c.cog is None]
        return mapping

    @commands.command(hidden=True)
    async def help(self, ctx, command_name: str = None):
        """Shows this help message"""
        prefix = config.prefix
        embed = discord.Embed(
            title="Help",
            description=f"*Use `{prefix}help <command-name>` to get a more detailed help for a specific command!*\n",
        )
        if command_name is not None:
            cmd = ctx.bot.all_commands.get(command_name)
            if cmd is not None:
                embed.add_field(name=cmd.name, value=cmd.help.format(prefix=prefix))
                return await ctx.send(embed=embed)
        embed = await create_bot_help(embed, self.get_bot_mapping(), prefix)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
