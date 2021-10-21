from bot.utils.pavlov import exec_server_command
import asyncio
import discord


async def exec_command_all_players(ctx, server_name: str, command: str):
    players = await exec_server_command(ctx, server_name, "RefreshList")
    player_list = players.get("PlayerList")
    dataresults = []
    if len(player_list) == 0:
        return "NoPlayers"
    else:
        for player in player_list:
            await asyncio.sleep(0.1)
            data = await exec_server_command(
                ctx, server_name, command.replace(" all ", " " + player.get("UniqueId") + " ")
            )
            dataresults.append(data)
    return dataresults


async def exec_command_all_players_on_team(ctx, server_name: str, team_id: str, command: str):
    players = await exec_server_command(ctx, server_name, "RefreshList")
    player_list = players.get("PlayerList")
    dataresults = []
    if len(player_list) == 0:
        return "NoPlayers"
    else:
        team_id = team_id.replace("team", "")
        if team_id.casefold() == "blue":
            team_id = "0"
        elif team_id.casefold() == "red":
            team_id = "1"
        if (team_id.isnumeric()) == False:
            return "NotValidTeam"
        for player in player_list:
            data = await exec_server_command(
                ctx, server_name, f"InspectPlayer {player.get('UniqueId')}"
            )
            player_team = data.get("PlayerInfo").get("TeamId")
            await asyncio.sleep(0.1)
            if player_team == team_id:
                data2 = await exec_server_command(
                    ctx, server_name, command.replace(" team ", " " + player.get("UniqueId") + " ")
                )
                dataresults.append(data2)
    return dataresults


async def parse_player_command_results(ctx, data, embed, server_name):
    success = 0
    failure = 0
    if data == "NoPlayers":
        embed = discord.Embed(title=f"No players on {server_name}")
        return embed
    elif data == "NotValidTeam":
        embed = discord.Embed(
            title=f"**Invalid team. Must be number team0/team1 or teamblue/teamred**\n"
        )
        return embed
    elif type(data) == dict:
        result = data.get("Successful")
        if result == True:
            result = "✅"
            success += 1
        elif result == False:
            result = "❎"
            failure += 1
        embed.add_field(name=data.get("UniqueID"), value=result, inline=False)
        embed.description = f"{success} out of {success + failure} players affected"
    else:
        for i in data:
            result = i.get("Successful")
            if result == True:
                result = "✅"
                success += 1
            elif result == False:
                result = "❎"
                failure += 1
            embed.add_field(name=i.get("UniqueID"), value=result, inline=False)
        embed.description = f"{success} out of {success + failure} players affected"
    return embed
