from abc import ABC, abstractmethod
import time
import requests
from typing import Optional

from logging import Logger


class Extractor(ABC):
    """Abstract base class providing HTTP helpers for API extractors."""

    @staticmethod
    def _fetch_from_api(
        url: str, logger: Logger, isbn: str, api_name: str
    ) -> Optional[dict]:
        """Make HTTP request to API and handle common errors."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {api_name} data for ISBN {isbn}")
                return None

            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {api_name} data for ISBN {isbn}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {api_name} data for ISBN {isbn}: {str(e)}")
            return None

    @abstractmethod
    def extract(self, logger: Logger, isbn: str) -> Optional[dict]:
        """Extract data from API for a book using ISBN. Must be implemented by subclasses."""
