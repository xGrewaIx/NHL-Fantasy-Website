from datetime import date as Date
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import scripts.ingest_date_s3 as ingest_date_s3


def lambda_handler(event, context):
    """Ingest a specified NHL date or yesterday's date when scheduled.
    
    1. If the event contains a "date" key, ingest that date (manual mode).
    2. If the event does not contain a "date" key, ingest yesterday's date in Vancouver time (scheduled mode).
    3. If the event contains a "force" key, overwrite existing S3 objects. Otherwise, skip existing objects.
    4. Return a summary of the ingestion process, including the run ID and status.
    5. Raise an exception if the ingestion process fails, so that Lambda records the invocation as a failure.   
    
    """  # noqa: E501

    # Lambda passes the event JSON to this function as a Python object.
    # We expect a JSON object, which becomes a Python dictionary.
    if not isinstance(event, dict):
        raise ValueError("Event must be a JSON object.")

    # Normal runs skip existing S3 objects. Only an explicit JSON true
    # allows the ingestion script to replace them.
    force = event.get("force", False)
    if not isinstance(force, bool):
        raise ValueError("force must be a boolean.")

    if "date" in event:
        # MANUAL MODE
        # Example test event: {"date": "2023-11-10", "force": false}
        # An explicitly supplied date lets you test or rerun one NHL date.
        target_date = event["date"]

        if not isinstance(target_date, str):
            raise ValueError("date must be a YYYY-MM-DD string.")

        try:
            # fromisoformat checks that this is a real calendar date.
            # The round-trip check also requires the exact YYYY-MM-DD format.
            parsed_date = Date.fromisoformat(target_date)
            if parsed_date.isoformat() != target_date:
                raise ValueError("Date is not in canonical YYYY-MM-DD format.")
        except ValueError as error:
            raise ValueError("date must be a valid YYYY-MM-DD date.") from error

        trigger = "manual"
        
    else:
        # SCHEDULED MODE
        # EventBridge Scheduler sends {} with no date.
        # Use Vancouver's calendar date so the calculation follows the
        # NHL date you intend to process, including daylight saving changes.
        vancouver_today = datetime.now(ZoneInfo("America/Vancouver")).date()
        target_date = (vancouver_today - timedelta(days=1)).isoformat()
        trigger = "eventbridge"

    # Lambda sends print output to its CloudWatch logs.
    print(
        f"Starting NHL ingestion: date={target_date}, "
        f"force={force}, trigger={trigger}"
    )

    try:
        # The ingestion script owns the NHL API requests, S3 writes, UUID,
        # counters, and run manifest. The Lambda handler only orchestrates it.
        summary = ingest_date_s3.ingest_date(
            date=target_date,
            force=force,
            trigger=trigger,
        )

        # The run ID connects this CloudWatch invocation to its S3 manifest.
        print(
            f"Ingestion finished: date={target_date}, "
            f"run_id={summary['run_id']}, status={summary['status']}"
        )

        # ingest_date() can return a saved manifest with partial_failure
        # or failed status. Raise so Lambda records this invocation as an
        # error instead of treating the returned manifest as success.
        if summary["status"] != "success":
            raise RuntimeError(
                f"Ingestion {summary['status']} for {target_date}; "
                f"run_id={summary['run_id']}"
            )

        # A successful invocation returns its summary to a manual Lambda
        # test. EventBridge does not need to use this return value.
        return {
            "date": target_date,
            "force": force,
            "trigger": trigger,
            "run_id": summary["run_id"],
            "summary": summary,
        }

    except Exception:
        # Log the target date, then re-raise the original exception.
        # Re-raising preserves the error and traceback in CloudWatch
        # and lets Lambda handle the invocation as a failure.
        print(f"Ingestion invocation failed for date {target_date}")
        raise