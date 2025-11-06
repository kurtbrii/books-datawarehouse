# 003: ETL Pipeline Core (Publisher, Worker, Transformer)

## Overview
Build the ETL orchestration layer: publisher reads curated books CSV and creates jobs, worker processes jobs by extracting and transforming data, and transformer merges/deduplicates data from multiple sources.

## Dependencies
- Depends on: 001-project-setup-and-database-schema, 002-api-extractors

## Blocks
- 004-data-loader
- 005-analytics-and-testing

## Acceptance Criteria
- [ ] `publisher.py` reads curated_books.csv and creates job records
- [ ] Publisher validates CSV format (ISBN/title and author columns)
- [ ] Publisher creates jobs in 'pending' status
- [ ] `worker.py` implements main ETL orchestration loop
- [ ] Worker fetches pending jobs and processes them sequentially
- [ ] Worker calls both API extractors (Open Library and Google Books)
- [ ] Worker handles timeout and partial failures gracefully
- [ ] `transformer.py` merges data from both APIs into unified format
- [ ] Transformer handles data deduplication and conflict resolution
- [ ] Transformer normalizes data types and handles missing values
- [ ] Transformer validates data quality before loading
- [ ] Worker updates job status: pending → processing → completed/failed
- [ ] Failed jobs include error messages for debugging
- [ ] Logging captures all ETL activities at job and row levels
- [ ] Transaction management ensures data consistency

## Technical Details

### Files to Create/Modify
- `publisher.py` - CSV reader and job creator
- `worker.py` - Main ETL orchestrator loop
- `transformer.py` - Data merging and validation
- `data/curated_books.csv` - Sample input data

### Publisher Logic
```
1. Read CSV file (isbn, title, author columns)
2. For each row:
   - Validate ISBN or title exists
   - Create job record with status='pending'
   - Log job creation
3. Handle duplicate detection (skip if job exists for same ISBN)
```

### Worker Flow
```
1. Connect to database
2. Query jobs with status='pending'
3. For each job (limit by BATCH_SIZE):
   - Update status to 'processing'
   - Extract from Open Library API
   - Extract from Google Books API
   - Call transformer to merge data
   - If successful: pass to loader (story 004)
   - If failed: update status='failed', store error_message
   - Increment retry_count if applicable
4. Log summary statistics
```

### Transformer Responsibilities
- Merge Open Library and Google Books data
- ISBN normalization (remove hyphens, validate format)
- Author deduplication using Open Library keys
- Genre/category mapping
- Price and rating data handling
- Missing data strategies (nulls vs. defaults)
- Data quality validation before load

### Data Flow
```
CSV → Publisher → Jobs Table
Jobs Table → Worker → Extractors → Transformer → Unified Record
```

## Implementation Notes
- Worker can run as one-time script or continuous service
- Implement batch processing to avoid memory overload
- Use logging for debugging API interactions
- Transformer should be independent and testable
- Handle edge cases: incomplete data, duplicate editions, language variations
- CSV should include sample 10-20 books for testing
- Consider transaction rollback on partial failures

## Testing Requirements
- Unit test: CSV parsing and job creation
- Unit test: Transformer merging logic with sample data
- Unit test: Error handling and retry logic
- Integration test: End-to-end with mock APIs
- Manual test: Run with 20-50 real books
- Data quality checks: Verify transformed data matches schema

## Estimated Effort
**Large** (8-10 hours)

