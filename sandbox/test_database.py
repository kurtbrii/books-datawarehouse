"""
Script to execute schema.sql and create all database tables.
"""

import sys
import os

# Add parent directory to path to import config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import Config


def run_schema():
    """Execute schema.sql to create all database tables."""

    # Get database connection string
    db_url = Config.get_connection_string()

    if not db_url:
        raise ValueError(
            "DATABASE_URL not found in environment variables. "
            "Please set it in your .env file."
        )

    # Get the path to schema.sql (in parent directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(project_root, "sql", "schema.sql")

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Read the schema file
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Connect to database and execute schema
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(db_url)

        # Set isolation level to allow DROP TABLE statements
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()

        print("Executing schema.sql...")
        cursor.execute(schema_sql)

        print("✅ Schema executed successfully!")

        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")

        cursor.close()
        conn.close()

        print("\n✅ Database schema setup complete!")

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    run_schema()
