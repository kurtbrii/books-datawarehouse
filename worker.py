import sys

from config import Config
from logging import Logger
from typing import Dict
from extractors.google_books import GoogleBooksExtractor
from extractors.open_library import OpenLibraryExtractor


def print_summary(logger: Logger, stats: Dict[str, int]) -> None:
    """
    Print a summary of the processing results.

    Args:
        logger: Logger instance
        stats: Dictionary containing processing statistics
    """
    logger.info("=" * 60)
    logger.info("📊 Worker: Job processing complete")
    logger.info("=" * 60)
    logger.info(f"📈 Total rows processed: {stats['total_fetched']}")
    logger.info(f"✅ Successful Google Books: {stats['successful_google_books']}")
    logger.info(f"✅ Successful Open Library: {stats['successful_open_library']}")
    logger.info(f"❌ Failed Google Books: {stats['failed_google_books']}")
    logger.info(f"❌ Failed Open Library: {stats['failed_open_library']}")


def main():
    logger = Config.setup_logging()
    logger.info("=" * 60)
    logger.info("🚀 Worker: Starting job processing")

    supabase_client = Config.get_supabase_client()

    worker_stats = {
        "total_fetched": 0,
        "successful_google_books": 0,
        "successful_open_library": 0,
        "failed_google_books": 0,
        "failed_open_library": 0,
    }

    if not supabase_client:
        logger.error("🔴 Failed to connect to Supabase")
        sys.exit(1)

    response = (
        supabase_client.table("jobs")
        .select("title, author")
        .eq("status", "pending")
        .limit(Config.BATCH_SIZE)
        .execute()
    )  # response.data is a list of job dictionaries

    for job_data in response.data:
        worker_stats["total_fetched"] += 1

        google_books_data = GoogleBooksExtractor().extract(job_data)
        open_library_data = OpenLibraryExtractor().extract(job_data)

        if not google_books_data or not open_library_data:
            if not google_books_data:
                worker_stats["failed_google_books"] += 1
            if not open_library_data:
                worker_stats["failed_open_library"] += 1
            logger.error(
                f"🔴 Failed to fetch Google Books data for {job_data['title']} by {job_data['author']}"
            )

            # TODO: Update job status to failed (requeue)
            continue

        # Only reach here if BOTH APIs succeeded
        worker_stats["successful_google_books"] += 1
        worker_stats["successful_open_library"] += 1

    print_summary(logger, worker_stats)


if __name__ == "__main__":
    main()
