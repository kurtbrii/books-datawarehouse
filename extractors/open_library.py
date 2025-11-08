from config import Config
from extractors.base_extractor import Extractor


class OpenLibraryExtractor(Extractor):
    def extract(self, job_data: dict) -> dict:
        """Fetch Open Library data for a book."""
        logger, title, author = self._setup_job_data(job_data)

        logger.info(f"Fetching Open Library data for {title} by {author}")

        query = f"{title} {author}".replace(" ", "+")
        url = f"{Config.OPEN_LIBRARY_BASE_URL}/search.json?q={query}&limit=1"

        return self._fetch_from_api(url, logger, title, author, "Open Library")
