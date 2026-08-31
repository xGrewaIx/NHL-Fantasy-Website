# Auditing each source of data 

I have the following files already scrapped:
- Play-by-play, roster, shift, data from the season 2010-11 till 2023-24 

The NHL open API will be the source of all other data and live data:
-  https://github.com/Zmalski/NHL-API-Reference 

**A data dictionary and schema for all tables will be made prior to silver S3 bucket in AWS*

## Pre Scraped Play-by-play, roster, shift, parquet Data (201011 - 202324)

### Play-by-play

**Will need to standarize direction on every event**
- If not done events from the same spot in opposite offensive zones will be counted as different from one another 

Key Identifiers for players:
- away_skater_id# (# ranges from 1 - 10)
- home_skater_id# (# ranges from 1 - 10)

Most seasons either do not have a column home/away_skater_id# in the ranges
7-10. This would make sense as at most a team can have 6 skaters on the ice
excluding goalies. 

- away_goalie_id 
- home_goalie_id

Key Identifiers for teams:
- awayTeamId
- homeTeamId
- hometeamDefendingSide (Only available 1920 season onwards)
- away_team_side
- home_team_side


Key Identifiers for event:
- descKey
- eventId
- eventeamId
- goaleInNetId (Need to dig deeper into this variable)
- periodNumber
- periodType
- playerId_# (1-3) (this may be the players involved in the event?)
- shotType
- teamId
- timeInPeriod and timeInPeriod_s (second variable is in seconds)
- timeRemaining and timeRemaining_s (second variable is in seconds)
- typeCode
- xCoord
- xFixed
- yCoord
- yFixed
- elapsedTime
- gameState
- game_strength


Key Identifiers for game:
- gameId
- gameDate
- gameType
- season


### Rosters
- Only missing column is firstName.fr from the seasons 1011 - 1617
- fullName
- gameId
- is_home
- playerId
- position
- positionCode
- sweaterNumber
- teamId
- teamAbbrev

### shifts
- No missing or null data
- Event
- gameId
- playerId
- teamId
- teamAbbrev


## NHL API JSON responses 
Base URL: https://api-web.nhle.com/
Supplemental resource: https://docs.rs/nhl_api/latest/nhl_api/ 

Getting player specific information endpoint: /v1/player/{player}/landing (player = playerId)

Getting team roster as of now: /v1/roster/{team}/current (team = 3-letter team code) **Need to make sure each teamId has the corresponding 3-letter team code**

Getting team roster as by season: /v1/roster/{team}/{season} (team = 3-letter team code, season = in YYYYYYYY format, e.g. 20232024)

Get team season schedule as of now: /v1/club-schedule-season/{team}/now

Get team season schedule: /v1/club-schedule-season/{team}/{season}

Get schedule by date: /v1/schedule/{date} (date: format: YYYY--MM-DD) **Use this api endpoint to get schedule per day to automate pipeline**

Get Scoreboard in the current moment: /v1/scoreboard/now 

Get play by play: /v1/gamecenter/{game-id}/play-by-play **Use this api endpoint for all play by play data**

Get boxscore for a game: /v1/gamecenter/{game-id}/boxscore

Get partner game odds: /v1/partner-game/{country-code}/now (Odds for games in a specific country as of the current moment)

Get shift charts: /{lang}/shiftcharts?cayenneExp=gameId={game_id} (lang: language code)

### NHL Edge data endpoints also available 


## What source to get each form of data from for live pipeline

*NHL Api will be primary source for live pipeline, need to be careful for API rate/request limits*

- Game details -> Schedule (NHL Api) -> fact_game (fact table for each game) store: 
- gameId, seasonId, hometeamId, awayteamId, gameState,  

- Player game statistics -> Box Score (NHL Api) -> fact_player_game (fact table for each player in each game) store:
- gameId, seasonId, hometeamId, awayteamId, playerId, player_name, (all the stats outputted in JSON, update player season and career stats)
*Alternative is updating player stats as play by play data is ingested in the pipeline and use box score as validation*


- Event data -> Play by play data (NHL Api) -> fact_event (fact table for each event in each game) store: 
- gameId, seasonId, teamId (only one team as each event signals which team was involved), playerId, eventId, goalieId (null for all events other than shots), x/y coords, strength state, etc

- Player identification -> Rosters (NHL Api) -> Fact player (fact table storing player information) store:
- player number, team, stats, country, etc

- Shift data -> Shift charts (NHL Api) *worry about shift data after MVP*
- Will use shift data to analyze players quality of teammates and competition on the ice

## Differences with scraped data and NHL Api (normalize these in transformation layer)
- scraped data: ... | NHL Api: typeDescKey
