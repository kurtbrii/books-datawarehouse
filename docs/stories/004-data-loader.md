# 004: Data Loader

## Overview
Build the data loading layer that inserts transformed book data into all dimension tables, bridge tables, and fact table. Implement transaction management, constraint handling, and upsert logic for idempotent operations.

## Dependencies
- Depends on: 001-project-setup-and-database-schema, 003-etl-pipeline-core

## Blocks
- 005-analytics-and-testing

## Acceptance Criteria
- [ ] `loader.py` created with modular functions for each table type
- [ ] Loader handles dimension table inserts with deduplication (publishers, authors, genres)
- [ ] Loader manages ISBN-based insertions into dim_books
- [ ] Loader creates entries in bridge tables (book_author, book_genre)
- [ ] Loader inserts metrics into fact_book_metrics
- [ ] Upsert logic prevents duplicate dimension records (publisher name, author ol_key, genre name)
- [ ] Transaction management ensures all-or-nothing inserts per job
- [ ] Rollback on constraint violations (FK, UNIQUE)
- [ ] Foreign key resolution before inserting fact records
- [ ] Handles missing dimensions gracefully (creates NULL-safe relationships)
- [ ] Deduplication using Open Library keys for authors
- [ ] Proper handling of date dimension foreign keys (YYYYMMDD format)
- [ ] Job status updated to 'completed' after successful load
- [ ] Error details captured for failed loads

## Technical Details

### Files to Create/Modify
- `loader.py` - Database loader with transaction management

### Loader Functions
```python
def load_book_data(job, transformed_data, db_connection):
    # Main orchestrator
    # Returns: True/False with error message
    
def upsert_publisher(publisher_name, db_connection):
    # Get or create publisher, return publisher_id
    
def upsert_author(author_data, db_connection):
    # Get or create author, return author_id
    
def upsert_genre(genre_name, db_connection):
    # Get or create genre, return genre_id
    
def insert_book(book_data, publisher_id, db_connection):
    # Insert into dim_books
    
def link_book_authors(isbn, author_ids, db_connection):
    # Insert into book_author_bridge
    
def link_book_genres(isbn, genre_ids, db_connection):
    # Insert into book_genre_bridge
    
def insert_metrics(isbn, metrics_data, snapshot_date_key, db_connection):
    # Insert into fact_book_metrics
```

### Transaction Strategy
```
BEGIN TRANSACTION
  1. Upsert publishers
  2. Upsert authors and genres
  3. Insert book record
  4. Create book-author relationships
  5. Create book-genre relationships
  6. Insert metrics record
  7. Update job status to 'completed'
COMMIT or ROLLBACK on error
```

### Constraint Handling
- UNIQUE constraints: Use "ON CONFLICT" if supported, otherwise check before insert
- FOREIGN KEY constraints: Validate all references before insert
- CHECK constraints: Validate ranges (ratings 0-5, positive page counts)
- Deduplication: Use ol_author_key for authors, name for publishers/genres

### Date Dimension Integration
- Convert published_date to YYYYMMDD key format
- If date doesn't exist in dim_date, create it (or handle gracefully)
- Support NULL dates for books without publication date

## Implementation Notes
- Use psycopg2 connection context managers for proper transaction handling
- Batch inserts where possible for performance
- Log each insert operation for debugging
- Handle edge cases: NULL values, special characters in names
- Implement dry-run mode for testing
- Consider adding performance metrics (inserts per second)

## Testing Requirements
- Unit test: Upsert logic with existing and new records
- Unit test: Transaction rollback on constraint violations
- Unit test: FK validation before insert
- Integration test: Load complete transformed record through all tables
- Integration test: Verify bridge table relationships
- Manual test: Load 50-100 books and verify data integrity
- Constraint test: Verify UNIQUE constraints prevent duplicates

## Estimated Effort
**Large** (6-8 hours)

