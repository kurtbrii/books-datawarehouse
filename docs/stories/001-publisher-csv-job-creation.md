# Publisher: CSV Reading & Job Creation

## Overview
Implement the `publisher.py` module that reads book data from a CSV file, validates the data, detects duplicates, and creates job records in the `jobs` table with status='pending'. This is the entry point for the entire ETL pipeline.

## Dependencies
- Depends on: Database schema must be created (jobs table)
- Blocks: 002-worker-etl-orchestration

## Acceptance Criteria
- [ ] `publisher.py` reads `data/curated_books.csv` with columns: title, author, ISBN
- [ ] Data validation ensures required fields (title, author) are present and formatted correctly
- [ ] Invalid rows are skipped and validation errors are logged
- [ ] Duplicate detection prevents creating jobs for books with identical ISBNs
- [ ] For each valid book, a job record is created in the `jobs` table with:
  - `title`: Book title from CSV
  - `author`: Book author from CSV
  - `isbn`: Optional ISBN identifier
  - `status`: 'pending' (ready for processing)
  - `created_at`: Job creation timestamp
  - `retry_count`: Initialized to 0
- [ ] Successfully processes multiple runs without creating duplicate jobs for the same ISBN
- [ ] Provides clear output showing number of jobs created, skipped, and any validation errors

## Technical Details

### Files to Create/Modify
- `publisher.py` (create new)
- `data/curated_books.csv` (sample/template file)

### Database Changes
- Ensure `jobs` table exists with columns: job_id, title, author, isbn, status, created_at, retry_count, error_message, completed_at
- Create unique constraint on ISBN to help with duplicate detection

### Configuration
- CSV file path: `data/curated_books.csv` (configurable via environment or `config.py`)
- Database connection via `config.py`

### Environment Variables
- `CSV_FILE_PATH` (optional, defaults to `data/curated_books.csv`)
- `DATABASE_URL` or individual `DB_*` variables (from `config.py`)

## Implementation Notes
- The `config.py` module already exists with database connection utilities
- CSV reading should use Python's standard `csv` module
- Validation should be thorough but not over-engineered
- Duplicate detection should query the jobs table for existing ISBNs before inserting
- All database operations should be wrapped in try-catch blocks with proper error logging
- Consider batch inserts for performance if processing many books

## Testing Requirements
- **Unit tests**: CSV parsing, data validation, duplicate detection logic
- **Integration tests**: End-to-end CSV → jobs table flow
- Test with sample CSV file containing:
  - Valid books
  - Books with missing fields
  - Books with malformed data
  - Duplicate ISBNs (should skip the second occurrence)

## Estimated Effort
**Medium: 4-8 hours**

---

## Implementation Steps

1. Create CSV schema validation logic
2. Implement duplicate detection query against jobs table
3. Build job record creation with transaction safety
4. Add comprehensive logging and error reporting
5. Create sample data file for testing
6. Write integration tests

