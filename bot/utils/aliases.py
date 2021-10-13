import json
import os
import re
from typing import List, Tuple

import urllib.parse as urlparse
from urllib.parse import parse_qs

from bot.utils.steamplayer import SteamPlayer

DEFAULT_FORMAT = {"maps": {}, "players": {}, "teams": {}}
MAP_NAME_REGEX = r"UGC[0-9]*"
WORKSHOP_URL = "https://steamcommunity.com/sharedfiles/filedetails/"
STRING_ID_CHARACTER_LENGTH = 16


def check_map_already_label(name):
    if re.match(MAP_NAME_REGEX, name):
        return True
    return False


def check_player_already_id(name) -> Tuple[bool, str]:
    try:
        int(name)
        return True, name
    except ValueError:
        if name.lower().startswith("q-"):
            # special exception for Quest IDs, have to start with q- since they are strings
            return True, name[2:]
        elif len(name) >= STRING_ID_CHARACTER_LENGTH:
            if int(name, 16):  # check if hexadecimal
                return True, name
    return False, name


class Team:
    def __init__(self, name: str, members: List[SteamPlayer]):
        self.name = name
        self._original_members = members
        self._ringers = list()

    @property
    def members(self):
        return self._original_members + self._ringers

    def ringer_add(self, ringer: SteamPlayer):
        self._ringers.append(ringer)

    def ringers_reset(self):
        self._ringers = list()

    def ringer_delete(self, ringer: SteamPlayer):
        for r in self._ringers:
            if r.unique_id == ringer.unique_id:
                self._ringers.remove(r)

    def __repr__(self):
        return self.member_repr()

    def member_repr(self):
        s = f"original members:```\n"
        for member in self._original_members:
            s += f" - {f'{member.name}' if member.has_alias else ''} <{member.unique_id}>\n"
        if self._ringers:
            s += "```ringers:```\n"
            for member in self._ringers:
                s += f" - {f'{member.name}' if member.has_alias else ''} <{member.unique_id}>\n"
        s += "```"
        return s


class AliasNotFoundError(Exception):
    def __init__(self, alias_type: str, alias: str):
        self.alias_type = alias_type
        self.alias = alias


class Aliases:
    def __init__(self, filename="aliases.json"):
        self._filename = filename
        self._aliases = {}
        self.AliasNotFoundError = AliasNotFoundError
        if not os.path.isfile(filename):
            with open(filename, "w") as file:
                json.dump(DEFAULT_FORMAT, file)
        with open(filename) as file:
            data = json.load(file)
            self._aliases = data
        self.teams = None

    def get(self, alias_type: str, name: str):
        data = self._aliases.get(alias_type, {})
        alias = data.get(name)
        if alias is None:
            for key in data.keys():
                if key.lower() == name.lower():
                    alias = data.get(key)
                    break
            else:
                raise AliasNotFoundError(alias_type, name)
        return alias

    def load_teams(self):
        _teams = self._aliases.get("teams", {})
        teams = {}
        for team_name, members in _teams.items():
            steam_members = list()
            for member in members:
                steam_members.append(SteamPlayer.convert(member))
            team = Team(name=team_name, members=steam_members)
            teams[team_name] = team
        self.teams = teams

    def get_map(self, name: str):
        if name.startswith(WORKSHOP_URL):
            parsed_url = urlparse.urlparse(name)
            try:
                id = parse_qs(parsed_url.query)['id'][0]
                return f"UGC{id}"
            except KeyError:
                raise AliasNotFoundError("maps", name)
            jid = parse_qs(parsed_url.query)['id'][0]
            return f"UGC{id}"
        if check_map_already_label(name):
            return name
        return self.get("maps", name)

    def get_player(self, name: str):
        is_id, name = check_player_already_id(name)
        if is_id:
            return name
        return self.get("players", name)

    def get_team(self, name: str):
        team = self.teams.get(name)
        if team is None:
            for team_name, t in self.teams.items():
                if name.lower() == team_name.lower():
                    team = t
                    break
            else:
                raise AliasNotFoundError("teams", name)
        return team

    def find_alias(self, alias_type: str, search: str):
        data = self._aliases.get(alias_type, {})
        for alias, label in data.items():
            if str(label) == str(search):
                return alias

    def find_map_alias(self, map_label: str):
        return self.find_alias("maps", map_label)

    def find_player_alias(self, unique_id: str):
        return self.find_alias("players", unique_id)

    def get_maps(self):
        return self._aliases.get("maps", {})

    def get_players(self):
        return self._aliases.get("players", {})

    def get_teams_list(self):
        return self.teams.values()
