# 002: API Extractors (Open Library & Google Books)

## Overview
Build extractors for both Open Library and Google Books APIs. Handle API authentication, rate limiting, error handling, and data validation. Return structured data for transformation.

## Dependencies
- Depends on: 001-project-setup-and-database-schema

## Blocks
- 003-etl-pipeline-core
- 004-data-loader

## Acceptance Criteria
- [ ] `extractors/open_library.py` created with functions to fetch book metadata, editions, and authors
- [ ] `extractors/google_books.py` created with functions to fetch ratings, categories, and pricing
- [ ] Both extractors handle API authentication and key management
- [ ] Rate limiting implemented to avoid hitting API limits
- [ ] Comprehensive error handling for network failures, timeouts, and invalid responses
- [ ] Retry logic with exponential backoff for failed requests
- [ ] Logging of all API calls and failures
- [ ] Data validation to ensure required fields are present
- [ ] Functions return dictionaries with standardized keys for transformation
- [ ] Handle ISBN and title-based lookups for book identification
- [ ] Mock/test data available for local development without hitting real APIs

## Technical Details

### Files to Create/Modify
- `extractors/open_library.py` - Open Library API client
- `extractors/google_books.py` - Google Books API client
- `extractors/__init__.py` - Export public functions

### API Endpoints to Integrate
**Open Library:**
- `/search.json?title=<title>&author=<author>` - Book search
- `/isbn/<isbn>.json` - Direct ISBN lookup
- `/works/<work_key>.json` - Work details (editions, authors)
- `/authors/<author_key>.json` - Author information

**Google Books:**
- `/volumes?q=isbn:<isbn>` - ISBN search
- `/volumes?q=<title>+inauthor:<author>` - Title + author search
- Extract: ratings, categories, language, description, prices, availability

### Error Handling Strategy
- Network timeouts: Retry with exponential backoff
- Rate limits (429): Pause and retry
- Not found (404): Log and continue
- Invalid data: Log warning and skip fields
- Timeout: Maximum 3 retries

### Rate Limiting
- Request throttling: 10 requests per second
- Batch processing with delays between batches
- Respect API rate limit headers

## Implementation Notes
- Use `requests` library with session objects for connection pooling
- Implement circuit breaker pattern to stop calling failing APIs
- Cache responses where possible to minimize API calls
- Handle edge cases: missing ISBNs, multiple editions, international characters
- Document API key setup for both services
- Create test fixtures with sample API responses

## Testing Requirements
- Unit test: Mock API responses and verify parsing
- Unit test: Verify error handling and retry logic
- Unit test: Confirm rate limiting works correctly
- Integration test: Test with actual APIs (if keys available)
- Manual test: Verify data quality with various book types

## Estimated Effort
**Large** (6-8 hours)

