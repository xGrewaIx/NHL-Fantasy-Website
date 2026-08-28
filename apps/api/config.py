"""
config.py: Give my entire application a centralized place to get all configuration values from
- Want confiruation to be centralized so that it is easy to change values in one place and have them
reflected throughout the application, as well as making it easy to add new configuration values in
the future when aws services are added.
"""

# https://www.geeksforgeeks.org/python/python-functools-lru_cache/
# lru_cache is used to cache results of function calls.
# Stored results are returned instead of executing the function again.
from functools import lru_cache

# https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/
# BaseSettings is a class-based configuration tool that reads environment variables and .env files. It allows you to define configuration values as class attributes, and it automatically loads the values from the environment or .env file when the class is instantiated.  # noqa: E501
# SettingsConfigDict is a dictionary-like object that allows you to configure the behavior of the BaseSettings class. It can be used to specify the location of the .env file, the encoding of the .env file, and how to handle extra fields that are not defined in the class.  # noqa: E501
from pydantic_settings import BaseSettings, SettingsConfigDict


# create a settings class that inherits from BaseSettings. This class will hold all the configuration values for the application.  # noqa: E501
class Settings(BaseSettings):
    app_name: str = "NHL Fantasy Platform API"  # name of the app
    environment: str = "local"  # what environment the app is running in
    log_level: str = "INFO"  # how much information logging system should log (DEBUG, INFO, WARNING, ERROR, CRITICAL)  # noqa: E501

    # create a model_config attribute that is an instance of SettingsConfigDict. This will allow us
    # to specify the location of the .env file, the encoding of the .env file, and how to handle extra fields that are not defined in the class.  # noqa: E501
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# First call created the Settings object and caches it. Subsequent calls return the cached object instead of creating a new one.  # noqa: E501
@lru_cache
def get_settings() -> (
    Settings
):  # return an instance of the settings class. This function is decorated with lru_cache to cache the result of the function call, so that subsequent calls return the cached object instead of creating a new one.  # noqa: E501
    return Settings()
