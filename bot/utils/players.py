from bot.utils.pavlov import exec_server_command
import asyncio 

async def exec_command_all_players(ctx, server_name: str, command: str):
    players = await exec_server_command(ctx, server_name, "RefreshList")
    player_list = players.get("PlayerList")
    dataresults = []
    if len(player_list) == 0:
        return "NoPlayers"
    else:
        for player in player_list:
            await asyncio.sleep(0.2)
            data = await exec_server_command(
                        ctx, server_name, command.replace(" all ", " " + player.get('UniqueId') + " ")
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
        team_id = team_id.replace('team', '')
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
            await asyncio.sleep(0.2)
            if player_team == team_id:
                data2 = await exec_server_command(
                        ctx, server_name, command.replace(" team ", " " + player.get('UniqueId') + " ")
                    )
                dataresults.append(data2)
    return dataresults
