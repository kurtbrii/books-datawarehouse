import json
from datetime import datetime
from typing import Dict, Any, Optional

from transformers.date_transformer import DateTransformer

from logging import Logger


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

    # print(json.dumps(google_books_data, indent=2))
    # print("\n" + "=" * 60 + "\n")
    # print(json.dumps(open_library_data, indent=2))

    google_books_book_info: dict = google_books_data.get("items", [{}])[0].get(
        "volumeInfo", {}
    )

    open_library_book_info: dict = open_library_data.get("docs", [{}])[0]

    date_dimension: dict = DateTransformer().extract_date_dimension(
        google_books_book_info.get("publishedDate"), logger
    )

    return {
        "isbn": google_books_data.get("isbn", open_library_data.get("isbn")),
    }
