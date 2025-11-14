import sys
import time
from logging import Logger

from typing import Dict

from config import Config
from models.job import JobStatus
from etl.extract import Extractor
from etl.transform import Transformer
from etl.load import Loader


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

    try:
        supabase_client = Config.get_supabase_client()
    except Exception as e:
        logger.error(f"🔴 Failed to connect to Supabase: {e}")
        sys.exit(1)

    response = (
        supabase_client.table("jobs")
        .select("job_id, isbn, retry_count")
        .eq("status", JobStatus.PENDING.value)
        .limit(Config.BATCH_SIZE)
        .execute()
    )  # response.data is a list of job dictionaries

    for job_data in response.data:
        worker_stats["total_fetched"] += 1
        job_id = job_data["job_id"]
        isbn = job_data["isbn"]
        retry_count = job_data.get("retry_count", 0)

        logger.info(
            f"Processing job {job_id}: ISBN {isbn} (retry_count: {retry_count})"
        )

        # ! extraction phase
        # extract the raw json data from the APIs
        google_books_data, open_library_data = Extractor().extract_book_data(
            logger, supabase_client, job_data
        )

        if not google_books_data or not open_library_data:
            logger.error(f"❌ Failed to extract data for ISBN {isbn}")
            continue

        # ! transform independent dimensions and book dimension
        independent_dimensions = Transformer().transform_independent_dimensions(
            logger, google_books_data, open_library_data
        )

        book_dimension = Transformer().transform_book_data(
            google_books_data, open_library_data
        )

        # ! load independent dimensions
        dims_pk_id = Loader().load_independent_dimensions(
            logger, independent_dimensions
        )

        # ! load dim_books
        dim_book_isbn = Loader().load_dim_books(
            logger,
            metadata={
                "isbn": isbn,
                **book_dimension,
                "publisher_id": dims_pk_id["dim_publisher"][0],
                "published_date_key": dims_pk_id["dim_date"][0],
            },
        )

        # ! load the bridge tables
        # author bridge table
        Loader().load_bridge_tables(
            logger,
            "book_author_bridge",
            dim_book_isbn,
            dims_pk_id["dim_author"],
            "author",
        )

        # genre bridge table
        Loader().load_bridge_tables(
            logger,
            "book_genre_bridge",
            dim_book_isbn,
            dims_pk_id["dim_genre"],
            "genre",
        )

    print_summary(logger, worker_stats)


if __name__ == "__main__":
    main()
