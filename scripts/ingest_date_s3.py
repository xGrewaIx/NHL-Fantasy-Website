import sys
from datetime import datetime

from pipeline.ingest.client import NHLClient
from pipeline.ingest.games import get_boxscore, get_play_by_play
from pipeline.ingest.schedules import get_schedule
from pipeline.storage.s3 import S3Storage

"""
This is my orchestration script for ingesting data from the NHL api and writing it to s3 bucket

1. Parse date from command line arguments
2. Get schedule for that date
3. Identify all completed games for that specific date
4. Save schedule 
5. For each completed game, get boxscore, save boxscore, get play-by-play, save play-by-play
6. Print summary of completed games and their respective file paths

- Ensure to validate date formats, game IDs, "", etc before writing to storage.
"""


def ingest_date(date: str):
    """
    ingest_date: Given a date, ingest the schedule, boxscore, and play-by-play data for that date.

    arguments:
        date: str - date in the format YYYY-MM-DD

    returns:
        None - writes data to storage and prints summary to console
    """

    # load instance of S3Storage class to write to s3 bucket
    s3_storage = S3Storage()

    # keep track of how many files were skipped and how many were written
    objects_written = 0
    objects_skipped = 0
    schedule_written = 0
    boxscore_written = 0
    pbp_written = 0

    # save target date for ingestion
    target_date = date

    # keep track of start time for the ingestion process
    start_time = datetime.now()

    # 1. Use the NHLClient to get the schedule for the given date
    client = NHLClient()

    # 2. Get the schedule for the given date
    schedule_date = datetime.strptime(date, "%Y-%m-%d").date()
    schedule_response = get_schedule(client, schedule_date)

    # load in JSON data and find all completed games for that target_date
    # extract the data from the response object using the .data attribute
    schedule_data = schedule_response.data

    # ensure schedule_data is of type dict, if not raise an error
    if not isinstance(schedule_data, dict):
        raise ValueError(f"Schedule data is not of type dict. Got {type(schedule_data)} instead.")

    # 3. Index into the schedule_data to get the list of games for that date
    # find object whose date == target date -> games is a list of dicts
    # so iterate through games to find the ones whose "gameState" == "OFF"
    # append those games "id" to a list of completed games
    # I want to save the daily schedule not the entire week, so I will save the daily schedule only

    daily_schedule = None
    completed_games = []

    for date_obj in schedule_data.get("gameWeek", []):
        if date_obj.get("date") == target_date:
            # save the daily schedule for that date as we've indexed into the schedule_data to find
            # the object whose date == target_date
            daily_schedule = date_obj

            for game in date_obj.get("games", []):
                if game.get("gameState") == "OFF":
                    game_id = game.get("id")

                    if game_id is not None:
                        # append the game_id to the completed_games list as a string
                        completed_games.append(str(game_id))

            break

    # check if daily_schedule is None, if so raise an error
    if daily_schedule is None:
        raise ValueError(f"No schedule found for date {target_date}.")

    # 4. save the schedule data to s3 storage
    schedule_file_path = s3_storage.schedule_path(target_date)

    schedule_result = s3_storage.write_json(daily_schedule, schedule_file_path)
    
    if schedule_result == "Written":
        objects_written += 1
        schedule_written += 1

    else:
        objects_skipped += 1

    # 5. For each compeleted game, get boxscore, and pbp data and save them to s3 bucket
    # track failed games in a list to print at the end
    # when a game fails to be ingested, print game ID, entity, object path, and the error message
    failed_games = []

    for game in completed_games:
        # get boxscore data
        boxscore_file_path = s3_storage.boxscore_path(date, game)
        try:
            boxscore_response = get_boxscore(client, game)
            boxscore_data = boxscore_response.data

            # check if boxscore data is of type dict and if path exists
            if not isinstance(boxscore_data, dict):
                raise ValueError(
                    f"Boxscore data for game {game} is not of type dict. Got {type(boxscore_data)} instead."
                )

            boxscore_result = s3_storage.write_json(boxscore_data, boxscore_file_path)
            if boxscore_result == "Skipped":
                print(
                    f"Boxscore file for game {game} already exists in S3 storage. Skipping writing it."
                )
                objects_skipped += 1
                
            elif boxscore_result == "Written":
                print(f"Written boxscore file for game {game} to S3 storage.")
                objects_written += 1
                boxscore_written += 1

        except Exception as error:
            failed_games.append(
                {
                    "game_id": game,
                    "entity": "boxscore",
                    "object_path": boxscore_file_path,
                    "error": str(error),
                }
            )
            print(f"Failed to ingest boxscore for game {game}. Error: {str(error)}")

        # now repeat for play-by-play data
        pbp_file_path = s3_storage.pbp_path(date, game)
        try:
            pbp_response = get_play_by_play(client, game)
            pbp_data = pbp_response.data

            # check if pbp data is of type dict and if path exists
            if not isinstance(pbp_data, dict):
                raise ValueError(
                    f"Play-by-play data for game {game} is not of type dict. Got {type(pbp_data)} instead."
                )

            pbp_result = s3_storage.write_json(pbp_data, pbp_file_path)
            if pbp_result == "Skipped":
                print(
                    f"Play-by-play file for game {game} already exists in S3 storage. Skipping writing it."
                )
                objects_skipped += 1
                
            elif pbp_result == "Written":
                print(f"Written play-by-play file for game {game} to S3 storage.")
                objects_written += 1
                pbp_written += 1

        except Exception as error:
            failed_games.append(
                {
                    "game_id": game,
                    "entity": "play-by-play",
                    "object_path": pbp_file_path,
                    "error": str(error),
                }
            )
            print(f"Failed to ingest play-by-play for game {game}. Error: {str(error)}")

    # keep track of end time for the ingestion process
    end_time = datetime.now()

    duration = end_time - start_time

    # 6. Print summary of completed games and their respective file paths
    summary = {
        "target_date": target_date,
        "completed_games": len(completed_games),
        "objects_written": objects_written,
        "objects_skipped": objects_skipped,
        "failed_games": failed_games,
        "schedule_written": schedule_written,
        "boxscore_written": boxscore_written,
        "pbp_written": pbp_written,
        "start_time": start_time.isoformat(),
        "finish_time": end_time.isoformat(),
        "duration": str(duration),
    }

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

    summary_file_path = s3_storage.ingestion_path_summary(date, run_id)
    s3_storage.write_summary(summary, summary_file_path)

    # Print summary to console
    print()
    print("=" * 60)
    print("NHL DATE INGESTION SUMMARY")
    print("=" * 60)

    print(f"Target date:       {summary['target_date']}")
    print(f"Completed games:   {summary['completed_games']}")
    print(f"Objects written:   {summary['objects_written']}")
    print(f"Objects skipped:   {summary['objects_skipped']}")
    print(f"Failed games:      {len(summary['failed_games'])}")
    print(f"Start time:        {summary['start_time']}")
    print(f"Finish time:       {summary['finish_time']}")
    print(f"Duration:          {summary['duration']}")

    if summary["failed_games"]:
        print()
        print("FAILED GAMES")
        print("-" * 60)

        for failure in summary["failed_games"]:
            print(
                f"Game ID: {failure['game_id']} | "
                f"Entity: {failure['entity']} | "
                f"Error: {failure['error']}"
            )

    print()
    print(f"Summary saved to: {summary_file_path}")

    print("=" * 60)


def main():
    """
    ingest date from command line arguments and call ingest_date function
    Future Improvements:
      - Trigger Lambda function using Amazon eventbridge to schedule the ingestion of data
        for a specific date
    """

    if len(sys.argv) < 2:
        print(
            "Error: Missing command line argument for data. Please provide a date as (YYYY-MM-DD)"
        )
        sys.exit(1)

    date = sys.argv[1]

    date_format = "%Y-%m-%d"

    try:
        datetime.strptime(date, date_format)
    except ValueError:
        print(f"Error: Invalid date format. Please provide a date in the format {date_format}.")
        sys.exit(1)

    ingest_date(date)


if __name__ == "__main__":
    main()
