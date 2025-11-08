from config import Config
from extractors.base_extractor import Extractor
from logging import Logger


class OpenLibraryExtractor(Extractor):
    def extract(self, logger: Logger, title: str, author: str) -> dict:
        """Fetch Open Library data for a book."""
        logger.info(f"Fetching Open Library data for {title} by {author}")

        query = f"{title} {author}".replace(" ", "+")
        url = f"{Config.OPEN_LIBRARY_BASE_URL}/search.json?q={query}&limit=1"

        return self._fetch_from_api(url, logger, title, author, "Open Library")
