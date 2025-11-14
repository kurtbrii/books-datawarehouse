"""
Transformation Order:

Phase 1: Independent Dimensions (no dependencies)
1. dim_date - Date dimension (referenced by dim_books and fact_book_metrics)
2. dim_publisher - Publisher dimension
3. dim_author - Author dimension
4. dim_genre - Genre dimension

Phase 2: Dependent Dimensions
5. dim_books - References dim_publisher and dim_date

Phase 3: Bridge Tables (many-to-many relationships)
6. book_author_bridge - References dim_books and dim_author
7. book_genre_bridge - References dim_books and dim_genre

Phase 4: Fact Table
8. fact_book_metrics - References dim_books and dim_date
"""

from typing import Dict, Any, Optional
from logging import Logger

from transformers.date_transformer import DateTransformer
from transformers.publisher_transformer import PublisherTransformer
from transformers.author_transformer import AuthorTransformer
from transformers.genre_transformer import GenreTransformer
from transformers.book_transformer import BookTransformer


class Transformer:
    """Transform and merge raw book data from multiple API sources."""

    @staticmethod
    def _extract_api_data(
        google_books_data: Optional[Dict[str, Any]],
        open_library_data: Optional[Dict[str, Any]],
    ) -> tuple[dict, dict, dict]:
        """
        Extract structured data from raw API responses.

        Args:
            google_books_data: Raw extracted data from Google Books API
            open_library_data: Raw extracted data from Open Library API

        Returns:
            Tuple of (gb_book_info, gb_general_info, ol_general_info)
        """
        # gb = Google Books
        gb_general_info: dict = google_books_data.get("items", [{}])[0]
        gb_book_info: dict = gb_general_info.get("volumeInfo", {})

        # ol = Open Library
        ol_general_info: dict = open_library_data.get("docs", [{}])[0]

        return gb_book_info, gb_general_info, ol_general_info

    @staticmethod
    def transform_independent_dimensions(
        logger: Logger,
        google_books_data: Optional[Dict[str, Any]],
        open_library_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Transform and merge raw book data from multiple API sources.

        Takes extracted data from Google Books and Open Library APIs, cleans it,
        resolves conflicts between sources, and produces a unified standardized format
        for warehouse loading.

        Args:
            logger: Logger instance for audit trail and debugging
            google_books_data: Raw extracted data from Google Books API
            open_library_data: Raw extracted data from Open Library API
        """

        gb_book_info, _, ol_general_info = Transformer._extract_api_data(
            google_books_data, open_library_data
        )

        # Call static methods directly on transformer classes
        date_dimension: dict = DateTransformer.transform_date_attributes(
            gb_book_info, logger
        )

        publisher_dimension: dict = PublisherTransformer.transform_publisher_attributes(
            gb_book_info
        )

        author_dimension: dict = AuthorTransformer.merge_author_sources(
            gb_book_info, ol_general_info
        )

        genre_dimension: dict = GenreTransformer.transform_genre(gb_book_info)

        return {
            "dim_date": date_dimension,
            "dim_publisher": publisher_dimension,
            "dim_author": author_dimension,
            "dim_genre": genre_dimension,
        }

    @staticmethod
    def transform_book_data(
        google_books_data: Optional[Dict[str, Any]],
        open_library_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Transform book data from multiple API sources.

        Args:
            gb_book_info: Raw extracted data from Google Books API
            gb_general_info: Raw extracted data from Google Books API
            ol_general_info: Raw extracted data from Open Library API
        """
        gb_book_info, gb_general_info, ol_general_info = Transformer._extract_api_data(
            google_books_data, open_library_data
        )

        book_dimension: dict = BookTransformer.transform_book(
            gb_book_info, gb_general_info, ol_general_info
        )

        return book_dimension
