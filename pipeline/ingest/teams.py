from pipeline.ingest.client import NHLClient

"""
Functions for getting team data such as rosters by season and now from the 
NHL API using the NHLClient class.

teams.py -> NHLClient.get() -> httpx -> NHL API
"""


def get_team_roster_season(client: NHLClient, team_id: str, season: str):
    """
    Get the roster data for a specific team and season using the NHLClient class.
    Function should receive team_id and season, format them, and return the APIResponse

    Args:
        client (NHLClient): An instance of the NHLClient class.
        team_id (str): The team ID for which to retrieve the roster, 3-letter code
        season (str): The season for which to retrieve the roster, in YYYYYYYY format
        (e.g., "20232024" for the 2023-2024 season).

    Returns:
        API response containing the roster data for the specified team and season and request log
        information, including the request URL, status code, and response time.

    Raises:
        ValueError: If the team_id or season parameters are not strings.
    """
    if not isinstance(team_id, str):
        raise ValueError("The 'team_id' parameter must be a string.")

    if not isinstance(season, str):
        raise ValueError("The 'season' parameter must be a string.")

    endpoint = f"/v1/roster/{team_id}/{season}"

    return client.get(endpoint)


def get_team_roster_now(client: NHLClient, team_id: str):
    """
    Get the current roster data for a specific team using the NHLClient class.
    Function should receive team_id, format it, and return the APIResponse

    Args:
        client (NHLClient): An instance of the NHLClient class.
        team_id (str): The team ID for which to retrieve the current roster, 3-letter code.

    Returns:
        API response containing the current roster data for the specified team and request log
        information, including the request URL, status code, and response time.

    Raises:
        ValueError: If the team_id parameter is not a string.
    """
    if not isinstance(team_id, str):
        raise ValueError("The 'team_id' parameter must be a string.")

    endpoint = f"/v1/roster/{team_id}"

    return client.get(endpoint)
