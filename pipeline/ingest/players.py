from pipeline.ingest.client import NHLClient

"""
Functions for retrieving player specific information from the NHL API using the NHLClient class.

players.py -> NHLClient.get() -> httpx -> NHL API
"""


def get_player_info(client: NHLClient, player_id: str):
    """
    Get the player information for a specific player using the NHLClient class.
    Function should receive player_id, format it, and return the APIResponse

    Args:
        client (NHLClient): An instance of the NHLClient class.
        player_id (str): The player ID for which to retrieve the information.

    Returns:
        API response containing the player information for the specified player and request log
        information, including the request URL, status code, and response time.

    Raises:
        ValueError: If the player_id parameter is not a string.
    """
    if not isinstance(player_id, str):
        raise ValueError("The 'player_id' parameter must be a string.")

    endpoint = f"/v1/player/{player_id}/landing"

    return client.get(endpoint)
