from typing import Dict, Any

from extractors.google_books import GoogleBooksExtractor
from extractors.open_library import OpenLibraryExtractor
from models.job import JobStatus
from helpers.utils import update_job_status
from config import Config

from logging import Logger
from supabase import Client


def extract_book_data(
    logger: Logger,
    worker_stats: Dict[str, int],
    supabase_client: Client,
    job_data: Dict[str, Any],
) -> tuple[Dict[str, int], dict, dict]:
    title = job_data["title"]
    author = job_data["author"]
    retry_count = job_data.get("retry_count", 0)

    google_books_data = GoogleBooksExtractor().extract(logger, title, author)
    open_library_data = OpenLibraryExtractor().extract(logger, title, author)

    # TODO: add pydantic validation: do not proceed with transformation if data is not valid
    # TODO: remove worker_stats (updating of worker_stats is done after loading to database, after everything is finished)

    # Check if both APIs succeeded
    if google_books_data and open_library_data:
        # Both APIs succeeded - set to processing
        logger.info(f"✅ Both APIs succeeded for {title} by {author}")
        worker_stats["successful_google_books"] += 1
        worker_stats["successful_open_library"] += 1

        if update_job_status(
            logger, supabase_client, title, author, JobStatus.PROCESSING
        ):
            logger.info(f"✅ Updated {title} by {author} to processing status")
        else:
            logger.error(f"❌ Failed to update {title} by {author} to processing")

    else:
        # One or both APIs failed - handle retry logic
        if not google_books_data:
            worker_stats["failed_google_books"] += 1
            logger.error(
                f"❌ Failed to fetch Google Books data for {title} by {author}"
            )
        if not open_library_data:
            worker_stats["failed_open_library"] += 1
            logger.error(
                f"❌ Failed to fetch Open Library data for {title} by {author}"
            )

        # Determine if we should retry or mark as failed
        max_retries = Config.RETRY_MAX_ATTEMPTS
        if retry_count < max_retries:
            # Can still retry
            new_retry_count = retry_count + 1
            error_msg = (
                f"API extraction failed. Retry attempt {new_retry_count}/{max_retries}"
            )

            if update_job_status(
                logger,
                supabase_client,
                title,
                author,
                JobStatus.PENDING,
                retry_count=new_retry_count,
                error_message=error_msg,
            ):
                worker_stats["jobs_marked_for_retry"] += 1
                logger.info(
                    f"🔄 Marked {title} by {author} for retry (attempt {new_retry_count}/{max_retries})"
                )
            else:
                logger.error(f"❌ Failed to update retry count for {title} by {author}")

        else:
            # Max retries exceeded
            error_msg = f"API extraction failed after {max_retries} retry attempts"

            if update_job_status(
                logger,
                supabase_client,
                title,
                author,
                JobStatus.FAILED,
                error_message=error_msg,
            ):
                worker_stats["jobs_permanently_failed"] += 1
                logger.error(
                    f"❌ Permanently failed {title} by {author} (exceeded max retries)"
                )
            else:
                logger.error(f"❌ Failed to mark {title} by {author} as failed")

    return worker_stats, google_books_data, open_library_data
