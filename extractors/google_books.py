import json
from config import Config
from extractors.base_extractor import Extractor
from logging import Logger
from typing import Optional


class GoogleBooksExtractor(Extractor):
    """
    Class to extract data from Google Books API.
    """

    def extract(self, logger: Logger, isbn: str) -> Optional[dict]:
        """Fetch Google Books data for a book using ISBN."""

        logger.info(f"Fetching Google Books data for ISBN {isbn}")

        query = f"isbn:{isbn}"
        url = f"{Config.GOOGLE_BOOKS_BASE_URL}/volumes?q={query}&country=US"  # US for USD currency

        response = self._fetch_from_api(url, logger, isbn, "Google Books")

        return (
            response
            if response is not None and response.get("totalItems", 0) > 0
            else None
        )
