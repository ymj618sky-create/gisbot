"""Utility functions for JSON I/O operations."""

import json
from pathlib import Path
from typing import Any, TypeVar
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=dict | list)


def read_json_file(path: Path) -> dict | list:
    """
    Read JSON file with error handling.

    Args:
        path: Path to the JSON file

    Returns:
        Parsed JSON data (dict or list)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        OSError: If file cannot be read
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        raise
    except OSError as e:
        logger.error(f"Error reading {path}: {e}")
        raise


def write_json_file(path: Path, data: Any) -> None:
    """
    Write JSON file with error handling and atomic write.

    Args:
        path: Path to write the JSON file
        data: Data to serialize (must be JSON-serializable)

    Raises:
        TypeError: If data is not JSON-serializable
        OSError: If file cannot be written
    """
    try:
        # Use atomic write pattern: write to temp file, then rename
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        temp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        temp_path.replace(path)
    except TypeError as e:
        logger.error(f"Data not JSON-serializable for {path}: {e}")
        raise
    except OSError as e:
        logger.error(f"Error writing {path}: {e}")
        raise


def read_json_file_safe(path: Path, default: T) -> T:
    """
    Read JSON file with fallback to default value on error.

    Args:
        path: Path to the JSON file
        default: Default value to return on error

    Returns:
        Parsed JSON data or default value on error
    """
    try:
        return read_json_file(path)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default