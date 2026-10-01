import sys
import uuid
from datetime import datetime, timezone

from pipeline.ingest.client import NHLClient
from pipeline.ingest.games import get_boxscore, get_play_by_play
from pipeline.ingest.schedules import get_schedule
from pipeline.storage.s3 import S3Storage


def ingest_date(date: str, force: bool = False, trigger: str = "local"):
    """
    Ingest the schedule, boxscore, and play-by-play data for one YYYY-MM-DD date.

    force=True replaces existing NHL source objects. Returns a run manifest
    with status success, partial_failure, or failed.
    """
    run_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)

    # Load S3 storage; initialization is inside the outer try so a failure is logged.
    s3_storage = None

    # Keep track of object outcomes. Replacements are separate from new writes.
    objects_written = 0
    objects_skipped = 0
    objects_replaced = 0
    objects_failed = 0
    schedule_written = 0
    boxscore_written = 0
    pbp_written = 0
    failed_objects = []
    run_error = None

    target_date = date
    daily_schedule = None
    completed_games = []
    games_found = 0

    # Run-level errors (schedule, validation, or schedule write) still get a manifest.
    try:
        schedule_date = datetime.strptime(date, "%Y-%m-%d").date()
        if schedule_date.isoformat() != date:
            raise ValueError("Date must be in YYYY-MM-DD format.")

        s3_storage = S3Storage()
        client = NHLClient()

        # 1–2. Retrieve the requested week's schedule.
        schedule_response = get_schedule(client, schedule_date)
        schedule_data = schedule_response.data
        if not isinstance(schedule_data, dict):
            raise ValueError(
                f"Schedule data is not a dict. Got {type(schedule_data)} instead."
            )
        if not isinstance(schedule_data.get("gameWeek"), list):
            raise ValueError("Schedule response does not contain a gameWeek list.")

        # 3. Find the requested date and its completed games.
        for date_obj in schedule_data["gameWeek"]:
            if not isinstance(date_obj, dict) or date_obj.get("date") != target_date:
                continue

            daily_schedule = date_obj
            games = date_obj.get("games")
            if not isinstance(games, list):
                raise ValueError(f"Games for {target_date} must be a list.")

            for game in games:
                if not isinstance(game, dict):
                    raise ValueError(f"Invalid game in schedule for {target_date}.")
                games_found += 1
                if game.get("gameState") in {"OFF", "FINAL"}:
                    game_id = game.get("id")
                    if game_id is None:
                        raise ValueError("Completed game is missing its ID.")
                    completed_games.append(str(game_id))
            break

        # An absent date in a valid gameWeek means no games; its manifest records that.
        # 4. Wait until all games finish so an early, incomplete schedule cannot
        # become a permanently skipped S3 object on the next default run.
        if daily_schedule is not None and games_found == len(completed_games):
            schedule_file_path = s3_storage.schedule_path(target_date)
            schedule_result = s3_storage.write_json(
                daily_schedule, schedule_file_path, force=force
            )
            if schedule_result == "Written":
                objects_written += 1
                schedule_written += 1
            elif schedule_result == "Skipped":
                objects_skipped += 1
            elif schedule_result == "Replaced":
                objects_replaced += 1
            else:
                raise ValueError(f"Unexpected schedule write result: {schedule_result!r}")

        # 5. Attempt each game object independently.
        for game in completed_games:
            boxscore_file_path = s3_storage.boxscore_path(date, game)
            try:
                boxscore_response = get_boxscore(client, game)
                boxscore_data = boxscore_response.data
                if not isinstance(boxscore_data, dict):
                    raise ValueError(
                        f"Boxscore data for game {game} is not a dict. "
                        f"Got {type(boxscore_data)} instead."
                    )

                boxscore_result = s3_storage.write_json(
                    boxscore_data, boxscore_file_path, force=force
                )
                if boxscore_result == "Skipped":
                    print(f"Boxscore for game {game} already exists. Skipping.")
                    objects_skipped += 1
                elif boxscore_result == "Written":
                    print(f"Written boxscore for game {game} to S3.")
                    objects_written += 1
                    boxscore_written += 1
                elif boxscore_result == "Replaced":
                    print(f"Replaced boxscore for game {game} in S3.")
                    objects_replaced += 1
                else:
                    raise ValueError(
                        f"Unexpected boxscore write result: {boxscore_result!r}"
                    )
            except Exception as error:
                failed_objects.append(
                    {
                        "game_id": game,
                        "entity": "boxscore",
                        "object_path": boxscore_file_path,
                        "error": str(error),
                    }
                )
                objects_failed += 1
                print(f"Failed to ingest boxscore for game {game}: {error}")

            pbp_file_path = s3_storage.pbp_path(date, game)
            try:
                pbp_response = get_play_by_play(client, game)
                pbp_data = pbp_response.data
                if not isinstance(pbp_data, dict):
                    raise ValueError(
                        f"Play-by-play data for game {game} is not a dict. "
                        f"Got {type(pbp_data)} instead."
                    )

                pbp_result = s3_storage.write_json(
                    pbp_data, pbp_file_path, force=force
                )
                if pbp_result == "Skipped":
                    print(f"Play-by-play for game {game} already exists. Skipping.")
                    objects_skipped += 1
                elif pbp_result == "Written":
                    print(f"Written play-by-play for game {game} to S3.")
                    objects_written += 1
                    pbp_written += 1
                elif pbp_result == "Replaced":
                    print(f"Replaced play-by-play for game {game} in S3.")
                    objects_replaced += 1
                else:
                    raise ValueError(f"Unexpected PBP write result: {pbp_result!r}")
            except Exception as error:
                failed_objects.append(
                    {
                        "game_id": game,
                        "entity": "play-by-play",
                        "object_path": pbp_file_path,
                        "error": str(error),
                    }
                )
                objects_failed += 1
                print(f"Failed to ingest play-by-play for game {game}: {error}")
    except Exception as error:
        run_error = {"type": type(error).__name__, "message": str(error)}
        print(f"Run-level ingestion failure for {target_date}: {error}", file=sys.stderr)

    # 6. Build and persist this run's summary/manifest.
    end_time = datetime.now(timezone.utc)
    duration = end_time - start_time
    unfinished_games = games_found - len(completed_games)
    if run_error is not None:
        status = "failed"
    elif objects_failed or unfinished_games:
        status = "partial_failure"
    else:
        status = "success"

    summary = {
        "run_id": run_id,
        "status": status,
        "target_date": target_date,
        "trigger": trigger,
        "force": force,
        "games_found": games_found,
        "completed_games": len(completed_games),
        "unfinished_games": unfinished_games,
        "objects_written": objects_written,
        "objects_skipped": objects_skipped,
        "objects_replaced": objects_replaced,
        "objects_failed": objects_failed,
        "failed_objects": failed_objects,
        "run_error": run_error,
        "schedule_written": schedule_written,
        "boxscore_written": boxscore_written,
        "pbp_written": pbp_written,
        "start_time": start_time.isoformat(),
        "finish_time": end_time.isoformat(),
        "duration": str(duration),
    }

    if s3_storage is None:
        raise RuntimeError(
            f"Could not initialize S3 to save the manifest for run {run_id}: {run_error}"
        )
    summary_file_path = s3_storage.ingestion_path_summary(target_date, run_id)
    # force applies to NHL source objects, not a unique per-run manifest.
    summary_result = s3_storage.write_summary(summary, summary_file_path)
    if summary_result != "Written":
        raise RuntimeError(
            f"Manifest was not written: {summary_file_path} ({summary_result})"
        )

    print()
    print("=" * 60)
    print("NHL DATE INGESTION SUMMARY")
    print("=" * 60)
    print(f"Run ID:            {summary['run_id']}")
    print(f"Status:            {summary['status']}")
    print(f"Target date:       {summary['target_date']}")
    print(f"Games found:       {summary['games_found']}")
    print(f"Completed games:   {summary['completed_games']}")
    print(f"Unfinished games:  {summary['unfinished_games']}")
    print(f"Objects written:   {summary['objects_written']}")
    print(f"Objects skipped:   {summary['objects_skipped']}")
    print(f"Objects replaced:  {summary['objects_replaced']}")
    print(f"Objects failed:    {summary['objects_failed']}")
    print(f"Start time:        {summary['start_time']}")
    print(f"Finish time:       {summary['finish_time']}")
    print(f"Duration:          {summary['duration']}")

    if summary["failed_objects"]:
        print()
        print("FAILED OBJECTS")
        print("-" * 60)
        for failure in summary["failed_objects"]:
            print(
                f"Game ID: {failure['game_id']} | "
                f"Entity: {failure['entity']} | "
                f"Error: {failure['error']}"
            )
    if summary["run_error"]:
        print(f"Run error: {summary['run_error']['message']}")
    print()
    print(f"Summary saved to: {summary_file_path}")
    print("=" * 60)
    return summary


def main():
    """Ingest the command-line date; --force replaces existing NHL objects."""
    if len(sys.argv) < 2:
        print("Error: Missing date. Provide a date as YYYY-MM-DD.")
        sys.exit(1)

    date = sys.argv[1]
    date_format = "%Y-%m-%d"
    try:
        parsed_date = datetime.strptime(date, date_format).date()
        if parsed_date.isoformat() != date:
            raise ValueError("Date must use YYYY-MM-DD.")
    except ValueError:
        print(f"Error: Invalid date. Provide a date in the format {date_format}.")
        sys.exit(1)

    if len(sys.argv) > 3 or (len(sys.argv) == 3 and sys.argv[2] != "--force"):
        print("Usage: python -m scripts.ingest_date_s3 YYYY-MM-DD [--force]")
        sys.exit(1)

    force = len(sys.argv) == 3 and sys.argv[2] == "--force"
    summary = ingest_date(date, force=force)
    if summary["status"] != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()