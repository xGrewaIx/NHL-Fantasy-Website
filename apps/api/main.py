"""
main.py: Main FastAPI application file. This is where the configuration, logging, and FastAPI
come togethor to create the API endpoint.
"""

import logging

# https://www.geeksforgeeks.org/python/introduction-to-fastapi/
# https://www.geeksforgeeks.org/python/creating-first-rest-api-with-fastapi/
from fastapi import FastAPI

# import get_settings and configure_logging from the config and logging_config modules
from apps.api.config import get_settings
from apps.api.logging_config import configure_logging

# give main.py the application settings and configure logging for the application.
settings = get_settings()
configure_logging(settings.log_level)


# create a logger for the main.py file
# https://realpython.com/python-logging/
# __name__ is a special variable. It makes sure hte logger's name is the same as the modules name in the python package namespace  # noqa: E501
logger = logging.getLogger(__name__)


# Create a FastAPI application instance with the title and version
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


# define a health check endpoint that returns the status of the application and the environment it is running in  # noqa: E501
# when somebody hits the /health endpoint, it will return a JSON response with the status and environment of the application.  # noqa: E501
@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
    }
