import json
import os

from pipeline.storage.base import StorageBase

"""
Local.py:

This script is strictly for local use and testing purposes. 

This file should handle directory creation if the specified file path does not exist.
ex. data/bronze/entity=boxscore/date=2023-01-01/game_id=12345678/ 

- We want determinsitc functions, so that we can easily test and verify the output of this file.
- Make sure there idempotency in the functions, if target files exists, skip it 
"""


class LocalStorage(StorageBase):
    # Create functions that return the path to the file given the entity,
    # date, game_id, etc.

    def schedule_path(self, date: str):
        """
        Given a date, return the path to the schedule file for that date.

        Example:
        data/bronze/entity=schedule/date=2023-01-01/schedule.json
        """
        return f"data/bronze/entity=schedule/date={date}/schedule.json"

    def boxscore_path(self, date: str, game_id: int):
        """
        Given a date and game ID, return the path to the boxscore file.
        """
        return f"data/bronze/entity=boxscore/date={date}/game_id={game_id}/boxscore.json"

    def pbp_path(self, date: str, game_id: int):
        """
        Given a date and game ID, return the path to the play-by-play file.
        """
        return f"data/bronze/entity=play_by_play/date={date}/game_id={game_id}/play_by_play.json"

    def team_roster_season_path(self, team_id: str, season: str):
        """
        Given a team ID and season, return the path to the team roster.
        """
        return f"data/bronze/entity=team_roster/team_id={team_id}/season={season}/roster.json"

    def team_roster_now_path(self, team_id: str):
        """
        Given a team ID, return the path to the current team roster.
        """
        return f"data/bronze/entity=team_roster/team_id={team_id}/roster.json"

    def player_info_path(self, player_id: str):
        """
        Given a player ID, return the path to the player information file.
        """
        return f"data/bronze/entity=player_info/player_id={player_id}/player_info.json"

    def ingestion_path_summary(self, date: str, run_id: str):
        """
        Given a date and run ID, return the path to the ingestion summary.
        """
        return f"data/bronze/entity=ingestion_summary/date={date}/summary_{run_id}.json"

    def write_summary(self, summary_data: dict, file_path: str):
        """
        Write an ingestion summary dictionary as JSON.

        If the file already exists, skip writing it.
        """
        return self.write_json(summary_data, file_path)

    def write_json(self, json_object_data: dict, file_path: str):
        """
        Write a JSON object to a local file.

        If the file already exists, skip writing it.
        If the parent directory does not exist, create it.
        """

        # Check if target file already exists
        if os.path.exists(file_path):
            print(f"File {file_path} already exists. Skipping write.")
            return "Skipped"

        # Create parent directory if necessary
        parent_dir = os.path.dirname(file_path)

        if parent_dir and not os.path.exists(parent_dir):
            print(f"Parent directory {parent_dir} does not exist. Creating it.")
            os.makedirs(parent_dir)

        # Write JSON
        with open(file_path, "w", encoding="utf-8") as f:
            print(f"Writing JSON object to {file_path}.")
            json.dump(json_object_data, f, indent=4)

        return "Written"

    def read_json(self, file_path: str):
        """
        Read a JSON object from a local file.
        """
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def exists(self, file_path: str):
        """
        Check whether a local file exists.
        """
        return os.path.exists(file_path)

    def list(self, directory_path: str):
        """
        List all files in a local directory.
        """
        if not os.path.exists(directory_path):
            return []

        return [os.path.join(directory_path, file_name) for file_name in os.listdir(directory_path)]

    def write_manifest(self, filter_func):
        """
        Write a manifest of files matching a filter.

        Not implemented yet.
        """
        raise NotImplementedError
