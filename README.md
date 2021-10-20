# pavlov-bot
Discord bot to inferface with Pavlov VR RCON


# Setup
*This setup guide assumes you are running Ubuntu 18.04 or later. Later versions may already have required python3.8 version. It also assumes you are running the bot on the same server running pavlovserver following setup guide found [here](http://wiki.pavlov-vr.com/index.php?title=Dedicated_server).*

## Prerequisites
- pip3    
- python3.8    
- pipenv

## Installing pip3
`sudo apt install python3-pip`

## Installing python3.8 (required for Ubuntu prior to 20.04)
Get your system up to date and install some prerequisites 
```
sudo apt update
sudo apt upgrade
sudo apt install software-properties-common
```

Install PPA for Python3.8 by adding the deadsnakes PPA to your system’s sources list:

```
sudo add-apt-repository ppa:deadsnakes/ppa
```
When prompted press Enter to continue

Once the repository is enabled, install Python 3.8 with:

```
sudo apt install python3.8
```

Verify that the installation was successful by typing:
```
python3.8 --version
```

## Getting pavlov-bot code from github and creating config files
*Log in as steam user (or whatever user will run bot. This assumes steam user used for pavlovserver as documented [here](http://wiki.pavlov-vr.com/index.php?title=Dedicated_server)) and run following commands*


```
su - steam 

cd ~ && git clone https://github.com/makupi/pavlov-bot
```
Copy file config.json.default file from Examples directory to `/home/steam/pavlov-bot/config.json` with following single line:
```json
{"prefix": ";", "token": "replacemewithdiscordtoken"}
```

Copy servers.json.default file from Examples directory to `/home/steam/pavlov-bot/servers.json` and edit as required for your servers. Admins in servers.json are discordIDs of the admin users ([how to find user-ids](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-)) and IP, port are as required to get to the rcon severs and password is the unhashed password setup in RconSettings.txt.

Note that server names are processed case insensitive, so server named "Rush" can be called by `;serverinfo rush` or `;serverinfo RUSH` 

If you only have one server, if you name it `default` in servers.json and you can skip defining a server in all commands that require one as `default` will be used automatically. This default name can be changed in `config.json` 

*Optional but recommended*: Copy aliases.json.default file from Examples directory to `/home/steam/pavlov-bot/aliases.json` and edit as required for your servers. Maps and players can be called using either UGC### for maps or SteamID/EOSID or aliases defined in this file using these ID formats. Teams are setup as arrays of SteamIDs/EOSIDs for use with ;matchsetup command. Team aliases are required to used ``;matchsetup`` command.    

*Optional advanced feature*: Copy commands.json.default file from Examples directory to `/home/steam/pavlov-bot/commands.json` and edit as required. By default, all commands require Admin permission unless the "permission" field contains "All", "Captain" or "Mod" which grants execution rights to that level and higher.  Note that all commands will be run as the steam user. If you want to allow commands to call scripts requiring root permission, you will need to configure sudo to allow this. 

## Setup your bot with discord
Follow instructions [here](https://discordpy.readthedocs.io/en/latest/discord.html#).    
Obtain the bot token and install in config.json

## Installing pipenv
As root user run the following command    
`pip3 install pipenv`

## Setup of pipenv for pavlov-bot
login as steam user    
`cd ~/pavlov-bot && pipenv install`

## Test startup of bot
As steam user run the following command    
`cd ~/pavlov-bot && /usr/local/bin/pipenv run python3.8 run.py`

Go to your discord channel that the bot has been invited to and allowed to read and write to and try a few commands to test. Suggest ``;help`` and ``;info`` as good starters, then ``;servers`` to see if your server.json was read correctly. 

## Make bot run as a systemd service
As root create `/etc/systemd/system/pavlov-bot.service` file with following config:

```ini
[Unit]
Description=Pavlov-bot

[Service]
Type=simple
WorkingDirectory=/home/steam/pavlov-bot
ExecStart=/usr/local/bin/pipenv run python3.8 run.py
RestartSec=1
Restart=always
User=steam
Group=steam

[Install]
WantedBy = multi-user.target
```

As root run following commands:
```
systemctl enable pavlov-bot
systemctl start pavlov-bot
```

Test bot... if all is good, then bot will start with server boot and restart if crashes occur. 

Follow the logs with:    
`journalctl -n 20 -f -u pavlov-bot`

## Updating codebase
pavlov-bot is in active developement and new features will need to be checked out of the 'master' branch which we will try and keep stable. 

To update from master as steam user:

``cd /home/steam/pavlov-bot`` (or wherever you have installed)

``git pull``

``pipenv sync``

Then restart your bot to run version with recent changes. If following this guide:

``systemctl restart pavlov-bot``


# Roles and permissions
The bot has 4 permission levels:
* Everyone (can run ;servers, ;serverinfo, ;players, ;playersinfo ;batch)
* Captain (can run Everyone commands plus ;switchmap, ;resetsnd, ;switchteam, ;rotatemap)
* Mod (can run Captain commands plus ;ban, ;unban, ;kick)
* Admin (can do everything)

## Administration of permissions
* Admins are defined in servers.json all other groups are configured using discord roles. 
* Roles need to be setup in discord using the following format {role name}-{server} where Role names are (Mod,Captain,Banned) and server is as returned by ;server command. Eg: Mod-testserver or Captain-rush
* There is a set of "super" roles defined that allow Captain or Mod permissions for all servers controlled by the bot. These are granted by membership to the discord roles of "Captain-bot" and "Mod-bot"


## Advanced bot functions
In addition to the implemented RCON commands, the bot has a few advanced functions:
* Aliases as defined in aliases.json file allow UGC###/SteamID for maps and players to be called with easy to remember aliases. ``;aliases`` will list player and map aliases defined. ``;teams`` will list teams defined with ``;teams <teamname>`` providing list of players
* Team managment commands (``;ringer add, ;ringer delete, ;ringer reset``) allow dynamic addition of temporary players to teams defined in aliases.json. ``;teamsetup`` allows for quick creation of ad-hoc teams using an empty team name defined in aliases.json
* ``;matchsetup <CT Team> <T Team> <server>`` using the teams setup in aliases.json and with team management commands will push players to the correct teams in game, pause 10 seconds then issue ResetSND
 * ``;anyoneplaying`` will give a summary report of all servers controlled by the bot
 * ``;custom "<command string>" <server>`` will pass the command string along to RCON and presents back whatever data is returned (if any). This is useful for maps with rcon interfaces
* If you have a server called "default", you can omit the server name from commands. To set a different default server name, set `server_name` key in config.json
* ``;flush <server>`` will randomly pick a player who isn't in aliases.json and kick them from the server to make room for a registered player. 
* ``;command <command_name>`` will allow you to execute pre-defined commandline commands in commands.json on the local server running the bot. Useful for automation of things like starting and stopping pavlovserver instances or clearing disk space on server full of maps. 
* ``;repeat <full pavlov-bot command> <number>`` will issue the requested pavlov-bot command requested number of times up to 100. Useful for making a pile of nades or something. 
* Command shorthands: ;switchmap can be shortened to ;map and ;rotatemap can be shortened to ;next
* ;switchmap command can accept either map aliases, UGC### or full URLs from workshop like "https://steamcommunity.com/sharedfiles/filedetails/?id=1664873782"
* A set of commands which can apply to an individual player, a team or all players: ``;giveitem``, ``;slap``, ``;kill``, ``;switchplayerskins`` and ``;givecash``. These can take either an alias/steamID/q-questname, the keyword "all" or the keywords "teamblue/teamred/team0/team1" to apply command to an individual player, all players, or players on a team. 

## Quest IDs and maps 

Since quest IDs and maps are handled as strings we cannot easily distinguish them from aliases.    
Therefore, if you want to do a player action (ban, kick, giveitem, etc) for players *who aren't in aliases.json* then Quest IDs have to be entered with a `q-` prefix.
For example, you want to ban player "annoying" who isn't in your aliases file ``;ban q-annoying <server>`` but if you want to give cash to player "dude" who is in your aliases.json file ``;givecash 1000 dude <server>`` 

**IMPORTANT**: Do not use the `q-` in the aliases file!  QuestIDs in aliases file need to be quoted (e.g. ``"nickalready": "nickalready",``)

Quest maps need to be entered into the aliases.json file for them to work at all. Can either be a 1 to 1 (eg ``"mapname": "mapname",``) or might as well make a short alias (``"shortname": "mapname",``). 

# Known issues with Rcon that bot can't fix
* When a SwitchMap Rcon command is issued, the server always returns true no matter what map (or no valid map at all) was requested. No way to know if the request was valid or not or what will happen. Could be nothing, could be datacenter. It is a mystery. 
* After a ResetSND command is issued to pavlovserver the very first round can release the players before the countdown is complete. Also on occasion there have been noted CT/T side switches prior to round 9. Both bugs are documented here (https://discord.com/channels/267301605882200065/577875229599072266/729124885141389382).
* Issuing a ``ResetSND`` command to RCON very quickly after a ``SwitchTeam`` command can result in oddities like extra death count in scoreboard or weapons or SND bomb not getting removed from player. 
