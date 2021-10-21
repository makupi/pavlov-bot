import logging

import discord

from bot.utils import servers, user_action_log
from pavlov import PavlovRCON

RCON_TIMEOUT = 5


MODERATOR_ROLE = "Mod-{}"
CAPTAIN_ROLE = "Captain-{}"

SUPER_MODERATOR = ["Mod-bot"]
SUPER_CAPTAIN = ["Captain-bot"]


async def check_banned(ctx):
    pass


async def check_perm_admin(
    ctx, server_name: str = None, sub_check: bool = False, global_check: bool = False
):
    """ Admin permissions are stored per server in the servers.json """
    if not server_name and not global_check:
        return False
    _servers = list()
    if server_name:
        _servers.append(servers.get(server_name))
    elif global_check:
        _servers = servers.get_servers().values()
    for server in _servers:
        if ctx.author.id in server.get("admins", []):
            return True
    if not sub_check:
        user_action_log(
            ctx,
            f"ADMIN CHECK FAILED server={server_name}, global_check={global_check}",
            log_level=logging.WARNING,
        )
        if not ctx.batch_exec:
            await ctx.send(embed=discord.Embed(description=f"This command is only for Admins."))
    return False


def check_has_any_role(
    ctx,
    super_roles: list,
    role_format: str,
    server_name: str = None,
    global_check: bool = True,
):
    for super_role in super_roles:
        super_role = discord.utils.get(ctx.author.roles, name=super_role)
        if super_role is not None:
            return True

    role_names = list()
    if global_check:
        for server_name in servers.get_names():
            role_names.append(role_format.format(server_name))
    elif server_name:
        role_names.append(role_format.format(server_name))

    for role_name in role_names:
        r = discord.utils.get(ctx.author.roles, name=role_name)
        if r is not None:
            return True
    return False


async def check_perm_moderator(
    ctx, server_name: str = None, sub_check: bool = False, global_check: bool = False
):
    if await check_perm_admin(ctx, server_name, sub_check=True, global_check=global_check):
        return True
    if not check_has_any_role(ctx, SUPER_MODERATOR, MODERATOR_ROLE, server_name, global_check):
        if not sub_check:
            user_action_log(
                ctx,
                f"MOD CHECK FAILED server={server_name}, global_check={global_check}",
                log_level=logging.WARNING,
            )
            if not ctx.batch_exec:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"This command is only for Moderators and above."
                    )
                )
        return False
    return True


async def check_perm_captain(ctx, server_name: str = None, global_check: bool = False):
    if await check_perm_moderator(ctx, server_name, sub_check=True, global_check=global_check):
        return True
    if not check_has_any_role(ctx, SUPER_CAPTAIN, CAPTAIN_ROLE, server_name, global_check):
        user_action_log(
            ctx,
            f"CAPTAIN CHECK FAILED server={server_name} global_check={global_check}",
            log_level=logging.WARNING,
        )
        if not ctx.batch_exec:
            await ctx.send(
                embed=discord.Embed(description=f"This command is only for Captains and above.")
            )
        return False
    return True


async def exec_server_command(ctx, server_name: str, command: str):
    pavlov = None
    if hasattr(ctx, "pavlov"):
        pavlov = ctx.pavlov.get(server_name)
    if not hasattr(ctx, "pavlov") or pavlov is None:
        server = servers.get(server_name)
        pavlov = PavlovRCON(
            server.get("ip"),
            server.get("port"),
            server.get("password"),
            timeout=RCON_TIMEOUT,
        )
        if not hasattr(ctx, "pavlov"):
            ctx.pavlov = {server_name: pavlov}
        else:
            ctx.pavlov[server_name] = pavlov
    data = await pavlov.send(command)
    return data
