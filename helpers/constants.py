CONFLICT_COLUMNS = {
    "dim_date": "date_key",
    "dim_publisher": "name",
    "dim_author": "ol_author_key",  # Note: Only works when ol_author_key is NOT NULL
    "dim_genre": "genre_name",
    "dim_books": "isbn",
    "fact_book_metrics": "isbn,snapshot_date_key",
}
