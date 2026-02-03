import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "gt_ia_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def migrate():
    try:
        conn = psycopg2.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, dbname=DB_NAME)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Migrating schema...")
        # 1. Add estimated_savings to ai_decision_logs
        try:
            cur.execute("ALTER TABLE ai_decision_logs ADD COLUMN IF NOT EXISTS estimated_savings DECIMAL(15, 2) DEFAULT 0.00;")
            print("Added estimated_savings column.")
        except Exception as e:
            print(f"Column estimated_savings already exists or error: {e}")

        # 2. Fix Fiscal Data Columns check (Just informing, ALTER COLUMN is risky without type check, but we are fixing inserts)
        # Note: If we need to rename columns in DB from old schema 'revenue' to 'revenue_amount', we should do it here.
        # Checking if 'revenue' exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='fiscal_data' AND column_name='revenue_amount'")
        if not cur.fetchone():
             # Rename if old exists
             cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='fiscal_data' AND column_name='revenue'")
             if cur.fetchone():
                print("Renaming revenue -> revenue_amount")
                cur.execute("ALTER TABLE fiscal_data RENAME COLUMN revenue TO revenue_amount;")
                # assume others need rename too?
                cur.execute("ALTER TABLE fiscal_data RENAME COLUMN payroll TO payroll_amount;")
                cur.execute("ALTER TABLE fiscal_data RENAME COLUMN taxes_paid TO tax_withholding_amount;")
                cur.execute("ALTER TABLE fiscal_data RENAME COLUMN other_costs TO operational_costs_amount;")
                # period string to date conversion is tricky if data exists.
                # simpler: Drop table if dev
        
        conn.commit()
        cur.close()
        conn.close()
        print("Migration done.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
