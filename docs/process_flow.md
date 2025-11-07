# Data Pipeline Process Flow

## Overview

This document describes the complete flow of how the Books Data Pipeline processes book data from CSV input through to the data warehouse.

---

## Phase 1: CSV Reading & Job Creation (Publisher)

### Step 1.1: Read CSV File
- The `publisher.py` script reads the **curated_books.csv** file
- Expected columns: `title`, `author`, and optionally `ISBN`
- Each row represents a single book to be processed

### Step 1.2: Validate Data
- For each row in the CSV, the publisher validates the data
- Ensures required fields are present and properly formatted
- Skips invalid rows or reports validation errors

### Step 1.3: Create Job Records
- For each valid book, the publisher creates a **job record** in the `jobs` table
- Job fields:
  - `title`: Book title from CSV
  - `author`: Book author from CSV
  - `isbn`: Optional ISBN identifier
  - `status`: Set to **'pending'** (indicating ready for processing)
  - `created_at`: Timestamp of job creation
  - `retry_count`: Initialized to 0

### Step 1.4: Duplicate Detection
- Before creating a job, the publisher checks if a job already exists for the same ISBN
- If a duplicate is found, it skips that row
- This prevents redundant API calls and warehouse entries

---

## Phase 2: Data Extraction & Transformation (Worker)

### Step 2.1: Fetch Pending Jobs
- The `worker.py` script queries the database for all jobs with status = **'pending'**
- Fetches jobs in batches (controlled by the `BATCH_SIZE` environment variable)
- This allows for scalable, incremental processing

### Step 2.2: Update Job Status to Processing
- For each job being processed, update its status to **'processing'**
- This prevents other worker instances from processing the same job
- Provides visibility into what's currently being worked on

### Step 2.3: Extract Data from APIs
- The `extractors.py` module calls external APIs to fetch book data
- Multiple extractors may be used (e.g., Google Books API, Open Library API)
- Each extractor returns:
  - Book metadata (description, genres, publication date)
  - Author information
  - Publisher details
  - Other enriched fields

### Step 2.4: Transform & Merge Data
- The `transformer.py` module receives the raw data from all extractors
- Performs data cleaning:
  - Removes duplicates
  - Standardizes formats
  - Fills missing values
  - Normalizes text (case, whitespace, etc.)
- Merges data from multiple sources into a unified format
- Resolves conflicts between sources

---

## Phase 3: Data Loading to Warehouse

### Step 3.1: Prepare Warehouse Data
- The `loader.py` module receives the cleaned, merged data
- Prepares data for insertion into the warehouse schema

### Step 3.2: Populate Dimension Tables
- Insert or update dimension tables:
  - `authors` (author information)
  - `publishers` (publisher information)
  - `genres` (genre information)
  - `languages` (language information)
- Each dimension is checked for existing records (no duplicates)

### Step 3.3: Populate Bridge/Junction Tables
- Insert records into bridge tables to establish many-to-many relationships:
  - `book_authors` (books ↔ authors)
  - `book_genres` (books ↔ genres)
  - etc.

### Step 3.4: Insert into Fact Tables
- Insert the main book record into the `books` fact table
- Include:
  - Title and description
  - ISBNs
  - Publication details
  - Foreign keys to dimension tables

### Step 3.5: Transaction Management
- All warehouse inserts use transactions (all-or-nothing)
- If any insert fails, all changes are rolled back
- Ensures data integrity and consistency

---

## Phase 4: Job Completion

### Step 4.1: Mark as Completed
- Upon successful processing, update the job status to **'completed'**
- Record the completion timestamp

### Step 4.2: Handle Failures
- If any step fails, the job status is updated to **'failed'**
- The error message and exception details are stored
- The `retry_count` is incremented

### Step 4.3: Retry Logic
- Failed jobs can be retried later by running the worker again
- The worker only processes jobs with status **'pending'** (not 'failed')
- This allows for manual intervention if needed

---

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│              INPUT: curated_books.csv                   │
│         (title, author, ISBN columns)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │   publisher.py        │
         │  - Read CSV file      │
         │  - Validate data      │
         │  - Detect duplicates  │
         └───────────┬───────────┘
                     │
                     ↓
    ┌────────────────────────────────────┐
    │    jobs table (status: pending)    │
    │  ┌──────────────────────────────┐  │
    │  │ job_id │ title │ author │... │  │
    │  └──────────────────────────────┘  │
    └────────────────┬───────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │   worker.py           │
         │  - Query pending jobs │
         │  - Batch processing   │
         └───────────┬───────────┘
                     │
                     ↓
    ┌────────────────────────────────────────┐
    │      extractors.py                     │
    │  - Google Books API                    │
    │  - Open Library API                    │
    │  - Other data sources                  │
    └────────────────┬───────────────────────┘
                     │
                     ↓
    ┌────────────────────────────────────────┐
    │      transformer.py                    │
    │  - Clean & normalize data              │
    │  - Merge from multiple sources         │
    │  - Resolve conflicts                   │
    └────────────────┬───────────────────────┘
                     │
                     ↓
    ┌────────────────────────────────────────┐
    │      loader.py                         │
    │  - Populate dimension tables (authors) │
    │  - Populate junction tables (book_gen) │
    │  - Insert fact records (books)         │
    │  - Transaction management              │
    └────────────────┬───────────────────────┘
                     │
                     ↓
    ┌─────────────────────────────────────────┐
    │    Data Warehouse                       │
    │  ┌──────────────────────────────────┐   │
    │  │ Dimension tables (authors, etc.) │   │
    │  │ Bridge tables (book_authors)     │   │
    │  │ Fact tables (books)              │   │
    │  └──────────────────────────────────┘   │
    └────────────┬────────────────────────────┘
                 │
                 ↓
    ┌─────────────────────────────────────┐
    │  jobs table (status: completed)      │
    │  ┌────────────────────────────────┐  │
    │  │ job_id │ status │ completed_at │  │
    │  └────────────────────────────────┘  │
    └─────────────────────────────────────┘
```

---

## Key Architectural Benefits

### 1. **Decoupled Phases**
- CSV reading is independent from data processing
- Can add more books to CSV and re-run publisher without affecting existing data

### 2. **Scalable Job Processing**
- Worker can process jobs in configurable batch sizes
- Multiple worker instances can run in parallel (job status prevents conflicts)
- Horizontal scalability is built-in

### 3. **Fault Tolerance**
- Failed jobs don't stop the entire pipeline
- Error details are stored for debugging
- Retry mechanism allows recovering from temporary API failures

### 4. **Auditability**
- Jobs table provides complete history of what was processed
- Timestamps track when each job was created and completed
- Failed jobs can be reviewed and retried manually

### 5. **Idempotency**
- Worker can be run multiple times safely
- Only processes jobs with status = 'pending'
- Duplicate detection at CSV reading phase prevents redundant work

### 6. **Data Integrity**
- Transactions ensure all-or-nothing consistency in warehouse
- Dimension tables prevent duplicate entries
- Foreign key relationships maintain referential integrity

---

## Environment Variables

- **`BATCH_SIZE`**: Number of jobs to process in a single worker run (default: typically 10-50)
- **`DATABASE_URL`**: Connection string for the database
- **`API_TIMEOUT`**: Timeout for external API calls
- Other configuration as needed

---

## Running the Pipeline

### Initial Setup
```bash
# 1. Prepare your CSV file with book data
# 2. Run the publisher to create jobs
python publisher.py
```

### Process Jobs
```bash
# 3. Run the worker to process all pending jobs
python worker.py

# Can be run multiple times
python worker.py
```

### Retry Failed Jobs (if needed)
```bash
# 4. Manually fix issues and restart failed jobs
python worker.py --retry-failed
```

---

## Monitoring & Troubleshooting

### Check Job Status
- Query the `jobs` table to see the status of each job
- Filter by status: `pending`, `processing`, `completed`, `failed`

### Review Failed Jobs
- Check the `error_message` and `retry_count` fields
- Determine if the failure is temporary or requires data fixes

### Re-run Worker
- Worker automatically picks up pending jobs on the next run
- No manual intervention needed for retry logic


