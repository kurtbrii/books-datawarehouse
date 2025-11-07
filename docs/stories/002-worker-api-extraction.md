# Worker: ETL Orchestration & API Extraction

## Overview
Implement the `worker.py` orchestrator and `extractors/` modules that process pending jobs, fetch data from Google Books and Open Library APIs, and handle job status management. This is the core processing engine of the pipeline.

## Dependencies
- Depends on: 001-publisher-csv-job-creation (jobs table must be populated)
- Blocks: 003-data-transformation-loading

## Acceptance Criteria
- [ ] `worker.py` queries the database for all jobs with status='pending'
- [ ] Jobs are fetched in configurable batches (BATCH_SIZE environment variable, default 100)
- [ ] For each batch, job status is updated to 'processing' to prevent duplicate processing
- [ ] `extractors/open_library.py` fetches book data from Open Library API with:
  - Book metadata (description, genres, publication date)
  - Author information
  - Publisher details
- [ ] `extractors/google_books.py` fetches book data from Google Books API with:
  - Book metadata (description, categories, page count)
  - Author information
  - Publisher details
  - ISBN information
- [ ] Extractors handle API errors gracefully (network timeouts, 404s, rate limiting)
- [ ] Extracted data is returned in a standardized format
- [ ] Worker passes extracted data from all sources to the transformer (next phase)
- [ ] Worker properly handles and logs any errors during extraction
- [ ] Failed extraction updates job status to 'failed' with error message

## Technical Details

### Files to Create/Modify
- `worker.py` (create new)
- `extractors/__init__.py` (create new)
- `extractors/open_library.py` (create new)
- `extractors/google_books.py` (create new)
- `config.py` (update with API configuration)

### API Integration
**Open Library API:**
- Base URL: `https://openlibrary.org` (from process_flow.md, is public)
- Endpoints: Search by ISBN/title, author lookup
- Returns: JSON with book and author metadata

**Google Books API:**
- Base URL: `https://www.googleapis.com/books/v1` (from process_flow.md, is public)
- Endpoints: Search by ISBN/title
- Returns: JSON with book metadata, ratings, page counts

### Database Changes
- Update `jobs` table to track processing status transitions
- Ensure `status` column supports: 'pending', 'processing', 'completed', 'failed'

### Configuration
- `BATCH_SIZE`: Number of jobs to process per worker run (default 100)
- `API_TIMEOUT`: Timeout for API requests (default 30 seconds)
- `OPEN_LIBRARY_BASE_URL`: API endpoint (from config)
- `GOOGLE_BOOKS_BASE_URL`: API endpoint (from config)

### Environment Variables
- `BATCH_SIZE` (default: 100)
- `API_TIMEOUT` (default: 30)
- `LOG_LEVEL` (default: INFO) - already supported in config.py

## Implementation Notes
- Both APIs are public (no API keys required) as noted in the architecture overview
- Extractors should be designed as separate, pluggable modules to allow adding new data sources
- All API calls should include proper error handling and retry logic for transient failures
- Use the existing `config.py` for logging configuration
- Worker should log processing status at each step
- Database transactions should prevent race conditions with multiple worker instances

## Testing Requirements
- **Unit tests**: 
  - Extractor error handling (404, timeout, malformed responses)
  - Data format validation for extracted data
  - Batch processing logic
- **Integration tests**:
  - End-to-end worker flow with mock API responses
  - Job status transitions (pending → processing → handled by next phase)
  - Error scenarios with failed API calls

## Estimated Effort
**Large: 1-2 days**

---

## Implementation Steps

1. Create extractor base class/interface for consistency
2. Implement Open Library API extractor with error handling
3. Implement Google Books API extractor with error handling
4. Build worker.py with batch job fetching and status updates
5. Implement job → extractor → result data flow
6. Add comprehensive error handling and logging
7. Write unit and integration tests
8. Test with sample job data

