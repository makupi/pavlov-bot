import asyncio
from typing import Iterable

import discord

LEFT_EMOJI = "\u2B05"
RIGHT_EMOJI = "\u27A1"
FIRST_EMOJI = "\u23EE"
LAST_EMOJI = "\u23ED"
DELETE_EMOJI = "\u274c"

PAGINATION_EMOJI = [FIRST_EMOJI, LEFT_EMOJI, RIGHT_EMOJI, LAST_EMOJI, DELETE_EMOJI]


class PageFull(Exception):
    pass


class Page:
    def __init__(self, prefix: str, suffix: str, max_lines: int):
        self.messages = list()
        self.prefix = prefix
        self.suffix = suffix
        self.max_lines = max_lines

    def is_full(self):
        if len(self.messages) >= self.max_lines:
            return True
        return False

    def add_line(self, line: str):
        if self.is_full():
            raise PageFull
        self.messages.append(line)

    def __repr__(self):
        messages = "\n".join(self.messages)
        return f"{self.prefix}\n{messages}\n{self.suffix}"


class Paginator:
    def __init__(self, prefix: str = "```", suffix: str = "```", max_lines: int = 15):
        self.prefix = prefix
        self.suffix = suffix
        self.max_lines = max_lines
        self.index = 0
        self.pages = list()

    def _new_page(self, line: str):
        page = Page(self.prefix, self.suffix, self.max_lines)
        page.add_line(line)
        self.pages.append(page)

    def _get_current_page(self):
        try:
            return self.pages[self.index]
        except IndexError:
            self.index = 0
            return self.pages[self.index]

    def _next_page(self):
        self.index += 1
        if self.index >= len(self.pages):
            self._last_page()

    def _previous_page(self):
        self.index -= 1
        if self.index < 0:
            self._first_page()

    def _first_page(self):
        self.index = 0

    def _last_page(self):
        self.index = len(self.pages) - 1

    def _get_page_index(self) -> str:
        if len(self.pages) > 1:
            return f" (Page {self.index+1}/{len(self.pages)})"
        return ""

    def _edit_embed(self, embed: discord.Embed, footer_text: str):
        page = self._get_current_page()
        embed.description = str(page)
        embed.set_footer(text=f"{footer_text}{self._get_page_index()}")
        return embed

    def add_line(self, line: str):
        if len(self.pages) == 0:
            self._new_page(line)
        else:
            page = self.pages[-1]
            try:
                page.add_line(line)
            except PageFull:
                self._new_page(line)

    def add_lines(self, lines: Iterable[str]):
        for line in lines:
            self.add_line(line)

    async def create(
        self,
        ctx,
        embed: discord.Embed = None,
        timeout: int = 300,
        footer_text: str = "",
    ):
        ctx.bot.loop.create_task(self._create(ctx, embed, timeout, footer_text))

    async def _create(
        self,
        ctx,
        embed: discord.Embed,
        timeout: int,
        footer_text: str,
    ):
        if embed is None:
            embed = discord.Embed()

        def check(reaction_, user_):
            return (
                not user_.bot
                and reaction_.emoji in PAGINATION_EMOJI
                and reaction_.message.id == message.id
            )

        embed = self._edit_embed(embed, footer_text)
        message = await ctx.send(embed=embed)
        if len(self.pages) == 1:
            return  # no need for pagination if we only have one page
        for emoji in PAGINATION_EMOJI:
            await message.add_reaction(emoji)

        while True:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add", timeout=timeout, check=check
                )
            except asyncio.TimeoutError:
                break

            if reaction.emoji == DELETE_EMOJI:
                break

            if reaction.emoji == FIRST_EMOJI:
                self._first_page()
            elif reaction.emoji == LAST_EMOJI:
                self._last_page()
            elif reaction.emoji == LEFT_EMOJI:
                self._previous_page()
            elif reaction.emoji == RIGHT_EMOJI:
                self._next_page()

            await message.remove_reaction(reaction.emoji, user)
            embed = self._edit_embed(embed, footer_text)
            await message.edit(embed=embed)
        await message.clear_reactions()
