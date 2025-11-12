import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging import Logger

from transformers.date_transformer import DateTransformer
from transformers.publisher_transformer import PublisherTransformer
from transformers.author_transformer import AuthorTransformer


def transform_book_data(
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

    Returns:
        Dict containing merged, cleaned book data ready for warehouse loading:

        ```json
        {
            'book': {
                'isbn': '9780525555353',
                'title': 'Turtles All the Way Down',
                'description': '...',
                'page_count': 306,
                'language': 'en',
                'published_date': '2017-10-10',
                'cover_image_id': None,
                'work_key': '/works/OL17842319W'
            },
            'authors': [
                {
                    'name': 'John Green',
                    'ol_author_key': 'OL5046634A'
                }
            ],
            'publisher': {
                'name': 'Penguin'
            },
            'genres': [
                {'genre_name': 'Young Adult Fiction'}
            ],
            'metrics': {
                'rating_avg': 4.0,
                'rating_count': 6,
                'edition_count': 23,
                'list_price_amount': 790.43,
                'retail_price_amount': 537.49,
                'currency_code': 'PHP',
                'is_ebook_available': True,
                'saleability_status': 'FOR_SALE'
            }
        }
        ```
    """

    # TRANSFORMATION ORDER: Load in this sequence to respect foreign key dependencies
    """
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

    # gb = Google Books
    gb_general_info: dict = google_books_data.get("items", [{}])[0]
    gb_book_info: dict = gb_general_info.get("volumeInfo", {})

    # ol = Open Library
    ol_general_info: dict = open_library_data.get("docs", [{}])[0]

    date_dimension: dict = DateTransformer().transform_date_attributes(
        gb_book_info, logger
    )

    publisher_dimension: dict = PublisherTransformer().transform_publisher_attributes(
        gb_book_info
    )

    # print(publisher_dimension)
    # print(date_dimension)

    author_dimension: dict = AuthorTransformer().merge_author_sources(
        gb_book_info, ol_general_info
    )

    return {
        "isbn": google_books_data.get("isbn", open_library_data.get("isbn")),
    }
