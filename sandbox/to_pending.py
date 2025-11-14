"""
Supabase script to update job status to 'pending' by ISBN.

Usage:
    python sandbox/to_pending.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

# Setup logging
logger = Config.setup_logging()


def update_job_status_to_pending(isbn: str) -> None:
    """
    Update job status to 'pending' for a given ISBN using Supabase.

    Args:
        isbn (str): The ISBN identifier for the job to update
    """
    try:
        # Get Supabase client
        supabase = Config.get_supabase_client()

        # Update the job status
        response = (
            supabase.table("jobs")
            .update({"status": "pending"})
            .eq("isbn", isbn)
            .execute()
        )

        logger.info(f"✓ Successfully updated job with ISBN {isbn} to 'pending' status")
        logger.info(f"  Updated records: {len(response.data)}")

        if response.data:
            for record in response.data:
                logger.info(
                    f"  Job ID: {record.get('job_id')}, Title: {record.get('title')}"
                )

    except Exception as e:
        logger.error(f"✗ Error updating job status: {str(e)}")
        raise


if __name__ == "__main__":
    isbn = "9780063324534"
    logger.info(f"Updating job status to 'pending' for ISBN: {isbn}")
    update_job_status_to_pending(isbn)
    logger.info("Done!")
