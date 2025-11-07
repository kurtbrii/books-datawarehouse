
# Books Data Warehouse

A multi-source data warehouse that integrates book data from Open Library and Google Books APIs. This project demonstrates ETL pipeline development, dimensional modeling, and analytical query capabilities—serving as a foundation for future data engineering projects.

## Project Overview

This project builds a dimensional data warehouse to collect, transform, and analyze book metadata from multiple sources. It showcases:

- **Dimensional data warehouse schema** with proper normalization and relationships
- **ETL pipeline** that extracts from external APIs, transforms data, and loads into PostgreSQL
- **Data quality handling** for merging data from multiple sources
- **Scalable architecture** capable of processing thousands of books

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ (or Supabase)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd books-data-warehouse
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials (no API keys needed - both APIs are public)
   ```

5. **Create database schema:**
   ```bash
   psql -d your_database_name -f sql/schema.sql
   # Or for Supabase, run the schema.sql queries in the SQL editor
   ```

## Project Structure

```
books-data-warehouse/
│
├── data/
│   └── curated_books.csv          # Input: ISBNs or titles to process
│
├── extractors/
│   ├── __init__.py
│   ├── open_library.py            # Open Library API calls
│   └── google_books.py            # Google Books API calls
│
├── sql/
│   └── schema.sql                 # DDL for all tables, indexes, and constraints
│
├── config.py                      # Database and API configuration
├── publisher.py                   # Reads CSV, creates jobs
├── worker.py                      # Main ETL orchestrator
├── transformer.py                 # Data merging and cleaning
├── loader.py                      # Database insert operations
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── README.md                      # This file
└── .gitignore
```

## Tech Stack

### Backend
- **Language:** Python 3.x
- **Database:** PostgreSQL (or Supabase)
- **Package Manager:** pip

### Libraries
| Library | Purpose |
|---------|---------|
| requests | HTTP requests for API calls |
| psycopg2-binary | PostgreSQL database adapter |
| python-dotenv | Environment variable management |
| pandas | Data transformation and analysis |

### Data Sources
- **Open Library API** - Book metadata, editions, authors, subjects
- **Google Books API** - Ratings, categories, publisher info, availability

## Configuration

### Environment Variables

The project uses environment variables for configuration. See `.env.example` for all available options:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://user:pass@localhost:5432/books_db` |
| `DB_USER` | Database username (if using individual components) | `postgres` |
| `DB_PASSWORD` | Database password | `mypassword` |
| `DB_HOST` | Database host | `localhost` or `db.supabase.co` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `books_db` |
| `OPEN_LIBRARY_BASE_URL` | Open Library API base URL | `https://openlibrary.org` |
| `GOOGLE_BOOKS_BASE_URL` | Google Books API base URL | `https://www.googleapis.com/books/v1` |
| `LOG_LEVEL` | Logging verbosity | `INFO`, `DEBUG`, `ERROR` |
| `BATCH_SIZE` | Records to process per batch | `100` |
| `RETRY_MAX_ATTEMPTS` | Max retries for failed operations | `3` |

### Using Configuration

The `config.py` module provides a centralized `Config` class:

```python
from config import Config

# Access database configuration
db_url = Config.get_db_connection_string()

# Access API configuration
open_lib_url = Config.OPEN_LIBRARY_BASE_URL
google_books_url = Config.GOOGLE_BOOKS_BASE_URL

# Access application settings
batch_size = Config.BATCH_SIZE
retry_attempts = Config.RETRY_MAX_ATTEMPTS
```

## Database Schema

### Overview

The warehouse uses a **dimensional modeling** approach with the following table categories:

#### Dimension Tables (contain descriptive attributes)
- **dim_date** - Time dimension with YYYYMMDD key format
- **dim_publisher** - Publisher information
- **dim_author** - Author information with Open Library identifiers
- **dim_genre** - Genre/category information
- **dim_books** - Book attributes and metadata

#### Fact Tables (contain measurable metrics)
- **fact_book_metrics** - Ratings, prices, availability data

#### Bridge Tables (handle many-to-many relationships)
- **book_author_bridge** - Links books to multiple authors
- **book_genre_bridge** - Links books to multiple genres

#### Job Management
- **jobs** - Tracks ETL job status and processing queue

### Key Design Decisions

- **ISBN as Text:** Supports both ISBN-10 and ISBN-13 formats
- **Composite Keys:** Bridge tables use composite primary keys for data integrity
- **Audit Fields:** All dimension tables include `created_at` and `updated_at` timestamps
- **Cascading Deletes:** Foreign keys use ON DELETE CASCADE for referential integrity
- **Unique Constraints:** Prevent duplicate entries for publishers, authors, and genres
- **Check Constraints:** Validate data ranges (e.g., ratings 0-5)

### Indexes

Comprehensive indexing for query performance:

**Fact Table Indexes:**
- `idx_fact_metrics_isbn` - Fast metric lookup by book
- `idx_fact_metrics_snapshot_date` - Time-based queries
- `idx_fact_metrics_rating` - Rating-based filtering and sorting

**Dimension Table Indexes:**
- `idx_books_publisher` - Publisher-level analytics
- `idx_books_published_date` - Temporal analysis
- `idx_books_language` - Language-specific queries
- `idx_author_name` - Author lookup
- `idx_author_ol_key` - Open Library identifier lookup
- `idx_genre_name` - Genre deduplication

**Bridge Table Indexes:**
- `idx_book_author_author_id` - Many-to-many relationship queries
- `idx_book_genre_genre_id` - Genre-level aggregations

**Date Dimension Index:**
- `idx_date_year_month` - Year/month aggregations

## ETL Pipeline

### Data Flow

```
┌─────────────────────┐
│   Curated Books     │
│     (CSV file)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Publisher Process  │
│  (Creates Jobs)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│        Jobs Queue (PostgreSQL)          │
│   status: pending/processing/failed     │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│        Worker Process (ETL)             │
│  ┌──────────────────────────────────┐   │
│  │ 1. Extract from APIs             │   │
│  │    - Open Library API            │   │
│  │    - Google Books API            │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │ 2. Transform                     │   │
│  │    - Merge data from sources     │   │
│  │    - Validate quality            │   │
│  │    - Deduplicate records         │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │ 3. Load to Warehouse             │   │
│  │    - Insert/update dimensions    │   │
│  │    - Update fact table           │   │
│  │    - Handle errors               │   │
│  └──────────────────────────────────┘   │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│   Data Warehouse (PostgreSQL)           │
│                                         │
│  • 9 tables with relationships          │
│  • 23+ performance indexes              │
│  • Referential integrity constraints    │
│  • Audit trails (created_at, updated_at)│
└─────────────────────────────────────────┘
```

### Processing Steps

1. **Publisher Phase:** Read CSV file and create jobs
2. **Worker Phase:** Process jobs from queue
3. **Extract Phase:** Query both APIs for book data
4. **Transform Phase:** Merge, validate, and clean data
5. **Load Phase:** Insert into warehouse with error handling

## Analytics Queries

The schema supports answering questions like:

### Rating & Quality Analysis
- Which genres have the highest average ratings?
- What is the correlation between number of ratings and average rating?
- Do books with more editions tend to have higher ratings?
- Which publishers consistently produce highly-rated books (avg rating > 4.0)?
- Is there a correlation between page count and rating?

### Market & Popularity Analysis
- Which authors have the most books in the warehouse?
- What is the distribution of books by publication decade?
- Which genres have the most available ebooks?
- What percentage of books are available as ebooks vs. print only?
- Which books have the most editions available?

### Publisher & Author Insights
- Which publishers dominate each genre?
- What is the average page count by genre?
- Which authors write across the most genres?
- What are the top 10 books with the most editions available?

### Cross-Dimensional Analysis
- Fiction vs Non-Fiction: Which has higher ratings, more editions, and longer pages?

## Getting Help

### Supabase Setup

For Supabase users:

1. Create a new Supabase project
2. Note your connection details (host, port, database, user, password)
3. Update `.env` with Supabase credentials
4. Run `schema.sql` in the Supabase SQL Editor

### Debugging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python worker.py
```

Check job status:
```sql
SELECT job_id, status, error_message, retry_count FROM jobs WHERE status = 'failed';
```

### Common Issues

- **Connection refused:** Verify DATABASE_URL and database is running
- **API rate limits:** Adjust BATCH_SIZE and add delays between requests
- **Missing data:** Check API responses and error_message in jobs table

## Future Enhancements

- Time-series analysis with weekly ETL runs
- Additional data sources (NYT, Goodreads, etc.)
- Materialized views for common aggregations
- Data visualization dashboard (Streamlit/Tableau)
- Apache Airflow orchestration
- Redis caching for API responses

## Success Criteria

- ✅ Functional ETL pipeline for both APIs
- ✅ < 5% failed jobs with proper error handling
- ✅ All foreign keys valid, no orphaned records
- ✅ All 15 analytical queries complete in < 5 seconds
- ✅ Architecture scalable to 10,000+ books

## License

MIT License

## Contributing

Contributions welcome! Please follow PEP 8 style guide and add tests for new features.
