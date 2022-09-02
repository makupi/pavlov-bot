# Changelog

##v0.7.3 - 2022-09-03
- Locked Discord.py on 1.7.3 and discord-components to archived version
- Add privileged message intent to bot instance

##v0.7.2 - 2022-03-16
- Tweaked autobalance so that instead of randomly picking a player it always picks the player with median score. Prevents very skilled or very not skilled players from being move, neither of which balance the game well
- Added `;checkban` command to look for an ID in the banlist instead of having to do it manually


## v0.7.1 - 2022-02-06
- Autobalance: Designed primarly for PUSH servers, this feature monitors the scoreboard for team killers and kicks or bans at your tolerance limit. Watches player count for the two teams and when enough players are present and the teams are unbalanced, forces players from high count team to low to keep games numerically balanced.
- Added `;gamesetup` command that will spawn menu buttons in discord allowing control of an SND match using Discord buttons from within VR.
- Added `;menu` command to spawn admin menu with Discord buttons for use with virtual desktop in VR 
- Improved formatting of `;players` command scoreboard
- Lengthened pause before ResetSND on `;matchsetup` to 10 seconds from 5 seconds
- Added `;ringers populate {team} {server}` for setting up pubstomps against randos
- Added TTT related commands:
  - `;tttsetkarma <player_id/all/team> <karma_amount> <server_name>`
  
  - `;tttflushkarma <player_id/all/team> <server_name>`
  
  - `;tttendround server_name`
  - `;tttpausetimer pause/unpause/true/false server_name`
  - `;tttalwaysenableskinmenu enable/disable/true/false server_name`
- Added `;nametags enable/disable/true/false server_name` command to turn off nametags for vod recording
- Added "all" option to ban to ban player on all managed servers. `;ban 1234 all`

## v0.6.1 - 2021-11-?
- Improved performance of `;players` command
- Improved output of `;players` command to give player stats and game score
- Created the start of a polling system that continually runs commands against servers. First use case is a polling system that can send messages to discord channels when a server is filling up or emptying out
- Shortened pause before ResetSND on `;matchsetup` to 5 seconds from 10 seconds

## v0.5.1 - 2021-10-21
- Fixed Blacklist command changing to Banlist
- Removed "all" commands and made following commands accept either a UserID or keywords ``all``, ``teamred/teamblue`` or "team0/team1" with enhanced feedback on which players the command applied to:
	- ;slap
	- ;kill
	- ;giveitem
	- ;setplayerskin
	- ;givecash
- Graphics updates to ;players command
- Added in new player info parsing backend
- 
## v0.5 - 2021-10
- Added support for following new RCON commands
	- SetPin
	- AddMod
	- RemoveMod
	- GiveVehicle
	- Slap
- Added enhanced commands
	- ;slapall - slap to all players
	- ;killall - kill all players
	- ;giveall - give items to all players
	- ;spsall - Set player skin to all players
	- ;slapall - Slap all players
	- ;repeat - Allows repeating a valid pavlov-bot command up to 100 times. Useful for making a pile of nade or something
- Fixed some issues:
	- ;flush command bug hopefully fixed
	- Fixed long Quest/Shack playername issue
- Some QOL updates:
	- ;switchmap can now be called by just ;map as well
	- ;rotatemap can now be called by ;next as well
	- ;switchmap accepts Steamworkshop URLs as direct copy paste. e.g. ;switchmap https://steamcommunity.com/sharedfiles/filedetails/?id=921873447 dm servername will load DustII without having to extract the number and add UGC
- The obligatory fixed some small bugs line to cover things I forgot

## Undocumented lots of changes up to 0.4.2 because I am lazy
- Added `;custom` command with admin permission to execute custom RCON commands
- Added ;flush command, ;teamsetup command, ;ringer delete option and Quest playername support

## v0.2.3 - 2020-06-29
- Pavlov Cog refactored, for more info see PR [#51](https://github.com/makupi/pavlov-bot/pull/51)
- Fixed `;help` properly by splitting pavlov commands into separate categories (Pavlov, PavlovCaptain, PavlovMod, PavlovAdmin)

## v0.2.2 - 2020-06-28
- Fixed aliases character limit issue with pagination for aliases maps and players

## v0.2.1 - 2020-06-25
- Fixed `;help` command exceeding 1024 character field limit temporarily, refactor pending

## v0.2.0 - 2020-06-25
- Introduced `teams` aliases to `aliases.json` file
- Added `;matchsetup <CT team> <T team> <server>` to automatically match up teams defined in `aliases.json`
    - Performs SwitchTeam on every member and then ResetSND after a 10 second delay
    - Requires Captain permission or higher
- Added team related commands
    - `;teaminfo [team name]` with optional team name.
        - Will list either all available teams (without parameter) or all members of a team if given.
    - `;ringers add <unique-id/alias> <team-name>` to add a temporary ringer to a team
    - `;ringers reset <team-name>` removes temporary ringers from team
        - both `;ringers add/reset` require any kind of Captain permission or higher (refer to global-checks below)
   
- Added `;anyoneplaying` command
    - Iterates through all servers and sends Image with current players, map and map alias per server
    - This added `Pillow` package dependency 
- Added "super" moderator and captain roles
    - `Captain-bot` and `Mod-bot` are "super" roles that work for ALL servers
- Added global checks for non-server related commands (e.g. `;ringers`)
    - global checks iterate through all servers and check if the user has any 
    `Captain/Mod-servername` role or if they are admin in any server (including super roles mentioned above)
 - Added new RCON commands 
    - `;blacklist <server-name>`
    - `;maplist <server-name>`
    - `;itemlist <server-name>`
    - `;kill <unique-id/alias> <server-name>`
    
- Fixed minor bug if steam community page webscrape failed
- Fixed minor bug in error handling if error has no `.original`
