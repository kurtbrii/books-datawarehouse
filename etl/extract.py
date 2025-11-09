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
    supabase_client: Client,
    job_data: Dict[str, Any],
) -> tuple[dict, dict]:
    """Extract book data from Google Books and Open Library APIs using ISBN."""
    job_id = job_data["job_id"]
    isbn = job_data["isbn"]
    retry_count = job_data.get("retry_count", 0)

    google_books_data = GoogleBooksExtractor().extract(logger, isbn)
    open_library_data = OpenLibraryExtractor().extract(logger, isbn)

    # Check if both APIs succeeded
    if google_books_data and open_library_data:
        # Both APIs succeeded - set to processing
        logger.info(f"✅ Both APIs succeeded for ISBN {isbn}")

        if update_job_status(
            logger, supabase_client, job_id, status=JobStatus.PROCESSING
        ):
            logger.info(f"✅ Updated ISBN {isbn} to processing status")
        else:
            logger.error(f"❌ Failed to update ISBN {isbn} to processing")

    else:
        # One or both APIs failed - handle retry logic
        if not google_books_data:
            logger.error(f"❌ Failed to fetch Google Books data for ISBN {isbn}")
        if not open_library_data:
            logger.error(f"❌ Failed to fetch Open Library data for ISBN {isbn}")

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
                job_id,
                status=JobStatus.PENDING,
                retry_count=new_retry_count,
                error_message=error_msg,
            ):
                logger.info(
                    f"🔄 Marked ISBN {isbn} for retry (attempt {new_retry_count}/{max_retries})"
                )
            else:
                logger.error(f"❌ Failed to update retry count for ISBN {isbn}")

        else:
            # Max retries exceeded
            error_msg = f"API extraction failed after {max_retries} retry attempts"

            if update_job_status(
                logger,
                supabase_client,
                job_id,
                status=JobStatus.FAILED,
                error_message=error_msg,
            ):
                logger.error(
                    f"❌ Permanently failed ISBN {isbn} (exceeded max retries)"
                )
            else:
                logger.error(f"❌ Failed to mark ISBN {isbn} as failed")

    return google_books_data, open_library_data
