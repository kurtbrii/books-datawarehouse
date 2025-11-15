from typing import Dict, Any

from extractors.google_books import GoogleBooksExtractor
from extractors.open_library import OpenLibraryExtractor
from models.job import JobStatus
from helpers.utils import update_job_status
from config import Config

from logging import Logger
from supabase import Client


class Extractor:
    """Extract book data from multiple APIs and handle retry logic."""

    @staticmethod
    def extract_book_data(
        logger: Logger,
        supabase_client: Client,
        job_data: Dict[str, Any],
    ) -> tuple[dict, dict]:
        """
        Extract book data from Google Books and Open Library APIs using ISBN.

        Args:
            logger: Logger instance for audit trail
            supabase_client: Supabase client for database operations
            job_data: Job data containing job_id, isbn, and retry_count

        Returns:
            Tuple of (google_books_data, open_library_data) dictionaries
        """
        job_id = job_data["job_id"]
        isbn = job_data["isbn"]
        retry_count = job_data.get("retry_count", 0)

        # Call extractors directly - they don't maintain state
        google_books_data = GoogleBooksExtractor().extract(logger, isbn)
        open_library_data = OpenLibraryExtractor().extract(logger, isbn)

        # Check if both APIs succeeded
        if google_books_data or open_library_data:
            Extractor._handle_success(logger, supabase_client, job_id, isbn)
        else:
            Extractor._handle_failure(
                logger,
                supabase_client,
                job_id,
                isbn,
                retry_count,
                google_books_data,
                open_library_data,
            )

        return google_books_data, open_library_data

    @staticmethod
    def _handle_success(
        logger: Logger, supabase_client: Client, job_id: str, isbn: str
    ) -> None:
        """Handle successful extraction from both APIs."""
        logger.info(f"✅ Both APIs succeeded for ISBN {isbn}")

        if update_job_status(
            logger, supabase_client, job_id, status=JobStatus.PROCESSING
        ):
            logger.info(f"✅ Updated ISBN {isbn} to processing status")
        else:
            logger.error(f"❌ Failed to update ISBN {isbn} to processing")

    @staticmethod
    def _handle_failure(
        logger: Logger,
        supabase_client: Client,
        job_id: str,
        isbn: str,
        retry_count: int,
        google_books_data: Dict,
        open_library_data: Dict,
    ) -> None:
        """Handle failed extraction with retry logic."""
        # Log which APIs failed
        if not google_books_data:
            logger.error(f"❌ Failed to fetch Google Books data for ISBN {isbn}")
        if not open_library_data:
            logger.error(f"❌ Failed to fetch Open Library data for ISBN {isbn}")

        # Determine if we should retry or mark as failed
        max_retries = Config.RETRY_MAX_ATTEMPTS
        if retry_count < max_retries:
            Extractor._mark_for_retry(
                logger, supabase_client, job_id, isbn, retry_count, max_retries
            )
        else:
            Extractor._mark_as_failed(
                logger, supabase_client, job_id, isbn, max_retries
            )

    @staticmethod
    def _mark_for_retry(
        logger: Logger,
        supabase_client: Client,
        job_id: str,
        isbn: str,
        retry_count: int,
        max_retries: int,
    ) -> None:
        """Mark a job for retry."""
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

    @staticmethod
    def _mark_as_failed(
        logger: Logger,
        supabase_client: Client,
        job_id: str,
        isbn: str,
        max_retries: int,
    ) -> None:
        """Mark a job as permanently failed."""
        error_msg = f"API extraction failed after {max_retries} retry attempts"

        if update_job_status(
            logger,
            supabase_client,
            job_id,
            status=JobStatus.FAILED,
            error_message=error_msg,
        ):
            logger.error(f"❌ Permanently failed ISBN {isbn} (exceeded max retries)")
        else:
            logger.error(f"❌ Failed to mark ISBN {isbn} as failed")
