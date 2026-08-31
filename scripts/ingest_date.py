import sys
from datetime import datetime

import pipeline.storage.local as local
from pipeline.ingest.client import NHLClient
from pipeline.ingest.games import get_boxscore, get_play_by_play
from pipeline.ingest.schedules import get_schedule

"""
This is my orchestration script for ingesting data from the NHL api and writing it to storage

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
    Ingest_date: Given a date, ingest the schedule, boxscore, and play-by-play data for that date.

    arguments:
        date: str - date in the format YYYY-MM-DD

    returns:
        None - writes data to storage and prints summary to console
    """

    # keep track of how many files were skipped and how many were written
    objects_written = 0
    objects_skipped = 0
    schedule_written = 0
    boxscore_written = 0
    pbp_written = 0

    # save target date
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
    # index into the schedule_data to get the list of games for that date
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

    # 4. Save the schedule data to local storage
    # create the path to the schedule file for that date
    schedule_file_path = local.schedule_path(date)

    # make sure to save original raw JSON response
    # save the daily_schedule instead of the entire week
    schedule_result = local.write_json(daily_schedule, schedule_file_path)

    if schedule_result == "Written":
        schedule_written += 1
        objects_written += 1

    elif schedule_result == "Skipped":
        objects_skipped += 1

    # 5. for each completed game, get the boxscore and play-by-play data and save them to storage
    # track failed games in a list to print at the end
    # when a game fails to be ingested, print the game ID, entity, and the error message
    failed_games = []

    for game in completed_games:
        # get boxscore data
        try:
            boxscore_response = get_boxscore(client, game)
            boxscore_data = boxscore_response.data

            # save boxscore data to storage
            boxscore_file_path = local.boxscore_path(date, game)
            boxscore_result = local.write_json(boxscore_data, boxscore_file_path)

            # update counters
            if boxscore_result == "Written":
                boxscore_written += 1
                objects_written += 1

            elif boxscore_result == "Skipped":
                objects_skipped += 1

        # if there is an error in getting the boxscore data,
        # catch the exception and add it to the failed_games list
        except Exception as error:
            failed_games.append({"game_id": game, "entity": "boxscore", "error": str(error)})

            print(f"Failed to ingest boxscore for game {game}. Error: {error}")

        try:
            # get play-by-play data
            pbp_response = get_play_by_play(client, game)
            pbp_data = pbp_response.data

            # save play-by-play data to storage
            pbp_file_path = local.pbp_path(date, game)
            pbp_result = local.write_json(pbp_data, pbp_file_path)

            # update counters
            if pbp_result == "Written":
                pbp_written += 1
                objects_written += 1

            elif pbp_result == "Skipped":
                objects_skipped += 1

        # If there is an error in getting the play-by-play data, catch the exception
        # and add it to the failed_games list
        except Exception as error:
            failed_games.append({"game_id": game, "entity": "play_by_play", "error": str(error)})

            print(f"Failed to ingest play-by-play for game {game}. Error: {error}")

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

    summary_file_path = local.ingestion_path_summary(date, run_id)
    local.write_summary(summary, summary_file_path)

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
    Ingest date from command line arguments and call ingest_date function.
    """

    # ingest date from command line arguments
    # https://www.geeksforgeeks.org/python/command-line-arguments-in-python/
    # Handle missing command line argument for date [0] is the script name
    # [1] is the first and only argument
    if len(sys.argv) < 2:
        print(
            "Error: Missing command line argument for date. Please provide a date as (YYYY-MM-DD)."
        )  # noqa: E501
        # terminate the script with a non-zero exit code to indicate an error
        sys.exit(1)

    # get the first command line argument for date
    date = sys.argv[1]

    # ensure date is in the format YYYY-MM-DD
    date_format = "%Y-%m-%d"

    # https://www.geeksforgeeks.org/python/python-validate-string-date-format/
    try:
        datetime.strptime(date, date_format)
    except ValueError:
        print(f"Error: Date {date} is not in the format YYYY-MM-DD")
        # terminate the script with a non-zero exit code to indicate an error
        sys.exit(1)

    # run ingest_date function with the provided date
    ingest_date(date)


if __name__ == "__main__":
    main()
