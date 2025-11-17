from supabase import Client
from logging import Logger
from models.job import JobStatus
from typing import Optional


def get_id_name(dim_name: str) -> str:
    ID_NAME_MAP = {
        "dim_date": "date_key",
        "dim_publisher": "publisher_id",
        "dim_author": "author_id",
        "dim_genre": "genre_id",
    }
    return ID_NAME_MAP.get(dim_name, None)


def update_job_status(
    logger: Logger,
    supabase_client: Client,
    job_id: int,
    status: JobStatus,
    retry_count: Optional[int] = None,
    error_message: Optional[str] = None,
) -> bool:
    """
    Update job status by job_id (primary key).

    Args:
        logger: Logger instance
        supabase_client: Supabase client instance
        job_id: Unique job identifier
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

        # Only include retry_count if explicitly provided
        if retry_count is not None:
            update_payload["retry_count"] = retry_count

        # Only include error_message if explicitly provided
        if error_message is not None:
            update_payload["error_message"] = error_message

        response = (
            supabase_client.table("jobs")
            .update(update_payload)
            .eq("job_id", job_id)
            .execute()
        )

        return len(response.data) > 0

    except Exception as e:
        logger.error(f"Failed to update job status for job_id {job_id}: {str(e)}")
        return False
