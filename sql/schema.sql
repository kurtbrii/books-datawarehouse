-- ============================================================================
-- Books Data Warehouse Schema
-- Dimensional data warehouse for book metadata and metrics from multiple APIs
-- ============================================================================

-- Drop existing tables if they exist (for idempotency)
DROP TABLE IF EXISTS book_genre_bridge;
DROP TABLE IF EXISTS book_author_bridge;
DROP TABLE IF EXISTS fact_book_metrics;
DROP TABLE IF EXISTS dim_books;
DROP TABLE IF EXISTS dim_genre;
DROP TABLE IF EXISTS dim_author;
DROP TABLE IF EXISTS dim_publisher;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS jobs;

-- ============================================================================
-- 1. JOB MANAGEMENT TABLE
-- ============================================================================

CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn VARCHAR(20),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_isbn ON jobs(isbn);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);

-- ============================================================================
-- 2. DIMENSION TABLES
-- ============================================================================

-- dim_publisher: Publisher dimension with deduplication
CREATE TABLE dim_publisher (
    publisher_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_publisher_name ON dim_publisher(name);

-- dim_author: Author dimension with Open Library deduplication
CREATE TABLE dim_author (
    author_id SERIAL PRIMARY KEY,
    ol_author_key TEXT UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_author_name ON dim_author(name);
CREATE INDEX idx_author_ol_key ON dim_author(ol_author_key);

-- dim_genre: Genre/category dimension with deduplication
CREATE TABLE dim_genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_genre_name ON dim_genre(genre_name);

-- dim_date: Date dimension for temporal analysis
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    day INTEGER NOT NULL CHECK (day >= 1 AND day <= 31),
    quarter TEXT NOT NULL CHECK (quarter IN ('Q1', 'Q2', 'Q3', 'Q4')),
    day_of_week TEXT NOT NULL CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    is_weekend BOOLEAN NOT NULL
);

CREATE INDEX idx_date_year_month ON dim_date(year, month);
CREATE INDEX idx_date_full_date ON dim_date(full_date);

-- dim_books: Book dimension with all descriptive attributes
CREATE TABLE dim_books (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    page_count INTEGER CHECK (page_count > 0),
    language TEXT,
    published_date_key INTEGER REFERENCES dim_date(date_key) ON DELETE SET NULL,
    cover_image_id TEXT,
    work_key TEXT,
    publisher_id INTEGER REFERENCES dim_publisher(publisher_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_books_publisher ON dim_books(publisher_id);
CREATE INDEX idx_books_published_date ON dim_books(published_date_key);
CREATE INDEX idx_books_language ON dim_books(language);
CREATE INDEX idx_books_title ON dim_books(title);

-- ============================================================================
-- 3. BRIDGE TABLES FOR MANY-TO-MANY RELATIONSHIPS
-- ============================================================================

-- book_author_bridge: Links books to their authors
CREATE TABLE book_author_bridge (
    isbn TEXT NOT NULL REFERENCES dim_books(isbn) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES dim_author(author_id) ON DELETE CASCADE,
    PRIMARY KEY (isbn, author_id)
);


CREATE INDEX idx_book_author_author_id ON book_author_bridge(author_id);

-- book_genre_bridge: Links books to their genres/categories
CREATE TABLE book_genre_bridge (
    isbn TEXT NOT NULL REFERENCES dim_books(isbn) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES dim_genre(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (isbn, genre_id)
);

CREATE INDEX idx_book_genre_genre_id ON book_genre_bridge(genre_id);

-- ============================================================================
-- 4. FACT TABLE
-- ============================================================================

-- fact_book_metrics: Metrics and measurements for books (ratings, prices, availability)
CREATE TABLE fact_book_metrics (
    metric_id SERIAL PRIMARY KEY,
    isbn TEXT NOT NULL REFERENCES dim_books(isbn) ON DELETE CASCADE,
    snapshot_date_key INTEGER NOT NULL REFERENCES dim_date(date_key) ON DELETE CASCADE,
    rating_avg DECIMAL(3, 2) CHECK (rating_avg >= 0 AND rating_avg <= 5),
    rating_count INTEGER CHECK (rating_count >= 0),
    edition_count INTEGER CHECK (edition_count >= 0),
    list_price_amount DECIMAL(10, 2) CHECK (list_price_amount >= 0),
    retail_price_amount DECIMAL(10, 2) CHECK (retail_price_amount >= 0),
    currency_code VARCHAR(3),
    is_ebook_available BOOLEAN NOT NULL DEFAULT FALSE,
    saleability_status VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (isbn, snapshot_date_key)
);

CREATE INDEX idx_fact_metrics_isbn ON fact_book_metrics(isbn);
CREATE INDEX idx_fact_metrics_snapshot_date ON fact_book_metrics(snapshot_date_key);
CREATE INDEX idx_fact_metrics_rating ON fact_book_metrics(rating_avg);
CREATE INDEX idx_fact_metrics_created_at ON fact_book_metrics(created_at);

-- ============================================================================
-- 5. SUMMARY OF SCHEMA OBJECTS
-- ============================================================================
-- Tables Created: 9
--   - Job management: jobs (1)
--   - Dimension tables: dim_publisher, dim_author, dim_genre, dim_date, dim_books (5)
--   - Bridge tables: book_author_bridge, book_genre_bridge (2)
--   - Fact table: fact_book_metrics (1)
--
-- Indexes Created: 23
--   - jobs: 3
--   - dim_publisher: 1
--   - dim_author: 2
--   - dim_genre: 1
--   - dim_date: 2
--   - dim_books: 4
--   - book_author_bridge: 1
--   - book_genre_bridge: 1
--   - fact_book_metrics: 4
--
-- Primary Keys: 9
-- Foreign Keys: 8
-- Unique Constraints: 5 (publisher name, author ol_key, genre_name, date full_date, fact metrics isbn+date)
-- Check Constraints: 7
-- ============================================================================

