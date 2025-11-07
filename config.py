"""
Configuration module for the books data pipeline.

This module handles loading and managing configuration from environment variables,
supporting both .env files and system environment variables.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the books data pipeline."""

    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")

    OPEN_LIBRARY_BASE_URL = os.getenv(
        "OPEN_LIBRARY_BASE_URL", "https://openlibrary.org"
    )
    GOOGLE_BOOKS_BASE_URL = os.getenv(
        "GOOGLE_BOOKS_BASE_URL", "https://www.googleapis.com/books/v1"
    )

    # Application configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))

    @classmethod
    def get_connection_string(cls):
        """
        Get the database connection string.

        Returns a full PostgreSQL connection string prioritizing DATABASE_URL
        over individual connection components.

        Returns:
            str: PostgreSQL connection string
        """
        if cls.DATABASE_URL:
            return cls.DATABASE_URL

        return None
