"""
test_health.py: Test the health endpoint of the FastAPI application
"""

# https://www.geeksforgeeks.org/python/testing-fastapi-application/
from fastapi.testclient import TestClient

# import the FastAPI applicaiton instance from the main.py file in the apps/api directory
from apps.api.main import app

# create the test client
client = TestClient(app)


# Test to see if the health endpoint is working correctly.
# Send GET request, check status code, and JSON response
def test_health() -> None:
    response = client.get("/health")

    # assert means that we are checking if the condition is true.
    assert response.status_code == 200

    # check if the response JSON has a key "status" with value "ok"
    assert response.json()["status"] == "ok"
