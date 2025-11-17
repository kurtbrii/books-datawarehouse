from config import Config
from extractors.base_extractor import Extractor
from logging import Logger


class OpenLibraryExtractor(Extractor):
    """Extractor for Open Library API."""

    def extract(self, logger: Logger, isbn: str) -> dict:
        """Extract Open Library data for a book using ISBN."""

        url = f"{Config.OPEN_LIBRARY_BASE_URL}/search.json?isbn={isbn}"

        results = self._fetch_from_api(url, logger, isbn, "Open Library")

        return (
            results if results is not None and results.get("numFound", 0) > 0 else None
        )
