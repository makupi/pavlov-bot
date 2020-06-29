# Changelog

## unreleased
- Added `;custom` command with admin permission to execute custom RCON commands

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
