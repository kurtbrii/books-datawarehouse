"""
Publisher module for the books data pipeline.

Reads book data from CSV file, validates the data, detects duplicates,
and creates job records in the jobs table with status='pending'.
"""

import csv
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from logging import Logger
from supabase import Client as SupabaseClient
from config import Config
from models.job import JobCreate


def validate_row(
    row: Dict[str, str], row_num: int, logger: Logger
) -> tuple[bool, Optional[str]]:
    """
    Validate a CSV row for required fields.

    Args:
        row: Dictionary containing CSV row data
        row_num: Row number for error reporting
        logger: Logger instance for error logging

    Returns:
        Tuple of (is_valid, error_message)
    """
    title = row.get("Title", "").strip()
    author = row.get("Author", "").strip()

    if not title:
        error_msg = f"Row {row_num}: Missing or empty title"
        logger.warning(f"📚 {error_msg}")
        return False, error_msg

    if not author:
        error_msg = f"Row {row_num}: Missing or empty author"
        logger.warning(f"👤 {error_msg}")
        return False, error_msg

    return True, None


def check_duplicate_title_author(
    supabase_client, title: str, author: str, logger
) -> bool:
    """
    Check if a job with the given ISBN already exists.

    Args:
        supabase_client: Supabase client instance
        isbn: ISBN to check (can be None)
        logger: Logger instance

    Returns:
        True if duplicate exists, False otherwise
    """
    if not title or not author:
        return False

    try:
        response = (
            supabase_client.table("jobs")
            .select("*")
            .eq("title", title)
            .eq("author", author)
            .execute()
        )
        return len(response.data) > 0
    except Exception as e:
        logger.error(
            f"🔍 Error checking for duplicate title {title} and author {author}: {e}"
        )
        # If we can't check, assume not duplicate to allow processing
        return False


def read_csv_file(file_path: str, logger: Logger) -> tuple[list, Optional[str]]:
    """
    Read and parse CSV file with flexible column detection.

    Args:
        file_path: Path to CSV file
        logger: Logger instance

    Returns:
        Tuple of (list of row dictionaries, error_message if any)
    """
    try:
        csv_path = Path(file_path)
        if not csv_path.exists():
            error_msg = f"CSV file not found: {file_path}"
            logger.error(f"📄 {error_msg}")
            return [], error_msg

        if not csv_path.is_file():
            error_msg = f"Path is not a file: {file_path}"
            logger.error(f"📄 {error_msg}")
            return [], error_msg

    except Exception as e:
        error_msg = f"Error accessing CSV file: {e}"
        logger.error(f"📄 {error_msg}")
        return [], error_msg

    rows = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames

            if not fieldnames:
                error_msg = "CSV file is empty or has no header row"
                logger.error(f"📄 {error_msg}")
                return [], error_msg

            # Read and normalize rows
            for row_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 (header is row 1)
                rows.append(row)

            return rows, None

    except UnicodeDecodeError as e:
        error_msg = f"CSV file encoding error: {e}"
        logger.error(f"📄 {error_msg}")
        return [], error_msg
    except csv.Error as e:
        error_msg = f"CSV parsing error: {e}"
        logger.error(f"📄 {error_msg}")
        return [], error_msg
    except Exception as e:
        error_msg = f"Unexpected error reading CSV file: {e}"
        logger.error(f"📄 {error_msg}")
        return [], error_msg


def create_job(supabase_client: SupabaseClient, job_data: JobCreate, logger) -> bool:
    """
    Create a job record in the database.

    Args:
        supabase_client: Supabase client instance
        job_data: JobCreate model instance
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Add status='pending' as required by database schema
        job_dict = job_data.model_dump(mode="json")
        job_dict["status"] = "pending"

        supabase_client.table("jobs").insert(job_dict).execute()
        return True
    except Exception as e:
        error_msg = f"Database error creating job: {e}"
        logger.error(f"💾 {error_msg}")
        return False


def print_summary(logger: Logger, stats: Dict[str, int]) -> None:
    """
    Print a summary of the processing results.

    Args:
        logger: Logger instance
        stats: Dictionary containing processing statistics
    """
    # Print summary
    logger.info("=" * 60)
    logger.info("📊 Publisher: Processing complete")
    logger.info("=" * 60)
    logger.info(f"📈 Total rows processed: {stats['total_processed']}")
    logger.info(f"✅ Jobs created: {stats['jobs_created']}")
    logger.info(f"🔄 Duplicates skipped: {stats['duplicates_skipped']}")
    logger.info(f"❌ Validation errors: {stats['validation_errors']}")
    logger.info(f"💾 Database errors: {stats['database_errors']}")

    # Exit with error code if there were critical failures
    if stats["database_errors"] > 0:
        logger.error("💾 Some jobs failed to be created due to database errors")
        sys.exit(1)

    if stats["validation_errors"] == stats["total_processed"]:
        logger.error("⚠️  All rows failed validation")
        sys.exit(1)


def main():
    """Main entry point for the publisher script."""
    # Setup logging
    logger = Config.setup_logging()
    logger.info("=" * 60)
    logger.info("🚀 Publisher: Starting CSV to Jobs ETL process")
    logger.info("=" * 60)

    # Get configuration
    csv_file_path = os.getenv("CSV_FILE_PATH", "data/curated_books.csv")
    logger.info(f"📂 CSV file path: {csv_file_path}")

    # Initialize statistics
    stats = {
        "total_processed": 0,
        "jobs_created": 0,
        "duplicates_skipped": 0,
        "validation_errors": 0,
        "database_errors": 0,
    }

    try:
        # Get Supabase client
        try:
            supabase_client = Config.get_supabase_client()
            logger.info("🔗 Database connection established")
        except Exception as e:
            logger.error(f"🔌 Failed to connect to database: {e}")
            sys.exit(1)

        # Read CSV file
        rows, error = read_csv_file(csv_file_path, logger)
        if error:
            logger.error(f"📄 Failed to read CSV file: {error}")
            sys.exit(1)

        if not rows:
            logger.warning("📭 CSV file contains no data rows")
            sys.exit(0)

        logger.info(f"📋 Found {len(rows)} row(s) to process")

        # Process each row
        for row_num, row_data in enumerate(rows, start=2):
            stats["total_processed"] += 1

            # Validate row
            is_valid, validation_error = validate_row(row_data, row_num, logger)
            if not is_valid:
                stats["validation_errors"] += 1
                continue

            # Extract and clean data
            title = row_data["Title"].strip()
            author = row_data["Author"].strip()
            isbn = row_data.get("ISBN", "").strip() or None

            # Check for duplicates (if title and author are provided)
            if (
                title
                and author
                and check_duplicate_title_author(supabase_client, title, author, logger)
            ):
                logger.warning(
                    f"🔁 Row {row_num}: Skipping duplicate title '{title}' and author '{author}'"
                    f"(Title: {title}, Author: {author})"
                )
                stats["duplicates_skipped"] += 1
                continue

            # Create job
            job_data = JobCreate(
                title=title,
                author=author,
                isbn=isbn,
            )

            success = create_job(supabase_client, job_data, logger)
            if success:
                logger.info(
                    f"✅ Row {row_num}: Created job for '{title}' by {author} "
                    f"(ISBN: {isbn or 'N/A'})"
                )
                stats["jobs_created"] += 1
            else:
                stats["database_errors"] += 1

    except KeyboardInterrupt:
        logger.warning("⏸️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in main process: {e}", exc_info=True)
        sys.exit(1)

    print_summary(logger, stats)
    logger.info("✨ Publisher: Completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
