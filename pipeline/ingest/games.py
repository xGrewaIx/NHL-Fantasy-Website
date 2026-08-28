from pipeline.ingest.client import NHLClient

"""
Functions for retrieving boxscore and play-by-play data from the NHL API
using the NHLClient class. 

Should be able to get all game_id from schedule.py and then use those game_id 
to get boxscore and play-by-play data.

games.py -> NHLClient.get() -> httpx -> NHL API
"""


def get_boxscore(client: NHLClient, game_id: str):
    """
    Get the boxscore data for a specific game using the NHLClient class.
    Function should receive game_id, format it, and return the APIResponse

    Args:
        client (NHLClient): An instance of the NHLClient class.
        game_id (str): The game ID for which to retrieve the boxscore.

    Returns:
        API response containing the boxscore data for the specified game and request log
        information, including the request URL, status code, and response time.

    Raises:
        ValueError: If the game_id parameter is not a string.
    """
    if not isinstance(game_id, str):
        raise ValueError("The 'game_id' parameter must be a string.")

    endpoint = f"/v1/gamecenter/{game_id}/boxscore"

    return client.get(endpoint)


def get_play_by_play(client: NHLClient, game_id: str):
    """
    Get the play-by-play data for a specific game using the NHLClient class.
    Function should receive game_id, format it, and return the APIResponse

    Args:
        client (NHLClient): An instance of the NHLClient class.
        game_id (str): The game ID for which to retrieve the play-by-play data.

    Returns:
        API response containing the play-by-play data for the specified game and request log
        information, including the request URL, status code, and response time.

    Raises:
        ValueError: If the game_id parameter is not a string.
    """
    if not isinstance(game_id, str):
        raise ValueError("The 'game_id' parameter must be a string.")

    endpoint = f"/v1/gamecenter/{game_id}/play-by-play"

    return client.get(endpoint)
