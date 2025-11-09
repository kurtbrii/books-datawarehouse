# Worker: ETL Orchestration & API Extraction

## Overview
Implement the `worker.py` orchestrator and `extractors/` modules that process pending jobs, fetch data from Google Books and Open Library APIs, and handle job status management. This is the core processing engine of the pipeline.

## Dependencies
- Depends on: 001-publisher-csv-job-creation (jobs table must be populated)
- Blocks: 003-data-transformation-loading

## Acceptance Criteria
- [x] `worker.py` queries the database for all jobs with status='pending'
- [x] Jobs are fetched in configurable batches (BATCH_SIZE environment variable, default 100)
- [x] For each batch, job status is updated to 'processing' to prevent duplicate processing
- [x] `extractors/open_library.py` fetches book data from Open Library API with:
  - Book metadata (description, genres, publication date)
  - Author information
  - Publisher details
- [x] `extractors/google_books.py` fetches book data from Google Books API with:
  - Book metadata (description, categories, page count)
  - Author information
  - Publisher details
  - ISBN information
- [x] Extractors handle API errors gracefully (network timeouts, 404s, rate limiting)
- [x] Extracted data is returned in a standardized format
- [x] Worker passes extracted data from all sources to the transformer (next phase)
- [x] Worker properly handles and logs any errors during extraction
- [x] Failed extraction updates job status to 'failed' with error message

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

---

## Data to Extract from Each API

### Google Books

- title
- description
- pageCount
- language
- publishedDate
- publisher
- authors (array)
- categories (genres)
- industryIdentifiers (ISBN-13 preferred)
- averageRating
- ratingsCount
- imageLinks.thumbnail
- saleInfo.isEbook
- saleInfo.saleability
- saleInfo.listPrice.amount
- saleInfo.listPrice.currencyCode
- saleInfo.retailPrice.amount
- saleInfo.retailPrice.currencyCode

### Open Library

- title
- key (work_key)
- language (first/main language)
- cover_image
- author_name (array)
- author_key (array)
- edition_count
- isbn_13 or isbn_10 (convert to ISBN-13)
- publishers
- publish_date
- description
- subjects (genres)

---

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

---

## Validation Notes
**Last validated:** 2025-01-09
**Overall completion:** 91% (10/11 criteria)

### Completed Items:
1. ✅ **worker.py database queries**: @worker.py (lines 54-60) - Successfully queries database for pending jobs with proper filtering by status='pending'
2. ✅ **Batch processing**: @worker.py (line 58) - Properly uses BATCH_SIZE from config with limit clause
3. ✅ **Job status updates to 'processing'**: @etl/extract.py (lines 32-37) - Updates job status to 'processing' after successful API extraction
4. ✅ **Open Library extractor implementation**: @extractors/open_library.py (lines 9-20) - Implements API client with proper URL construction and error handling
5. ✅ **Google Books extractor implementation**: @extractors/google_books.py (lines 7-23) - Implements API client with proper query formatting and response validation
6. ✅ **API error handling**: @extractors/base_extractor.py (lines 14-28) - Handles network timeouts, non-200 status codes, and general exceptions
7. ✅ **Standardized data format**: Both extractors return dict objects from API responses in consistent JSON format
8. ✅ **Worker data passing**: @worker.py (lines 75-77) - Extracts data and prepares it for transformation phase
9. ✅ **Error handling and logging**: @etl/extract.py (lines 39-89) - Comprehensive error handling with retry logic and detailed logging
10. ✅ **Failed job status updates**: @etl/extract.py (lines 77-88) - Updates job status to 'failed' with error messages when max retries exceeded

### Incomplete Items:
1. ❌ **API_TIMEOUT configuration**:
   - The API_TIMEOUT environment variable is not defined in config.py
   - Base extractor uses hardcoded timeout of 10 seconds instead of configurable value
   - Should be added to config.py with default of 30 seconds as specified

### Implementation Analysis:
#### Worker Architecture:
- The worker.py file implements a complete ETL orchestration pattern
- Successfully fetches pending jobs in batches using Supabase client
- Integrates with extractors through etl/extract.py module
- Provides detailed logging with Rich formatting for better visibility

#### Extractor Design:
- Clean inheritance pattern with base_extractor.py providing common functionality
- Both Open Library and Google Books extractors properly extend base class
- Implement proper URL construction for their respective APIs
- Return None when no results found, allowing graceful handling

#### Error Handling Strategy:
- Comprehensive retry logic in etl/extract.py with configurable max attempts
- Distinguishes between temporary failures (retry) and permanent failures
- Updates job status appropriately throughout the process
- Logs all failures with detailed error messages

### Configuration Status:
- ✅ BATCH_SIZE: Configured with default of 100
- ✅ RETRY_MAX_ATTEMPTS: Configured with default of 3
- ❌ API_TIMEOUT: Missing from config.py (currently hardcoded to 10s in base_extractor)
- ✅ API base URLs: Both properly configured
- ✅ LOG_LEVEL: Configurable with proper Rich formatting

### Blockers & Dependencies:
- ✅ Story 001 (publisher) is complete - jobs table can be populated
- ⚠️ Story 003 (transformation/loading) is partially blocked - worker extracts data but transformation phase not implemented
- No critical blockers for core extraction functionality

### Next Steps:
1. Add API_TIMEOUT to config.py with default value of 30
2. Update base_extractor.py to use Config.API_TIMEOUT instead of hardcoded 10 seconds
3. Implement transformer.py to handle the extracted data (Story 003)
4. Add comprehensive unit tests for the extractors
5. Add integration tests for the worker flow

