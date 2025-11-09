from config import Config
from extractors.base_extractor import Extractor
from logging import Logger


class OpenLibraryExtractor(Extractor):
    """Extractor for Open Library API."""

    def extract(self, logger: Logger, title: str, author: str) -> dict:
        """Extract Open Library data for a book."""
        logger.info(f"Fetching Open Library data for {title} by {author}")

        query = f"{title} {author}".replace(" ", "+")
        url = f"{Config.OPEN_LIBRARY_BASE_URL}/search.json?q={query}&limit=1"

        results = self._fetch_from_api(url, logger, title, author, "Open Library")

        return (
            results if results is not None and results.get("numFound", 0) > 0 else None
        )
