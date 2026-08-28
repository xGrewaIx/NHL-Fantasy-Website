from datetime import date

from pipeline.ingest.client import NHLClient

"""
Functions for retrieving schedule data from the NHL API using the NHLClient class.

schedules.py -> NHLClient.get() -> httpx -> NHL API
"""


def get_schedule(client: NHLClient, schedule_date: date):
    """
    Get the schedule data for a specific date using the NHLClient class.
    Function should recieve date, format it, and return the APIResponse

    Args:
        client (NHLClient): An instance of the NHLClient class.
        date (date): The date for which to retrieve the schedule.

    Returns:
        API response containing the schedule data for the specified date and request log
        information, including the request URL, status code, and response time.

    Raises:
        ValueError: If the date parameter is not a datetime object.
    """
    if not isinstance(schedule_date, date):
        raise ValueError("The 'schedule_date' parameter must be a datetime.date object.")

    formatted_date = schedule_date.strftime("%Y-%m-%d")

    endpoint = f"/v1/schedule/{formatted_date}"

    return client.get(endpoint)
