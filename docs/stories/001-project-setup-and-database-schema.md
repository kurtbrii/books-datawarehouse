# 001: Project Setup and Database Schema

## Overview
Set up project structure, environment configuration, Python dependencies, and create the complete PostgreSQL database schema with all dimension tables, fact tables, indexes, and constraints.

## Dependencies
- None (foundation story)

## Blocks
- 002-api-extractors
- 003-etl-pipeline-core
- 004-data-loader

## Acceptance Criteria
- [ ] Project directory structure created per brief specifications
- [ ] `requirements.txt` defined with all necessary packages
- [ ] `.env.example` template created with all required variables
- [ ] `.gitignore` configured properly
- [ ] `config.py` created for database and API configuration
- [ ] Python virtual environment set up with dependencies installed
- [ ] README.md skeleton created
- [ ] All 9 database tables created with proper schema (jobs, dim_books, dim_date, dim_publisher, dim_author, dim_genre, book_author_bridge, book_genre_bridge, fact_book_metrics)
- [ ] All primary keys, foreign keys, and unique constraints implemented
- [ ] All 23 indexes created for query performance
- [ ] CHECK constraints for data validation implemented
- [ ] Audit fields (created_at, updated_at) on all dimension tables
- [ ] Schema script is idempotent (IF NOT EXISTS checks)

## Technical Details

### Files to Create/Modify
- `config.py` - Configuration management
- `requirements.txt` - Package dependencies
- `.env.example` - Environment template
- `.gitignore` - Git rules
- `README.md` - Documentation
- `sql/schema.sql` - Complete DDL for all tables
- `extractors/__init__.py` - Extractors package
- `data/` - Directory for CSV files

### Environment Variables
```
DATABASE_URL=postgresql://user:password@host:port/database
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_NAME=
OPEN_LIBRARY_API_KEY=
GOOGLE_BOOKS_API_KEY=
LOG_LEVEL=INFO
BATCH_SIZE=100
RETRY_MAX_ATTEMPTS=3
```

### Database Schema Highlights
- **jobs**: Queue management with status tracking
- **dim_tables**: dim_books, dim_publisher, dim_author, dim_genre (with audit fields)
- **fact_book_metrics**: Ratings, prices, availability data with (isbn, snapshot_date) uniqueness
- **Bridge tables**: book_author_bridge, book_genre_bridge for many-to-many relationships
- **dim_date**: Date dimension with YYYYMMDD format key

## Implementation Notes
- Use python-dotenv for environment variable loading
- Configuration should support both .env files and system variables
- ISBN stored as TEXT to support both ISBN-10 and ISBN-13
- DECIMAL(10,2) for prices, DECIMAL(3,2) for ratings
- All foreign keys use ON DELETE CASCADE
- Create comprehensive indexes for fact and dimension tables
- Include setup instructions for Supabase

## Testing Requirements
- Verify all imports work correctly
- Confirm environment variables load properly
- Integration test: Connect and verify all tables exist
- Integration test: Test foreign key constraints
- Integration test: Confirm unique constraints work

## Estimated Effort
**Medium** (4-6 hours)

