from config import Config
from extractors.base_extractor import Extractor
from logging import Logger


class GoogleBooksExtractor(Extractor):
    def extract(self, logger: Logger, title: str, author: str) -> dict:
        """Fetch Google Books data for a book."""

        logger.info(f"Fetching Google Books data for {title} by {author}")

        query = f"intitle:{title} inauthor:{author}".replace(" ", "+")
        url = f"{Config.GOOGLE_BOOKS_BASE_URL}/volumes?q={query}&maxResults=1"

        return self._fetch_from_api(url, logger, title, author, "Google Books")
