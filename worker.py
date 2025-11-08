import sys

from typing import Dict
from config import Config
from models.job import JobStatus
from etl.extract import extract_book_data

from logging import Logger


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
    logger.info(f"🔄 Marked for retry: {stats['jobs_marked_for_retry']}")
    logger.info(f"❌ Permanently failed: {stats['jobs_permanently_failed']}")
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
        "jobs_marked_for_retry": 0,
        "jobs_permanently_failed": 0,
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
        .select("title, author, retry_count")
        .eq("status", JobStatus.PENDING.value)
        .limit(Config.BATCH_SIZE)
        .execute()
    )  # response.data is a list of job dictionaries

    for job_data in response.data:
        worker_stats["total_fetched"] += 1
        title = job_data["title"]
        author = job_data["author"]
        retry_count = job_data.get("retry_count", 0)

        logger.info(f"Processing job: {title} by {author} (retry_count: {retry_count})")
        worker_stats, google_books_data, open_library_data = extract_book_data(
            logger, worker_stats, supabase_client, job_data
        )

    print_summary(logger, worker_stats)


if __name__ == "__main__":
    main()
