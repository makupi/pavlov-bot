import asyncio
import json
import os

from bot.utils.pavlov import check_perm_admin, check_perm_captain, check_perm_moderator

PERMISSIONS = {
    "any": None,
    "all": None,
    "captain": check_perm_captain,
    "mod": check_perm_moderator,
    "moderator": check_perm_moderator,
    "admin": check_perm_admin,
}

DEFAULT_FORMAT = {}


class NotFoundError(Exception):
    def __init__(self, command_name: str):
        self.command_name = command_name


class InvalidCommand(Exception):
    def __init__(self, command_name: str):
        self.command_name = command_name


class Command:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.command = data.get("command")
        if self.command is None:
            raise InvalidCommand(self.name)
        self.permission = data.get("permission", "admin")
        self._perm_check = check_perm_admin
        if self.permission.lower() in PERMISSIONS:
            self._perm_check = PERMISSIONS.get(self.permission.lower())

    async def __call__(self, ctx):
        if self._perm_check:
            if not await self._perm_check(ctx, server_name=None, global_check=True):
                return

        proc = await self._get_process()
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            if stdout:
                await ctx.send(f"**stdout**\n```{stdout.decode()}```")
            if stderr:
                await ctx.send(f"**stderr**\n```{stderr.decode()}```")
        except asyncio.TimeoutError:
            pass

    async def _get_process(self) -> asyncio.subprocess.Process:
        return await asyncio.create_subprocess_shell(
            self.command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )


class Commands:
    NotFoundError = NotFoundError

    def __init__(self, filename="commands.json"):
        self._filename = filename
        self._commands = {}
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump(DEFAULT_FORMAT, file)
        with open(filename) as file:
            data = json.load(file)
            self._commands = data

    def _find_command(self, command_name: str) -> dict:
        if command_name not in self._commands:
            for name in self._commands.keys():
                if name.lower() == command_name.lower():
                    command_name = name
                    break
        return self._commands.get(command_name)

    def get(self, command_name: str):
        command = self._find_command(command_name)
        return Command(name=command_name, data=command)
