from abc import ABC, abstractmethod
import requests
from config import Config

from logging import Logger


class Extractor(ABC):
    @staticmethod
    def _setup_job_data(job_data: dict):
        """Extract common job data and setup logging."""
        logger = Config.setup_logging()
        title = job_data["title"]
        author = job_data["author"]
        return logger, title, author

    @staticmethod
    def _fetch_from_api(
        url: str, logger: Logger, title: str, author: str, api_name: str
    ) -> dict:
        """Make HTTP request to API and handle common errors."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {api_name} data for {title} by {author}")
                return None

            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {api_name} data for {title} by {author}")
            return None
        except Exception as e:
            logger.error(
                f"Error fetching {api_name} data for {title} by {author}: {str(e)}"
            )
            return None

    @abstractmethod
    def extract(self, job_data: dict) -> dict:
        """Fetch data from API for a book. Must be implemented by subclasses."""
        pass
