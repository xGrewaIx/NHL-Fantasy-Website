from abc import ABC, abstractmethod

"""
base.py: 

This file contains the base class for storage. All storage classes should inherit from this class
and implement the methods defined in this class.

Functions:
    1. write_json: Given a JSON object and a file path, write the JSON object to the file path.
    2. read_json: Given a file path, read the JSON object from the file path and return it.
    3. exists: Given a file path, check if the file exists and return True or False.
    4. list: Given a directory path, list all files in the directory and return a list of file paths
    5. write_manifest: create a manifest of files for each date be a JSON file
"""


class StorageBase(ABC):
    """
    Base class for storage implementations.
    """

    # Use abtract methods to define the interface for storage implemenations
    # each storage implementation should implement these methods to be used in the pipeline
    @abstractmethod
    def write_json(self, json_obj: dict, file_path: str) -> None:
        """Write a JSON object to storage."""
        raise NotImplementedError

    @abstractmethod
    def read_json(self, file_path: str) -> dict:
        """Read a JSON object from storage."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check whether a file exists in storage."""
        raise NotImplementedError

    @abstractmethod
    def list(self, directory_path: str) -> list[str]:
        """List files under a directory/prefix."""
        raise NotImplementedError

    @abstractmethod
    def write_manifest(self, filter_func) -> None:
        """Write a manifest of files for each date as a JSON file."""
        raise NotImplementedError
