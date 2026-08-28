from unittest.mock import Mock

import httpx
import pytest

from pipeline.ingest.client import NHLClient
from pipeline.ingest.games import get_boxscore, get_play_by_play
from pipeline.ingest.players import get_player_info
from pipeline.ingest.schedules import get_schedule
from pipeline.ingest.teams import get_team_roster_now, get_team_roster_season

"""
Create offline tests for the API client NHLClient. The tests should cover the following scenarios:
1. Successful response, simulate HTTP 200 OK with valid JSON data.
2. Test timeout, request -> simulate a timeout exception.
3. Test temporary server error (503 code), test retry logic
4. Test permanent HTTP error(404 code), test that the client raises an exception and does not retry.
5. Test invalid JSON response, test if appropriate error is raised 
6. Test empty schedule "games": [], not a http error
7. Run the tests using pytest and ensure that all tests pass successfully.

TEST -> NHLClient -> mocked HTTPX -> fake response
"""

"""
Used the help of AI to generate these offline unit tests, as I have not used pytest before for 
api client testing. 
"""

# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------


@pytest.fixture
def nhl_client():
    """
    Create an NHLClient for testing.

    The backoff values should be configurable in NHLClient so that
    unit tests do not have to wait several seconds between retries.
    """

    client = NHLClient(
        max_attempts=3,
        backoff_factor=0,
        rate_limit_wait=0,
    )

    yield client

    client.close()


# ---------------------------------------------------------------------------
# Helper function
# ---------------------------------------------------------------------------


def make_response(
    status_code: int,
    json_data=None,
    content: bytes | None = None,
    url: str = "https://api-web.nhle.com/v1/test",
) -> httpx.Response:
    """
    Create a fake HTTPX response for testing.

    A request is included because NHLClient uses response.request
    when creating HTTPStatusError exceptions.
    """

    request = httpx.Request("GET", url)

    if json_data is not None:
        return httpx.Response(
            status_code,
            json=json_data,
            request=request,
        )

    return httpx.Response(
        status_code,
        content=content,
        request=request,
    )


# ---------------------------------------------------------------------------
# Test 1: Successful response
# ---------------------------------------------------------------------------


def test_successful_response(nhl_client):
    """
    Test that NHLClient correctly handles a successful HTTP 200 response
    containing valid JSON.
    """

    mock_response = make_response(
        200, json_data={"data": "valid"}, url="https://api-web.nhle.com/v1/game/1234/boxscore"
    )

    nhl_client.http_client.get = Mock(return_value=mock_response)

    response = nhl_client.get("/v1/game/1234/boxscore")

    assert response.status_code == 200
    assert response.data == {"data": "valid"}
    assert response.attempts == 1
    assert response.source_url == ("https://api-web.nhle.com/v1/game/1234/boxscore")
    assert response.retrieved_at is not None

    nhl_client.http_client.get.assert_called_once_with("/v1/game/1234/boxscore")


# ---------------------------------------------------------------------------
# Test 2: Timeout
# ---------------------------------------------------------------------------


def test_timeout(nhl_client):
    """
    Test that a timeout is retried and eventually raised after
    the maximum number of attempts.
    """

    nhl_client.http_client.get = Mock(side_effect=httpx.ReadTimeout("Request timed out."))

    with pytest.raises(httpx.ReadTimeout):
        nhl_client.get("/v1/test")

    assert nhl_client.http_client.get.call_count == 3


# ---------------------------------------------------------------------------
# Test 3: Temporary server error (503)
# ---------------------------------------------------------------------------


def test_temporary_server_error_retries(nhl_client):
    """
    Test that a temporary HTTP 503 error is retried and that the
    request succeeds when the server eventually returns HTTP 200.
    """

    response_503 = make_response(
        503,
        json_data={"error": "Service unavailable"},
    )

    response_200 = make_response(
        200,
        json_data={"data": "success"},
    )

    nhl_client.http_client.get = Mock(
        side_effect=[
            response_503,
            response_503,
            response_200,
        ]
    )

    response = nhl_client.get("/v1/test")

    assert response.status_code == 200
    assert response.data == {"data": "success"}
    assert response.attempts == 3

    assert nhl_client.http_client.get.call_count == 3


# ---------------------------------------------------------------------------
# Test 4: Permanent HTTP error (404)
# ---------------------------------------------------------------------------


def test_permanent_http_error_does_not_retry(nhl_client):
    """
    Test that a permanent HTTP 404 error raises an exception
    and is not retried.
    """

    response_404 = make_response(
        404,
        json_data={"error": "Not found"},
    )

    nhl_client.http_client.get = Mock(return_value=response_404)

    with pytest.raises(httpx.HTTPStatusError):
        nhl_client.get("/v1/test")

    # 404 should not be retried.
    assert nhl_client.http_client.get.call_count == 1


# ---------------------------------------------------------------------------
# Test 5: Invalid JSON
# ---------------------------------------------------------------------------


def test_invalid_json(nhl_client):
    """
    Test that an HTTP 200 response containing invalid JSON raises
    a ValueError.
    """

    mock_response = make_response(
        200,
        content=b"this is not valid JSON",
    )

    nhl_client.http_client.get = Mock(return_value=mock_response)

    with pytest.raises(
        ValueError,
        match="NHL API returned invalid JSON",
    ):
        nhl_client.get("/v1/test")

    # Invalid JSON should not be retried.
    assert nhl_client.http_client.get.call_count == 1


# ---------------------------------------------------------------------------
# Test 6: Empty schedule
# ---------------------------------------------------------------------------


def test_empty_schedule(nhl_client):
    """
    Test that an empty NHL schedule is treated as valid data
    rather than an HTTP error.
    """

    mock_response = make_response(
        200,
        json_data={"games": []},
    )

    nhl_client.http_client.get = Mock(return_value=mock_response)

    response = nhl_client.get("/v1/schedule/2025-04-01")

    assert response.status_code == 200
    assert response.data == {"games": []}
    assert response.data["games"] == []
    assert response.attempts == 1

    # Empty data is valid, so there should be no retry.
    assert nhl_client.http_client.get.call_count == 1


# ---------------------------------------------------------------------------
# Test 7: Test all games.py, players.py, schedule.py, teams.py functions
#         with mocked NHLClient.get() to ensure that the functions are calling
#         the correct endpoints
# ---------------------------------------------------------------------------


def test_all_functions_call_correct_endpoints(nhl_client):
    """
    Test that all ingestion functions construct the correct NHL API
    endpoints, delegate the request to NHLClient.get(), and return
    the client's response.
    """

    mock_response = make_response(
        200,
        json_data={"data": "valid"},
    )

    nhl_client.get = Mock(return_value=mock_response)

    # ---------------------------------------------------------
    # get_boxscore
    # ---------------------------------------------------------

    game_id = "1234"

    response = get_boxscore(
        nhl_client,
        game_id,
    )

    assert response is mock_response

    nhl_client.get.assert_called_once_with(f"/v1/gamecenter/{game_id}/boxscore")

    nhl_client.get.reset_mock()

    # ---------------------------------------------------------
    # get_play_by_play
    # ---------------------------------------------------------

    response = get_play_by_play(
        nhl_client,
        game_id,
    )

    assert response is mock_response

    nhl_client.get.assert_called_once_with(f"/v1/gamecenter/{game_id}/play-by-play")

    nhl_client.get.reset_mock()

    # ---------------------------------------------------------
    # get_player_info
    # ---------------------------------------------------------

    player_id = "5678"

    response = get_player_info(
        nhl_client,
        player_id,
    )

    assert response is mock_response

    nhl_client.get.assert_called_once_with(f"/v1/player/{player_id}/landing")

    nhl_client.get.reset_mock()

    # ---------------------------------------------------------
    # get_schedule
    # ---------------------------------------------------------

    from datetime import date

    schedule_date = date(2023, 11, 10)

    response = get_schedule(
        nhl_client,
        schedule_date,
    )

    assert response is mock_response

    nhl_client.get.assert_called_once_with("/v1/schedule/2023-11-10")

    nhl_client.get.reset_mock()

    # ---------------------------------------------------------
    # get_team_roster_season
    # ---------------------------------------------------------

    team_id = "BUF"
    season = "20232024"

    response = get_team_roster_season(
        nhl_client,
        team_id,
        season,
    )

    assert response is mock_response

    nhl_client.get.assert_called_once_with(f"/v1/roster/{team_id}/{season}")

    nhl_client.get.reset_mock()

    # ---------------------------------------------------------
    # get_team_roster_now
    # ---------------------------------------------------------

    response = get_team_roster_now(
        nhl_client,
        team_id,
    )

    assert response is mock_response

    nhl_client.get.assert_called_once_with(f"/v1/roster/{team_id}")
