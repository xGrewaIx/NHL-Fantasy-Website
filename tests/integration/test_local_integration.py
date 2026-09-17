import json
import os

import pytest

from scripts.ingest_date_local import ingest_date

# set global variables for the test
TARGET_DATE = "2023-11-10"
BRONZE_PATH = "data/bronze"

"""
Build the integration test for the ingest_date function. 

1. run ingestion
2. check expected directories/files
3. run ingestion again to ensure that files are skipped if they already exist
4. check nothing new was created

API -> ingestion - storage

Use the date: 2023-11-10


AI was again used to help assist me in writing the tests
"""


def get_completed_games(schedule_file_path):
    """
    Read the schedule file and return all completed game IDs
    for the target date.
    """

    with open(schedule_file_path) as f:
        schedule_data = json.load(f)

    completed_games = []

    for game in schedule_data.get("games", []):
        if game.get("gameState") == "OFF":
            game_id = game.get("id")

            if game_id is not None:
                completed_games.append(str(game_id))

    return completed_games


def get_all_files(directory):
    """
    Return a set containing every file under a directory.
    """

    files = set()

    for root, dirs, filenames in os.walk(directory):  # noqa: B007
        for filename in filenames:
            files.add(os.path.join(root, filename))

    return files


@pytest.mark.integration
def test_ingest_date_creates_schedule():
    """
    Verify that ingest_date creates the expected schedule file.
    """

    ingest_date(TARGET_DATE)

    schedule_file_path = f"data/bronze/entity=schedule/date={TARGET_DATE}/schedule.json"

    # test to check if the specific path is created and the schedule file exists
    assert os.path.exists(schedule_file_path)


@pytest.mark.integration
def test_ingest_date_creates_completed_game_data():
    """
    Verify that every completed game has both a boxscore
    and play-by-play file.
    """

    ingest_date(TARGET_DATE)

    schedule_file_path = f"data/bronze/entity=schedule/date={TARGET_DATE}/schedule.json"

    assert os.path.exists(schedule_file_path)

    completed_games = get_completed_games(schedule_file_path)

    assert len(completed_games) > 0

    for game_id in completed_games:
        boxscore_file_path = (
            f"data/bronze/entity=boxscore/date={TARGET_DATE}/game_id={game_id}/boxscore.json"
        )

        pbp_file_path = (
            f"data/bronze/entity=play_by_play/"
            f"date={TARGET_DATE}/"
            f"game_id={game_id}/play_by_play.json"
        )

        # test to check if the specific paths are created and the files exist
        assert os.path.exists(boxscore_file_path), (
            f"Boxscore file does not exist: {boxscore_file_path}"
        )

        assert os.path.exists(pbp_file_path), f"Play-by-play file does not exist: {pbp_file_path}"


@pytest.mark.integration
def test_ingest_date_preserves_raw_json():
    """
    Verify that the raw NHL responses are stored as valid JSON.
    """

    ingest_date(TARGET_DATE)

    schedule_file_path = f"data/bronze/entity=schedule/date={TARGET_DATE}/schedule.json"

    with open(schedule_file_path) as f:
        schedule_data = json.load(f)

    # check to see if the schedule data is a dictionary
    assert isinstance(schedule_data, dict)

    completed_games = get_completed_games(schedule_file_path)

    for game_id in completed_games:
        boxscore_file_path = (
            f"data/bronze/entity=boxscore/date={TARGET_DATE}/game_id={game_id}/boxscore.json"
        )

        pbp_file_path = (
            f"data/bronze/entity=play_by_play/"
            f"date={TARGET_DATE}/"
            f"game_id={game_id}/play_by_play.json"
        )

        with open(boxscore_file_path) as f:
            boxscore_data = json.load(f)

        with open(pbp_file_path) as f:
            pbp_data = json.load(f)

        # check to see if the boxscore and play-by-play data are dictionaries
        assert isinstance(boxscore_data, dict)
        assert isinstance(pbp_data, dict)


@pytest.mark.integration
def test_ingest_date_is_idempotent_for_raw_data():
    """
    Run ingestion twice.

    The second run should not create any new raw NHL data files.
    """

    ingest_date(TARGET_DATE)

    files_after_first_run = get_all_files(BRONZE_PATH)

    ingest_date(TARGET_DATE)

    files_after_second_run = get_all_files(BRONZE_PATH)

    summary_files_after_second_run = {
        file for file in files_after_second_run if "entity=ingestion_summary" in file
    }

    summary_files_after_first_run = {
        file for file in files_after_first_run if "entity=ingestion_summary" in file
    }

    raw_files_after_first_run = files_after_first_run - summary_files_after_first_run

    raw_files_after_second_run = files_after_second_run - summary_files_after_second_run

    # check to see if the raw files after the first run are the same as the raw files
    # after teh second run
    assert raw_files_after_first_run == raw_files_after_second_run


@pytest.mark.integration
def test_ingest_date_creates_new_summary_each_run():
    """
    Verify that every ingestion run creates a new summary file.
    """

    ingest_date(TARGET_DATE)

    files_after_first_run = get_all_files(BRONZE_PATH)

    summary_files_after_first_run = {
        file for file in files_after_first_run if "entity=ingestion_summary" in file
    }

    ingest_date(TARGET_DATE)

    files_after_second_run = get_all_files(BRONZE_PATH)

    summary_files_after_second_run = {
        file for file in files_after_second_run if "entity=ingestion_summary" in file
    }

    assert len(summary_files_after_second_run) == (len(summary_files_after_first_run) + 1)


@pytest.mark.integration
def test_ingestion_summary_exists():
    """
    Verify that an ingestion summary is created.
    """

    ingest_date(TARGET_DATE)

    summary_directory = f"data/bronze/entity=ingestion_summary/date={TARGET_DATE}"

    assert os.path.exists(summary_directory)

    summary_files = [file for file in os.listdir(summary_directory) if file.endswith(".json")]

    assert len(summary_files) >= 1


@pytest.mark.integration
def test_ingestion_summary_structure():
    """
    Verify that the ingestion summary contains the required fields.
    """

    ingest_date(TARGET_DATE)

    summary_directory = f"data/bronze/entity=ingestion_summary/date={TARGET_DATE}"

    summary_files = [file for file in os.listdir(summary_directory) if file.endswith(".json")]

    assert len(summary_files) >= 1

    summary_file_path = os.path.join(
        summary_directory,
        summary_files[-1],
    )

    with open(summary_file_path) as f:
        summary = json.load(f)

    required_fields = {
        "target_date",
        "completed_games",
        "objects_written",
        "objects_skipped",
        "failed_games",
        "start_time",
        "finish_time",
        "duration",
    }

    assert required_fields.issubset(summary.keys())


@pytest.mark.integration
def test_ingestion_summary_values():
    """
    Verify that the summary contains sensible values.
    """

    ingest_date(TARGET_DATE)

    summary_directory = f"data/bronze/entity=ingestion_summary/date={TARGET_DATE}"

    summary_files = [file for file in os.listdir(summary_directory) if file.endswith(".json")]

    summary_file_path = os.path.join(
        summary_directory,
        summary_files[-1],
    )

    with open(summary_file_path) as f:
        summary = json.load(f)

    assert summary["target_date"] == TARGET_DATE

    assert summary["completed_games"] >= 0

    assert summary["objects_written"] >= 0

    assert summary["objects_skipped"] >= 0

    assert isinstance(summary["failed_games"], list)

    assert summary["start_time"]
    assert summary["finish_time"]
    assert summary["duration"]
