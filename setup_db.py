import os
import sys

# Try to import psycopg2 for PostgreSQL connection
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("Error: 'psycopg2' module not found.")
    print("Please install it running: pip install psycopg2-binary")
    sys.exit(1)

# Database Configuration - basic defaults for local dev, usually overridden by env vars
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "gt_ia_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

SCHEMA_FILE = "schema.sql"

def create_database_if_not_exists():
    """Connects to default 'postgres' db to check and create target db."""
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Database '{DB_NAME}' does not exist. Creating...")
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to check/create database: {e}")
        sys.exit(1)

def run_schema_migration():
    """Applies the SQL schema to the target database."""
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: Schema file '{SCHEMA_FILE}' not found.")
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
        )
        # Enable autocommit for certain operations if needed, 
        # but typically schema changes can be in a transaction.
        # conn.autocommit = True 
        
        cur = conn.cursor()
        
        print(f"Reading schema from {SCHEMA_FILE}...")
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        print("Executing schema script...")
        cur.execute(sql_script)
        conn.commit()
        
        print("Schema applied successfully! Tables created.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to apply schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("--- GT-IA Database Setup ---")
    create_database_if_not_exists()
    run_schema_migration()
    print("--- Setup Complete ---")
