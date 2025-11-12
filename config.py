"""
Configuration module for the books data pipeline.

This module handles loading and managing configuration from environment variables,
supporting both .env files and system environment variables.
"""

import os

from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from rich.logging import RichHandler
from rich.console import Console

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the books data pipeline."""

    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

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

    LANGUAGE_CODE_MAP = {
        "eng": "en",
        "fre": "fr",
        "fra": "fr",  # French has two 3-letter codes
        "spa": "es",
        "ger": "de",
        "deu": "de",  # German has two codes
        "ita": "it",
        "por": "pt",
        "rus": "ru",
        "jpn": "ja",
        "chi": "zh",
        "zho": "zh",  # Chinese has two codes
        "kor": "ko",
        "ara": "ar",
        "pol": "pl",
        "dut": "nl",
        "nld": "nl",  # Dutch has two codes
        "heb": "he",
        "gre": "el",
        "ell": "el",  # Greek has two codes
        "tur": "tr",
        "swe": "sv",
        "dan": "da",
        "nor": "no",
        "fin": "fi",
        "ces": "cs",  # Czech
        "hun": "hu",
        "ron": "ro",  # Romanian
        "tha": "th",
        "vie": "vi",
        "ind": "id",  # Indonesian
        "msa": "ms",  # Malay
        "hin": "hi",
        "ben": "bn",
        "urd": "ur",
        "per": "fa",
        "fas": "fa",  # Persian has two codes
    }

    @classmethod
    def get_connection_string(cls):
        """
        Get the database connection string.

        Returns a full PostgreSQL connection string prioritizing DATABASE_URL
        over individual connection components.

        Returns:
            str: PostgreSQL connection string
        """
        if cls.SUPABASE_URL:
            return cls.SUPABASE_URL

        return None

    @classmethod
    def get_supabase_client(cls) -> Client:
        """
        Get a Supabase client instance.

        Returns:
            Client: Configured Supabase client
        """
        if not cls.SUPABASE_URL or not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required"
            )
        return create_client(cls.SUPABASE_URL, cls.SUPABASE_SERVICE_ROLE_KEY)

    @classmethod
    def setup_logging(cls):
        """Configure colored logging using Rich."""
        console = Console()

        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL.upper()),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[
                RichHandler(
                    console=console,
                    rich_tracebacks=True,
                    show_path=True,
                    show_time=True,
                )
            ],
        )

        # Suppress HTTP request logging from httpx/httpcore to avoid exposing sensitive URLs
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
        logging.getLogger("httpcore.http2").setLevel(logging.WARNING)

        return logging.getLogger(__name__)
