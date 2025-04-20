import discord

from bot.utils.pavlov import exec_server_command


async def exec_command_all_players(server_name: str, command: str):
    players = await exec_server_command(server_name, "RefreshList")
    player_list = players[0].get("PlayerList")
    result = list()
    if len(player_list) == 0:
        return "NoPlayers"
    else:
        for player in player_list:
            if player.get("UniqueId") == '' or player.get('Username') == '':
                continue
            data, _ = await exec_server_command(
                server_name,
                command.replace(" all ", " " + player.get("UniqueId") + " "),
            )
            result.append(data)
    return result


async def exec_command_all_players_on_team(server_name: str, team_id: str, command: str):
    players = await exec_server_command(server_name, "RefreshList")
    player_list = players[0].get("PlayerList")
    result = list()
    if len(player_list) == 0:
        return "NoPlayers"
    else:
        team_id = team_id.replace("team", "")
        if team_id.casefold() == "blue":
            team_id = "0"
        elif team_id.casefold() == "red":
            team_id = "1"
        if not team_id.isnumeric():
            return "NotValidTeam"
        for player in player_list:
            if player.get("UniqueId") == '' or player.get('Username') == '':
                continue
            data, _ = await exec_server_command(
                server_name, f"InspectPlayer {player.get('UniqueId')}"
            )
            player_team = data.get("PlayerInfo").get("TeamId")
            if player_team == team_id:
                data2, _ = await exec_server_command(
                    server_name,
                    command.replace(" team ", " " + player.get("UniqueId") + " "),
                )
                result.append(data2)
    return result


async def parse_player_command_results(data, embed, server_name):
    success = 0
    failure = 0
    if data == "NoPlayers":
        embed = discord.Embed(title=f"No players on {server_name}")
        return embed
    elif data == "NotValidTeam":
        embed = discord.Embed(
            title="**Invalid team. Must be number team0/team1 or teamblue/teamred**\n"
        )
        return embed
    elif type(data) == dict:
        result = data.get("Successful")
        if result:
            result = "✅"
            success += 1
        else:
            result = "❎"
            failure += 1
        embed.add_field(name=data.get("UniqueID"), value=result, inline=False)
        embed.description = f"{success} out of {success + failure} players affected"
    else:
        for i in data:
            result = i.get("Successful")
            if result:
                result = "✅"
                success += 1
            else:
                result = "❎"
                failure += 1
            embed.add_field(name=i.get("UniqueID"), value=result, inline=False)
        embed.description = f"{success} out of {success + failure} players affected"
    return embed


async def get_stats(server: str = ""):
    if server == "":
        return "NoServerSpecified"
    else:
        teamblue = []
        teamred = []
        alivelist = {}
        kdalist = {}
        scorelist = {}
        data, ctx = await exec_server_command(server, "RefreshList")
        player_list = data.get("PlayerList")
        for player in player_list:
            if player.get("UniqueId") == '' or player.get('Username') == '':
                continue
            data2, ctx = await exec_server_command(
                server, f"InspectPlayer {player.get('UniqueId')}"
            )
            dead = data2.get("PlayerInfo").get("Dead")
            alivelist.update({player.get("UniqueId"): dead})
            kda = data2.get("PlayerInfo").get("KDA")
            kdalist.update({player.get("UniqueId"): kda})
            score = data2.get("PlayerInfo").get("Score")
            scorelist.update({player.get("UniqueId"): score})
            team_id = data2.get("PlayerInfo").get("TeamId")
            if team_id == "0":
                teamblue.append(player.get("UniqueId"))
            elif team_id == "1":
                teamred.append(player.get("UniqueId"))
        return teamblue, teamred, kdalist, alivelist, scorelist, ctx
