"""
This is the worker script that processes the jobs, transforms the data,
and loads it into the warehouse.
"""

import sys
import time
from logging import Logger
from typing import Dict

from config import Config
from etl.extract import Extractor
from etl.load import Loader
from etl.transform import Transformer
from helpers.utils import update_job_status
from models.job import JobStatus


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
    """Run the worker pipeline: fetch jobs, execute ETL phases, and update stats."""
    logger = Config.setup_logging()
    logger.info("=" * 60)
    logger.info("🚀 Worker: Starting job processing")

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
    except (ValueError, ConnectionError) as e:
        logger.error("🔴 Failed to connect to Supabase: %s", e)
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
            "Processing job %s: ISBN %s (retry_count: %s)",
            job_id,
            isbn,
            retry_count,
        )

        try:
            # ! extraction phase
            logger.info("=" * 60)
            logger.info("📥 EXTRACTION PHASE")
            logger.info("=" * 60)

            # extract the raw json data from the APIs
            google_books_data, open_library_data = Extractor().extract_book_data(
                logger, supabase_client, job_data
            )

            if not google_books_data and not open_library_data:
                raise ValueError(f"Failed to extract data for ISBN {isbn}")

            # ! transform phase
            logger.info("=" * 60)
            logger.info("🔄 TRANSFORMATION PHASE")
            logger.info("=" * 60)

            independent_dimensions = Transformer().transform_independent_dimensions(
                logger, google_books_data, open_library_data
            )

            book_dimension = Transformer().transform_book_data(
                logger, google_books_data, open_library_data
            )

            fact_book_metrics = Transformer().transform_fact_book_metrics(
                logger, google_books_data, open_library_data
            )

            # ! load phase
            logger.info("=" * 60)
            logger.info("💾 LOADING PHASE")
            logger.info("=" * 60)

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

            # ! load fact_book_metrics
            Loader().load_fact_table(
                logger=logger,
                fact_table_name="fact_book_metrics",
                metadata={
                    **fact_book_metrics,
                    "snapshot_date_key": dims_pk_id["dim_date"][0],
                    "isbn": dim_book_isbn,
                },
            )

            # ! commit: update job status to completed
            logger.info("=" * 60)
            logger.info("✅ JOB COMPLETION")
            logger.info("=" * 60)
            update_job_status(
                logger,
                supabase_client,
                job_id,
                JobStatus.COMPLETED,
                retry_count=retry_count,  # Keep the current retry count
            )
            logger.info("✅ Job %s completed successfully for ISBN %s", job_id, isbn)

        except (ValueError, KeyError, IndexError, TypeError) as e:
            # ! rollback: handle job failure with retry logic
            logger.error("❌ Job %s processing failed: %s", job_id, str(e))

            # Determine if we should retry or mark as permanently failed
            if retry_count < Config.RETRY_MAX_ATTEMPTS:
                new_retry_count = retry_count + 1
                error_msg = f"Processing failed (attempt {new_retry_count}/{Config.RETRY_MAX_ATTEMPTS}): {str(e)}"

                update_job_status(
                    logger,
                    supabase_client,
                    job_id,
                    JobStatus.PENDING,
                    retry_count=new_retry_count,
                    error_message=error_msg,
                )
                logger.info(
                    "🔄 Marked job %s for retry (attempt %s/%s)",
                    job_id,
                    new_retry_count,
                    Config.RETRY_MAX_ATTEMPTS,
                )
                worker_stats["jobs_marked_for_retry"] += 1
            else:
                error_msg = f"Processing failed after {Config.RETRY_MAX_ATTEMPTS} retry attempts: {str(e)}"

                update_job_status(
                    logger,
                    supabase_client,
                    job_id,
                    JobStatus.FAILED,
                    error_message=error_msg,
                    retry_count=Config.RETRY_MAX_ATTEMPTS,
                )
                logger.error(
                    "❌ Job %s permanently failed for ISBN %s (exceeded max retries)",
                    job_id,
                    isbn,
                )
                worker_stats["jobs_permanently_failed"] += 1

    print_summary(logger, worker_stats)


if __name__ == "__main__":
    main()
