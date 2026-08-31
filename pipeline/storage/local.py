import json
import os

"""
Local.py:

This script is strictly for local use and testing purposes. 

This file should handle directory creation if the specified file path does not exist.
ex. data/bronze/entity=boxscore/date=2023-01-01/game_id=12345678/ 

- We want determinsitc functions, so that we can easily test and verify the output of this file.
- Make sure there idempotency in the functions, if target files exists, skip it 
"""


# Create functions that return the path to the file given the entity, date, game_id, and JSON object
# these are the functions that will be used to name the files in local storage
def schedule_path(date: str):
    """
    schedule_path: Given a date, return the path to the schedule file for that date.
    ex. data/bronze/entity=schedule/date=2023-01-01/schedule.json
    """
    return f"data/bronze/entity=schedule/date={date}/schedule.json"


def boxscore_path(date: str, game_id: int):
    """
    boxscore_path: Given a date and game ID, return the path to the boxscore file for that game.
    ex. data/bronze/entity=boxscore/date=2023-01-01/game_id=12345678/boxscore.json
    """
    return f"data/bronze/entity=boxscore/date={date}/game_id={game_id}/boxscore.json"


def pbp_path(date: str, game_id: int):
    """
    pbp_path: Given a date and game ID, return the path to the play-by-play file for that game.
    ex. data/bronze/entity=play_by_play/date=2023-01-01/game_id=12345678/play_by_play.json
    """
    return f"data/bronze/entity=play_by_play/date={date}/game_id={game_id}/play_by_play.json"


def team_roster_season_path(team_id: str, season: str):
    """
    team_roster_season_path: Given a team ID and season, return the path to the team roster file for
    that season.
    ex. data/bronze/entity=team_roster/team_id=BUF/season=2023-2024/roster.json
    """
    return f"data/bronze/entity=team_roster/team_id={team_id}/season={season}/roster.json"


def team_roster_now_path(team_id: str):
    """
    team_roster_now_path: Given a team ID, return the path to the current team roster file.
    ex. data/bronze/entity=team_roster/team_id=BUF/roster.json
    """
    return f"data/bronze/entity=team_roster/team_id={team_id}/roster.json"


def player_info_path(player_id: str):
    """
    player_info_path: Given a player ID, return the path to the player information file.
    ex. data/bronze/entity=player_info/player_id=8478402/player_info.json
    """
    return f"data/bronze/entity=player_info/player_id={player_id}/player_info.json"


def ingestion_path_summary(date: str, run_id: str):
    """
    Given a date return the path to the ingestion summary file for that date with a unique
    run_id using datetime
    ex. data/bronze/entity=ingestion_summary/date=2023-11-10/summary_{run_id}.json
    """

    return f"data/bronze/entity=ingestion_summary/date={date}/summary_{run_id}.json"


# create a seperate function to write the ingestion summary to a file
def write_summary(summary_data, file_path: str):
    """
    Write an ingestion summary dictionary as JSON.

    If the file already exists, skip writing it.
    """

    # check if the file already exists
    if os.path.exists(file_path):
        print(f"File {file_path} already exists. Skipping write.")
        return "Skipped"

    # get the parent directory of the file path removing the last part of the path
    parent_dir = os.path.dirname(file_path)

    # check to see if the parent directory exists, if not create it
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    # write the summary data to the file as JSON
    with open(file_path, "w") as f:
        json.dump(summary_data, f, indent=4)

    return "Written"


# Implement write_json function that takes a file path and a JSON object
# If directory does not exist, create it. If file already exists, skip writing to it.
# If file does not exist, write the JSON object to the file.


def write_json(json_object_data, file_path: str):
    """
    write_json:

    1. check if target file exists
    2. Yes -> skip writing to it
    3. No -> check if parent directory exists, if not create it
    4. Write the JSON object to the file
    """

    # 1.
    if os.path.exists(file_path):
        # 2.
        print(f"File {file_path} already exists. Skipping write.")
        return "Skipped"

    # 3.
    parent_dir = os.path.dirname(file_path)
    if not os.path.exists(parent_dir):
        print(f"Parent directory {parent_dir} does not exist. Creating it.")
        os.makedirs(parent_dir)

    # 4.
    # https://www.geeksforgeeks.org/python/reading-and-writing-json-to-a-file-in-python/
    with open(file_path, "w", encoding="utf-8") as f:
        print(f"Writing JSON object to {file_path}.")
        json.dump(json_object_data, f, indent=4)

    # return a message indicating that the file was written successfully
    return "Written"
