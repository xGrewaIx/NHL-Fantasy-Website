import json
import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from pipeline.storage.base import StorageBase

load_dotenv()  # Load environment variables from .env file
# aws lambda will have BRONZE_BUCKET_NAME set in the environment variables, will load in using 
# os.getenv("BRONZE_BUCKET_NAME")

class S3Storage(StorageBase):
    # Initialize the S3Storage class with the bucket name and profile name
    # Do not give profile name, 
    
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.getenv("BRONZE_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("BRONZE_BUCKET_NAME must be set")
        self.s3 = boto3.client("s3")  # Create an S3 client using default AWS credentials

    # Write a JSON object to S3 storage
    def write_json(self, json_obj: dict, file_path: str, force: bool = False):
        """
        Write JSON data to S3 storage. If the file already exists, skip writing it.
        """
        existed = self.exists(file_path)
        if existed and not force:
            print(f"File s3://{self.bucket_name}/{file_path} already exists. Skipping write.")
            return "Skipped"

        # If force is true/or the file does not exist, write the JSON object to S3
        # overwrite the file if it already exists or create a new file if it does not exist
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=file_path,
            Body=json.dumps(json_obj, indent=4),
            ContentType="application/json",
        )
        

        result = "Replaced" if existed else "Written"
        print(f"{result} JSON object at s3://{self.bucket_name}/{file_path}.")
        return result


    def read_json(self, file_path: str):
        """
        Read a JSON object from S3 storage.
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=file_path)
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                print(f"s3://{self.bucket_name}/{file_path} does not exist.")
                return None
            else:
                raise e

    def exists(self, file_path: str):
        """
        Check whether a file exists in S3 storage.
        """
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            else:
                raise e

    def list(self, directory_path: str):
        """
        List all files in a S3 directory/prefix.
        """
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=directory_path)

        return [obj["Key"] for obj in response.get("Contents", [])]

    def write_manifest(self, filter_func):
        """
        Write a manifest of files for each date as a JSON file.
        """
        raise NotImplementedError("write_manifest is not implemented for S3Storage.")

    def schedule_path(self, date: str):
        """
        Give a date return the path to the schedule file for that date in S3 storage.

        Example: source=nhlapi/entity=schedule/date=date/schedule.json
        """
        return f"source=nhlapi/entity=schedule/date={date}/schedule.json"

    def boxscore_path(self, date: str, game_id: str):
        """
        Given a date and game_id, return the path to the boxscore file for that game in S3 storage.

        Example: source=nhlapi/entity=boxscore/date=date/game_id=game_id/boxscore.json
        """
        return f"source=nhlapi/entity=boxscore/date={date}/game_id={game_id}/boxscore.json"

    def pbp_path(self, date: str, game_id: str):
        """
        Given a date and game_id, return the path to the play-by-play file for that game in S3 storage.

        Example: source=nhlapi/entity=play_by_play/date=date/game_id=game_id/play_by_play.json
        """  # noqa: E501
        return f"source=nhlapi/entity=play_by_play/date={date}/game_id={game_id}/play_by_play.json"

    def team_roster_season_path(self, team_id: str, season: str):
        """
        Given a team ID and season, return the path to the team roster for that team and season in S3 storage.

        Example: source=nhlapi/entity=team_roster/team_id=team_id/season=season/roster.json
        """  # noqa: E501
        return f"source=nhlapi/entity=team_roster/team_id={team_id}/season={season}/roster.json"

    def team_roster_now_path(self, team_id: str):
        """
        Given a team ID, return the path to the current team roster for that team in S3 storage.

        Example: source=nhlapi/entity=team_roster/team_id=team_id/roster.json
        """
        return f"source=nhlapi/entity=team_roster/team_id={team_id}/roster.json"

    def player_info_path(self, player_id: str):
        """
        Given a player ID, return the path to the player information file for that player in S3 storage.

        Example: source=nhlapi/entity=player_info/player_id=player_id/player_info.json
        """  # noqa: E501
        return f"source=nhlapi/entity=player_info/player_id={player_id}/player_info.json"

    def ingestion_path_summary(self, date: str, run_id: str):
        """
        Given a date and run ID, return the path to the ingestion summary for that date and run ID in S3 storage.

        Example: run-manifests/date=2023-11-11/run_id=<uuid>.json
        """  # noqa: E501
        return f"run-manifests/date={date}/run_id={run_id}.json"

    def write_summary(self, summary_data: dict, file_path: str, force: bool = False):
        """
        Write an ingestion summary dictionary as JSON to S3 storage.

        If the file already exists, skip writing it.
        """
        return self.write_json(summary_data, file_path, force=force)
