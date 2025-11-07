# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your database credentials (no API keys needed - both APIs are public)
```

### Database Setup
```bash
# Create database schema (PostgreSQL)
psql -d your_database_name -f sql/schema.sql

# For Supabase: Run schema.sql queries in the SQL editor
```

### Running the ETL Pipeline
```bash
# Step 1: Create jobs from CSV file
python publisher.py

# Step 2: Process pending jobs (can be run multiple times)
python worker.py

# Step 3: Run the demonstration/sample flow
python sandbox/sample_run.py
```

### Development Workflow
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python worker.py

# Check job status in database
psql -d your_database_name -c "SELECT job_id, status, error_message, retry_count FROM jobs WHERE status = 'failed';"
```

## Architecture Overview

This is a **dimensional data warehouse** project that implements a complete ETL pipeline for book metadata from Open Library and Google Books APIs. The architecture follows a job-queue pattern with clear separation of concerns.

### Core Components (Not Yet Implemented)

The project follows a modular ETL architecture with these key modules:

1. **publisher.py** - Reads `data/curated_books.csv` and creates job records
2. **worker.py** - Main ETL orchestrator that processes jobs from the queue
3. **extractors/** - API integration modules:
   - `open_library.py` - Open Library API client
   - `google_books.py` - Google Books API client
4. **transformer.py** - Data merging, cleaning, and quality validation
5. **loader.py** - Database operations with transaction management

### Data Flow Architecture

```
CSV Input → Job Queue → Worker Process → Extract APIs → Transform Data → Load Warehouse
```

**Phase 1: Job Creation**
- `publisher.py` reads curated_books.csv (title, author, ISBN columns)
- Creates jobs in PostgreSQL with status='pending'
- Implements duplicate detection via ISBN

**Phase 2: ETL Processing**
- `worker.py` fetches pending jobs in batches (configurable via BATCH_SIZE)
- Updates job status to 'processing' to prevent conflicts
- Calls extractors to fetch data from multiple APIs
- Passes extracted data to transformer for cleaning/merging
- Calls loader to insert into dimensional schema with transactions

**Phase 3: Warehouse Loading**
- Dimension tables: `dim_books`, `dim_author`, `dim_publisher`, `dim_genre`, `dim_date`
- Bridge tables: `book_author_bridge`, `book_genre_bridge` (many-to-many)
- Fact table: `fact_book_metrics` (ratings, prices, availability)
- Job status updated to 'completed' or 'failed'

### Database Schema Design

The warehouse uses **dimensional modeling** with 9 tables:

**Job Management:**
- `jobs` - ETL job queue with status tracking and retry logic

**Dimensions (descriptive attributes):**
- `dim_books` - Book metadata (ISBN as PK, title, description, page_count)
- `dim_author` - Author information with Open Library deduplication
- `dim_publisher` - Publisher details with unique constraints
- `dim_genre` - Genre/category information
- `dim_date` - Time dimension with YYYYMMDD key format

**Bridge Tables (many-to-many):**
- `book_author_bridge` - Links books to multiple authors
- `book_genre_bridge` - Links books to multiple genres

**Fact Table (measurable metrics):**
- `fact_book_metrics` - Ratings, prices, availability with snapshot dates

### Configuration Management

All configuration is centralized in `config.py` using environment variables:

- **Database:** `DATABASE_URL` or individual `DB_*` variables
- **APIs:** `OPEN_LIBRARY_BASE_URL`, `GOOGLE_BOOKS_BASE_URL` (both public, no API keys required)
- **Processing:** `BATCH_SIZE` (default 100), `RETRY_MAX_ATTEMPTS` (default 3)
- **Logging:** `LOG_LEVEL` (default INFO)

The `Config.get_db_connection_string()` method prioritizes `DATABASE_URL` over individual components.

### Key Architectural Benefits

1. **Fault Tolerance** - Failed jobs don't stop the pipeline; error details stored for debugging
2. **Scalability** - Job queue allows parallel processing; configurable batch sizes
3. **Idempotency** - Worker can be run multiple times safely; only processes 'pending' jobs
4. **Data Integrity** - Transactions ensure all-or-nothing consistency; proper foreign key constraints
5. **Auditability** - Complete job history with timestamps and error tracking

### Analytical Capabilities

The schema supports 15 key analytical questions across:
- Rating & Quality Analysis (genre ratings, correlation analysis)
- Market & Popularity Analysis (author productivity, ebook availability)
- Publisher & Author Insights (genre dominance, page count analysis)
- Cross-Dimensional Analysis (fiction vs non-fiction comparisons)

### Error Handling Strategy

- Jobs table tracks retry_count and error_message
- Worker updates status to 'failed' for permanent errors
- Temporary API failures can be retried by resetting status to 'pending'
- Database transactions prevent partial data loads
- Comprehensive logging via LOG_LEVEL configuration