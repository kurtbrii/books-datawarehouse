from config import Config
from logging import Logger
from models.job import JobStatus
from typing import Optional


def update_job_status(
    logger: Logger,
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
