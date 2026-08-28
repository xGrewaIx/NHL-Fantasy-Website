from pipeline.ingest.client import NHLClient

"""
Peform a real integration test of the NHLClient class by making actual requests to the NHL API.

1. Get the schedule for 2023-11-10

2. Get the boxscore and play-by-play data for the game_id 2023020204 which is in the 
schedule for 2023-11-10. GET THE game_id FROM THE SCHEDULE, DO NOT HARDCODE IT.
2023020204 is the first game_id in the schedule for 2023-11-10

3. Check that the boxscore and play-by-play data are not empty and contain valid JSON

4. Check the roster for the Buffalo Sabers (BUF) for the season 2023-24

5. Take a specific player_id from the roster and get the player information for that player_id
"""


def test_nhl_client_integration():

    with NHLClient() as client:
        # step 1: get the schedule for 2023-11-10
        schedule_endpoint = "/v1/schedule/2023-11-10"
        schedule_response = client.get(schedule_endpoint)

        # get the first game_id from the schedule
        # gameweek is the first list, get the first days games list, then
        # get the first game in the list and get the id
        assert schedule_response.status_code == 200
        assert schedule_response.data is not None
        assert "gameWeek" in schedule_response.data
        assert len(schedule_response.data["gameWeek"]) > 0
        assert "games" in schedule_response.data["gameWeek"][0]
        assert len(schedule_response.data["gameWeek"][0]["games"]) > 0
        game_id = schedule_response.data["gameWeek"][0]["games"][0]["id"]
        assert game_id == 2023020204  # make sure the game_id is correct for the test

        # step 2: get the boxscore and play-by-play data for the game_id
        boxscore_endpoint = f"/v1/gamecenter/{game_id}/boxscore"
        boxscore_response = client.get(boxscore_endpoint)

        play_by_play_endpoint = f"/v1/gamecenter/{game_id}/play-by-play"
        play_by_play_response = client.get(play_by_play_endpoint)

        # step 3: check that the boxscore and play-by-play data are not empty and contain valid JSON
        assert boxscore_response.status_code == 200
        assert play_by_play_response.status_code == 200

        assert boxscore_response.data is not None
        assert play_by_play_response.data is not None

        # step 4: check the roster for the Buffalo Sabers (BUF) for the season 2023-24
        roster_endpoint = "/v1/roster/BUF/20232024"
        roster_response = client.get(roster_endpoint)

        # step 5: take a specific player_id from the roster and get the player
        # information for that player_id
        assert roster_response.status_code == 200
        assert roster_response.data is not None
        assert "forwards" in roster_response.data
        player_id = roster_response.data["forwards"][0]["id"]
        player_endpoint = f"/v1/player/{player_id}/landing"

        # make sure to check that the player information is not empty and contains valid JSON
        player_response = client.get(player_endpoint)
        assert player_response.status_code == 200
        assert player_response.data is not None
