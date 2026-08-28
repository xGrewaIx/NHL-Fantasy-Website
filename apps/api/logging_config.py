"""
logging_config.py: confiuring logging for the aplpication. Each time the application runs, it will
log information about the application, such as the time, log level, logger name, and message.
"""

# https://www.w3schools.com/python/ref_module_logging.asp
# https://www.geeksforgeeks.org/python/logging-in-python/
# https://realpython.com/python-logging/
import logging


# create a function that configures logging for the application
# Takes in log level as a string and sets the logging level accordingly. The default log level is INFO.  # noqa: E501
# return None
def configure_logging(log_level: str = "INFO") -> None:

    # configure the root logger, set filename, level, and format.
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
