import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
)

"""
Sources:
https://docs.python.org/3/library/logging.html
https://www.python-httpx.org/quickstart/#exceptions
https://tenacity.readthedocs.io/en/latest/
https://www.w3schools.com/tags/ref_httpmessages.asp
"""

"""
Create a logging formatter class so that the extra fields in the log messages are structured
and easy to read.
"""


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        structured_fields = {
            "source_url": getattr(record, "source_url", None),
            "retrieved_at": getattr(record, "retrieved_at", None),
            "status_code": getattr(record, "status_code", None),
            "attempts": getattr(record, "attempts", None),
            "endpoint": getattr(record, "endpoint", None),
            "response_size_bytes": getattr(
                record,
                "response_size_bytes",
                None,
            ),
        }

        # Create a string of the structured fields, excluding any that are None
        fields = " ".join(
            f"{key}={value!r}" for key, value in structured_fields.items() if value is not None
        )

        # return a formatted string with the timestamp, log level, logger name,
        # message, and structured fields
        return (
            f"{self.formatTime(record)} "
            f"{record.levelname} "
            f"{record.name} "
            f"event={record.getMessage()} "
            f"{fields}"
        )


# initalize a logger for the NHLClient class
logger = logging.getLogger(__name__)

# If the logger has no handlers, add a StreamHandler with the StructuredFormatter
# A handler is an object that sends log messages to a specific destination,
# such as the console or a file
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)

# Set the logger level to INFO and prevent it from propagating to the root logger
# propogating is when the logger passes the log message to the root logger,
# which can cause duplicate log messages
logger.setLevel(logging.INFO)
logger.propagate = False


# create a dataclass to hold the response data and logging information
@dataclass
class APIResponse:
    """Container for an NHL API response and logging information"""

    data: Any
    source_url: str
    retrieved_at: datetime
    status_code: int
    attempts: int
    endpoint: str


# write a definition for retryable HTTP errors
# 4xx errors are client errors do not retry
# 5xx errors are server errors and should be retried
# add special case for 429 Too Many Requests (much longer wait time)
# retry when timeout occurs or when connection problems occur


# exception is the error that was raised during the request
class RetryableHTTPError(httpx.HTTPStatusError):
    """HTTP error representing a temporary server-side failure."""

    pass


def is_retryable_exception(exception: BaseException):
    """
    Determine whether an exception should trigger a retry.

    Retries occur for:
    - Network/request errors
    - HTTP 5xx server errors
    - 429 Too Many Requests

    4xx client errors are not retried.
    """
    return isinstance(exception, (httpx.RequestError, RetryableHTTPError))


# Create a function for waiting to retry for 429 Too Many Requests
def wait_for_retry(retry_state, backoff_factor=5.0, rate_limit_wait=300.0):
    """
    Determine how long to wait before retrying.

    429 errors use the configured rate-limit wait.
    Other temporary errors use exponential backoff.
    """

    exception = retry_state.outcome.exception()

    if isinstance(exception, RetryableHTTPError):
        if exception.response.status_code == 429:
            return rate_limit_wait

    return min(
        backoff_factor * (2 ** (retry_state.attempt_number - 1)),
        60,
    )


# Create a reusable class NHLClient for communicating with the NHL API
class NHLClient:
    """
    A client for communicating with the NHL API.

    Handles:
    - Base URL configuration
    - request timeout
    - retries with exponential backoff
    - returning JSON
    - detailed logging of all requests and responses
    """

    # initialize the client with all configuriation
    def __init__(
        self,
        base_url: str = "https://api-web.nhle.com",
        timeout: float = 30.0,  # maximum number of seconds to wait for a response
        max_attempts: int = 5,  # maximum number of total request attempts/retries
        backoff_factor: float = 5.0,  # base number of seconds to wait between retries
        rate_limit_wait: float = 300.0,  # number of seconds to wait for 429 Too Many Requests
    ):
        """
        Initialize the NHL API client:

        Arguments:
            base_url: Base URL for the NHL API.
            timeout: Maximum number of seconds to wait for a response.
            max_attempts: Maximum number of total request attempts.
            backoff_factor: Base number of seconds to wait between retries.
            rate_limit_wait: Number of seconds to wait for 429 Too Many Requests.
        """

        self.base_url = base_url
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.rate_limit_wait = rate_limit_wait
        # create a reusable httpx client with the base url and timeout
        self.http_client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            http2=True,  # use HTTP/2 for better performance
        )

        # create retry decorator with exponential backoff and logging
        # Use the library tenacity
        # stop after 5 attemps
        """
        Attempt 1: Wait 5 seconds
        Attempt 2: 5 x 2^1 = 10 seconds
        Attempt 3: 5 x 2^2 = 20 seconds
        Attempt 4: 5 x 2^3 = 40 seconds
        Attempt 5: 5 x 2^4 = 80 seconds (capped at 60 seconds)
        """
        # use helper function wait_for_retry to determine how long to wait for 429 Too Many Requests

        self.retrying = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=lambda retry_state: wait_for_retry(
                retry_state,
                backoff_factor=self.backoff_factor,
                rate_limit_wait=self.rate_limit_wait,
            ),
            retry=retry_if_exception(is_retryable_exception),
            before_sleep=before_sleep_log(
                logger,
                logging.WARNING,
            ),
            reraise=True,
        )

    # request the NHL API endpoint with retry logic and logging
    def _request_once(self, endpoint: str, attempt: int):
        """
        Perform one HTTP GET request.

        Retry logic is handled by Tenacity.
        """

        # log the inital request attempt
        logger.info(
            "api_request_started",
            extra={
                "source_url": str(self.http_client.base_url.join(endpoint)),
                "retrieved_at": datetime.now(
                    timezone.utc  # noqa: UP017
                ).isoformat(),
                "status_code": None,
                "attempts": attempt,
                "endpoint": endpoint,
            },
        )

        # Check to see if the endpoint is valid
        try:
            response = self.http_client.get(endpoint)

        # Handle all network errors (5xx server errors, connection errors, timeouts, etc.)
        except httpx.RequestError:
            logger.exception(
                "api_request_network_error",
                extra={
                    "source_url": str(self.http_client.base_url.join(endpoint)),
                    "retrieved_at": datetime.now(
                        timezone.utc  # noqa: UP017
                    ).isoformat(),
                    "status_code": None,
                    "attempts": attempt,
                    "endpoint": endpoint,
                },
            )

            raise

        # 429 Too Many Requests, so wait 5 minutes before retrying
        if response.status_code == 429:
            logger.warning(
                "api_request_too_many_requests",
                extra={
                    "source_url": str(response.url),
                    "retrieved_at": datetime.now(
                        timezone.utc  # noqa: UP017
                    ).isoformat(),
                    "status_code": response.status_code,
                    "attempts": attempt,
                    "endpoint": endpoint,
                },
            )

            # 429 Too Many Requests is a retryable error, so raise a RetryableHTTPError
            # to trigger a retry
            raise RetryableHTTPError(
                f"Too Many Requests: {response.status_code}",
                request=response.request,
                response=response,
            )

        # 5xx Server Errors, retry with exponential backoff
        if 500 <= response.status_code < 600:
            logger.warning(
                "api_request_server_error",
                extra={
                    "source_url": str(response.url),
                    "retrieved_at": datetime.now(
                        timezone.utc  # noqa: UP017
                    ).isoformat(),
                    "status_code": response.status_code,
                    "attempts": attempt,
                    "endpoint": endpoint,
                },
            )

            # 5xx Server Errors are retryable, so raise a RetryableHTTPError to trigger a retry
            raise RetryableHTTPError(
                f"Server error: {response.status_code}",
                request=response.request,
                response=response,
            )

        # Permanent HTTP errors, such as 4xx client errors, are not retried
        try:
            response.raise_for_status()

        # Log the error and raise it to be handled by the retry logic
        except httpx.HTTPStatusError:
            logger.error(
                "api_request_http_error",
                extra={
                    "source_url": str(response.url),
                    "retrieved_at": datetime.now(
                        timezone.utc  # noqa: UP017
                    ).isoformat(),
                    "status_code": response.status_code,
                    "attempts": attempt,
                    "endpoint": endpoint,
                },
            )

            # only raise as we will not retry
            raise

        # Parse JSON to ensure the response is valid JSON, and log an error if it is not
        try:
            data = response.json()

        # check to see if the response is a valid JSON
        except ValueError as exc:
            logger.error(
                "api_request_invalid_json",
                extra={
                    "source_url": str(response.url),
                    "retrieved_at": datetime.now(
                        timezone.utc  # noqa: UP017
                    ).isoformat(),
                    "status_code": response.status_code,
                    "attempts": attempt,
                    "endpoint": endpoint,
                },
            )

            # raise a ValueError to indicate that the response was not valid JSON
            raise ValueError(f"NHL API returned invalid JSON for endpoint: {endpoint}") from exc

        # Or else, log the successful request and return the data
        retrieved_at = datetime.now(timezone.utc)  # noqa: UP017

        # Log the successful request with all relevant information
        logger.info(
            "api_request_success",
            extra={
                "source_url": str(response.url),
                "retrieved_at": retrieved_at.isoformat(),
                "status_code": response.status_code,
                "attempts": attempt,
                "endpoint": endpoint,
                "response_size_bytes": len(response.content),
            },
        )

        # Return an APIResponse dataclass with the data and logging information
        return APIResponse(
            data=data,
            source_url=str(response.url),
            retrieved_at=retrieved_at,
            status_code=response.status_code,
            attempts=attempt,
            endpoint=endpoint,
        )

    # Request_once is called by _request, which handles retry logic and logging
    def _request(self, endpoint: str) -> APIResponse:
        """
        Make a GET request with retry handling.
        """

        # for each attempt in the retrying object, call _request_once and return the response if
        # successful.
        for attempt_manager in self.retrying:
            # Use the attempt manager as a context manager to handle retries and logging
            with attempt_manager:
                # Get the current attempt number for logging and retry purposes
                attempt = attempt_manager.retry_state.attempt_number

                # return the response from request_once, which will raise an exception
                # if the request fails
                return self._request_once(
                    endpoint,
                    attempt,
                )

        # If we reach this point it means all retry attempts have failed and nothing was returned
        raise RuntimeError("Unexpected retry state")

    # Public method to make a GET request to the NHL API
    def get(self, endpoint: str):
        """Make a GET request to the NHL API."""

        return self._request(endpoint)

    # close the underlying HTTP client when done
    def close(self):
        """Close the underlying HTTP client."""

        self.http_client.close()

    # allow NHLCleitn to act as its own target variable within a "with" statement context manager
    def __enter__(self):
        """Enter the NHLClient context manager."""

        return self

    # allow NHLCleitn to act as its own target variable within a "with" statement context manager
    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the NHLClient and close the underlying HTTP client."""

        self.close()
