import sys

from config import Config
from logging import Logger
from typing import Dict, Optional
from extractors.google_books import GoogleBooksExtractor
from extractors.open_library import OpenLibraryExtractor
from models.job import JobStatus


def update_job_status(
    supabase_client,
    title: str,
    author: str,
    status: JobStatus,
    retry_count: Optional[int] = None,
    error_message: Optional[str] = None,
) -> bool:
    """
    Update job status by title and author (composite key).

    Args:
        supabase_client: Supabase client instance
        title: Book title
        author: Book author
        status: New status (JobStatus enum)
        retry_count: Updated retry count (optional)
        error_message: Error message if failed (optional)

    Returns:
        bool: True if update succeeded, False otherwise
    """
    try:
        update_payload = {
            "status": status.value,
            "updated_at": "now()",  # Supabase will handle this
        }

        if retry_count is not None:
            update_payload["retry_count"] = retry_count

        if error_message is not None:
            update_payload["error_message"] = error_message

        response = (
            supabase_client.table("jobs")
            .update(update_payload)
            .eq("title", title)
            .eq("author", author)
            .execute()
        )

        return len(response.data) > 0

    except Exception as e:
        logger = Config.setup_logging()
        logger.error(f"Failed to update job status for {title} by {author}: {str(e)}")
        return False


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

        google_books_data = GoogleBooksExtractor().extract(job_data)
        open_library_data = OpenLibraryExtractor().extract(job_data)

        # Check if both APIs succeeded
        if google_books_data and open_library_data:
            # Both APIs succeeded - set to processing
            logger.info(f"✅ Both APIs succeeded for {title} by {author}")
            worker_stats["successful_google_books"] += 1
            worker_stats["successful_open_library"] += 1

            if update_job_status(supabase_client, title, author, JobStatus.PROCESSING):
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
                error_msg = f"API extraction failed. Retry attempt {new_retry_count}/{max_retries}"

                if update_job_status(
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
                    logger.error(
                        f"❌ Failed to update retry count for {title} by {author}"
                    )

            else:
                # Max retries exceeded
                error_msg = f"API extraction failed after {max_retries} retry attempts"

                if update_job_status(
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

    print_summary(logger, worker_stats)


if __name__ == "__main__":
    main()
