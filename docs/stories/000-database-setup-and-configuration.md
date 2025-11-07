# Database Setup & Project Configuration

## Overview
Set up the PostgreSQL database in Supabase, create all necessary dimensional tables and schema, configure environment variables, and prepare the project for ETL implementation. This is the foundational prerequisite that must be completed before any other stories can begin.

## Dependencies
- Depends on: None (this is the first story)
- Blocks: 001-publisher-csv-job-creation, 002-worker-api-extraction, 003-data-transformation-loading, 004-job-completion-monitoring

## Acceptance Criteria
- [ ] Supabase account is created and a new PostgreSQL database project is set up
- [ ] Database connection details are documented (host, port, database name, user credentials)
- [ ] All SQL schema is successfully executed in Supabase SQL editor
- [ ] All 9 tables are created with correct structure:
  - Job Management: `jobs`
  - Dimensions: `dim_books`, `dim_author`, `dim_publisher`, `dim_genre`, `dim_date`
  - Bridges: `book_author_bridge`, `book_genre_bridge`
  - Fact: `fact_book_metrics`
- [ ] All unique constraints are enforced (ISBN uniqueness, author deduplication, etc.)
- [ ] Foreign key relationships are established between fact and dimension tables
- [ ] Indexes are created for common query patterns (ISBN, author_id, genre_id, status, created_at)
- [ ] `.env` file is created from `.env.example` template with correct database credentials
- [ ] `config.py` is verified to contain correct database connection logic
- [ ] Database connection can be tested successfully from Python (`config.py`)
- [ ] Sample data can be inserted and queried successfully
- [ ] All tests in the project pass (if any exist)

## Technical Details

### Files to Create/Modify
- `.env` (create from `.env.example` template)
- `sql/schema.sql` (verify existing file is correct)
- `config.py` (verify existing connection utilities)

### Supabase Setup Steps

#### 1. Create Supabase Project
- Go to https://supabase.com and sign up/log in
- Create a new project
- Choose a region closest to your location
- Set a secure database password
- Wait for the project to provision (2-3 minutes)

#### 2. Get Connection Details
- In Supabase dashboard, go to Settings → Database
- Copy the following:
  - Host (postgresql.supabase.co or similar)
  - Port (usually 5432)
  - Database (usually "postgres")
  - User (usually "postgres")
  - Password (the one you set during creation)

#### 3. Create Schema
- In Supabase dashboard, go to SQL Editor
- Create a new query
- Copy the entire contents of `sql/schema.sql`
- Paste into the SQL editor
- Click "Run" to execute
- Verify all tables are created (check Tables list on left sidebar)

#### 4. Verify Table Creation
- Open SQL Editor again
- Run this verification query:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```
- Should return exactly 9 tables

### Environment Configuration

#### Step 1: Create .env File
```bash
# Copy the template
cp .env.example .env
```

#### Step 2: Edit .env with Supabase Credentials
```env
# Database Configuration
DB_HOST=your_supabase_host.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_secure_password_here

# Or use full connection string (prioritized in config.py)
DATABASE_URL=postgresql://postgres:your_password@your_host.supabase.co:5432/postgres

# Application Settings
LOG_LEVEL=INFO
BATCH_SIZE=100
RETRY_MAX_ATTEMPTS=3
API_TIMEOUT=30

# CSV Configuration (optional)
CSV_FILE_PATH=data/curated_books.csv
```

#### Step 3: Test Database Connection
```bash
# Activate virtual environment
source venv/bin/activate

# Run Python and test connection
python3
>>> from config import Config
>>> db_conn = Config.get_db_connection()
>>> cursor = db_conn.cursor()
>>> cursor.execute("SELECT version();")
>>> print(cursor.fetchone())
# Should print PostgreSQL version info
>>> db_conn.close()
```

### Database Schema Details

**Jobs Table** (ETL job queue and tracking)
- `job_id`: Primary key (auto-increment)
- `title`: Book title from CSV
- `author`: Book author from CSV
- `isbn`: Optional ISBN (unique constraint)
- `status`: Job status ('pending', 'processing', 'completed', 'failed')
- `created_at`: Timestamp when job was created
- `completed_at`: Timestamp when job completed (nullable)
- `error_message`: Error details if job failed (nullable)
- `retry_count`: Number of times job has been retried
- `updated_at`: Last update timestamp

**Dimension Tables** (Book metadata and attributes)
- `dim_books`: ISBN (PK), title, description, page_count, publication_date
- `dim_author`: author_id (PK), name, open_library_id, birth_date (nullable)
- `dim_publisher`: publisher_id (PK), name, country (nullable)
- `dim_genre`: genre_id (PK), name, category
- `dim_date`: date_id (PK, YYYYMMDD format), year, month, day, quarter

**Bridge Tables** (Many-to-many relationships)
- `book_author_bridge`: book_id, author_id (composite PK)
- `book_genre_bridge`: book_id, genre_id (composite PK)

**Fact Table** (Measurable metrics)
- `fact_book_metrics`: Fact_id (PK), book_id (FK), date_id (FK), rating, price, availability_status, open_library_id

### Constraints & Indexes

**Unique Constraints:**
- `jobs(isbn)` - Prevent duplicate job creation for same ISBN
- `dim_author(open_library_id)` - Prevent author duplication
- `dim_publisher(name)` - Prevent publisher duplication
- `dim_genre(name)` - Prevent genre duplication

**Foreign Keys:**
- `fact_book_metrics` → `dim_books`
- `fact_book_metrics` → `dim_date`
- `book_author_bridge` → `dim_books` and `dim_author`
- `book_genre_bridge` → `dim_books` and `dim_genre`

**Indexes:**
- `jobs(status)` - Fast filtering by job status
- `jobs(created_at)` - Fast chronological queries
- `dim_books(isbn)` - Fast ISBN lookups
- `dim_author(open_library_id)` - Fast author deduplication
- `dim_publisher(name)` - Fast publisher lookups
- `dim_genre(name)` - Fast genre lookups
- `fact_book_metrics(book_id)` - Fast metric lookups by book

### Configuration

All configuration is managed through `config.py`:
- Database connection pooling (if needed)
- Connection string prioritization (DATABASE_URL over individual components)
- Environment variable loading via `python-dotenv`
- Logging configuration based on LOG_LEVEL

### Environment Variables

- `DATABASE_URL`: Full PostgreSQL connection string (prioritized if set)
- `DB_HOST`: Database host (falls back if DATABASE_URL not set)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: "postgres")
- `DB_USER`: Database user (default: "postgres")
- `DB_PASSWORD`: Database password (required)
- `LOG_LEVEL`: Logging level (default: INFO, options: DEBUG, INFO, WARNING, ERROR)
- `BATCH_SIZE`: Jobs per worker run (default: 100)
- `RETRY_MAX_ATTEMPTS`: Max retries per failed job (default: 3)
- `API_TIMEOUT`: API request timeout in seconds (default: 30)
- `CSV_FILE_PATH`: Path to input CSV file (default: data/curated_books.csv)

## Implementation Notes
- Supabase automatically provisions backups; no manual backup setup needed
- Keep database password secure; never commit `.env` to version control (.gitignore already configured)
- For local development, Supabase provides free tier sufficient for testing
- Connection pooling in production may require additional setup if handling high concurrency
- Test connection before proceeding to Story 001 to catch credential issues early
- Use DEBUG log level during initial setup to see detailed connection info

## Testing Requirements
- **Database connectivity test**: Python script successfully connects and runs SELECT query
- **Schema verification**: All 9 tables exist with correct structure
- **Constraint verification**: Unique constraints and foreign keys enforced
- **Index verification**: All indexes created successfully
- **Sample insert**: Can insert sample data into jobs table
- **Sample query**: Can retrieve inserted data
- **Connection pooling**: Multiple connections can be created safely

## Estimated Effort
**Small: 1-2 hours**

---

## Implementation Checklist

### Before Starting
- [ ] Supabase account created
- [ ] PostgreSQL knowledge (basic)
- [ ] Python environment activated
- [ ] Requirements installed (`pip install -r requirements.txt`)

### During Setup
- [ ] Supabase project created
- [ ] Connection details noted
- [ ] `.env` file created with correct credentials
- [ ] `sql/schema.sql` executed in Supabase
- [ ] All 9 tables verified to exist
- [ ] Indexes created successfully
- [ ] Foreign keys established

### After Setup
- [ ] Database connection tested from Python
- [ ] Sample data inserted successfully
- [ ] Sample query returns expected results
- [ ] `.env` file secured (not in version control)
- [ ] Team members can connect to same database

### Verification Commands

```bash
# Test Python connection
python3 -c "from config import Config; db = Config.get_db_connection(); print('Connected!' if db else 'Failed')"

# Check tables (run in Supabase SQL Editor)
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';

# Verify constraints (run in Supabase SQL Editor)
SELECT constraint_name, constraint_type FROM information_schema.table_constraints WHERE table_schema = 'public' LIMIT 20;
```

## Next Steps
Once this story is complete:
1. Proceed to Story 001: Publisher CSV Job Creation
2. Run `python publisher.py` to create initial jobs
3. Continue with remaining stories in sequence

## Troubleshooting

**Connection refused:**
- Verify host address is correct
- Check firewall/IP whitelist in Supabase dashboard
- Confirm password is correct

**Schema creation fails:**
- Ensure all SQL is copied correctly from schema.sql
- Check for duplicate table definitions
- Verify database user has CREATE TABLE permissions

**Missing tables after execution:**
- Re-run schema.sql completely
- Check SQL execution results for errors
- Verify in Supabase UI that tables exist

**Environment variables not loading:**
- Ensure .env file is in project root
- Restart Python interpreter after creating .env
- Check .env file format (no quotes around values)

