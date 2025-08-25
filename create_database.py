#!/usr/bin/env python3
"""
create_database.py - Creates an SQLite database for stock market data storage
Each stock gets its own table for optimized performance and organization
"""

import sqlite3
import os
from datetime import datetime

def create_database(db_path='stock_market.db'):
    """
    Creates the stock market database with master tables.
    Individual stock tables are created dynamically when stocks are added.
    
    Args:
        db_path (str): Path to the database file
    """
    
    # Check if database already exists
    if os.path.exists(db_path):
        response = input(f"Database '{db_path}' already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Database creation cancelled.")
            return False
        else:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
    
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create master stocks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks_master (
                ticker TEXT PRIMARY KEY NOT NULL,
                company_name TEXT,
                sector TEXT,
                exchange TEXT,
                currency TEXT DEFAULT 'USD',
                table_name TEXT NOT NULL,
                added_date DATE DEFAULT (date('now')),
                last_updated TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                total_records INTEGER DEFAULT 0,
                date_range_start DATE,
                date_range_end DATE,
                CHECK (length(ticker) <= 10)
            )
        ''')
        
        print("✓ Created 'stocks_master' table")
        
        # Create configuration table for system settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY NOT NULL,
                value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("✓ Created 'config' table")
        
        # Create data_sources table to track where data comes from
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                source_name TEXT NOT NULL,
                fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                records_added INTEGER,
                start_date DATE,
                end_date DATE,
                status TEXT CHECK(status IN ('success', 'partial', 'failed')),
                error_message TEXT,
                FOREIGN KEY (ticker) REFERENCES stocks_master(ticker) ON DELETE CASCADE
            )
        ''')
        
        print("✓ Created 'data_sources' table")
        
        # Create index for data sources
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_sources_ticker 
            ON data_sources(ticker)
        ''')
        
        # Create index for stocks master
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stocks_master_ticker 
            ON stocks_master(ticker)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stocks_master_table_name 
            ON stocks_master(table_name)
        ''')
        
        print("✓ Created indexes for optimized queries")
        
        # Insert default configuration values
        default_configs = [
            ('ma_periods', '5,20,50,200', 'Moving average periods to calculate'),
            ('default_data_source', 'yfinance', 'Default API for fetching stock data'),
            ('max_records_per_fetch', '500', 'Maximum records to fetch per API call'),
            ('database_version', '1.0', 'Database schema version')
        ]
        
        for key, value, description in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO config (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, description))
        
        print("✓ Inserted default configuration")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Database created successfully!")
        print(f"📁 Location: {os.path.abspath(db_path)}")
        
        # Display database statistics
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📊 Database Statistics:")
        print(f"   Tables created: {len(tables)}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchall()
        print(f"   Indexes created: {len(indexes)}")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        print(f"   Views created: {len(views)}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def verify_database(db_path='stock_market.db'):
    """
    Verifies that the database was created correctly.
    
    Args:
        db_path (str): Path to the database file
    """
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print("\n🔍 Database Verification:")
        print("\nTables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        # Check if foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        print(f"\nForeign Keys: {'Enabled' if fk_status else 'Disabled'}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Verification error: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("STOCK MARKET DATABASE CREATOR")
    print("=" * 60)
    
    # Check for force flag
    force = '--force' in sys.argv or '-f' in sys.argv
    
    # If force flag is set and database exists, remove it
    if force and os.path.exists('stock_market.db'):
        os.remove('stock_market.db')
        print("Force flag detected - removed existing database")
    
    # Create the database
    if create_database():
        # Verify the database was created correctly
        verify_database()
        print("\n✨ Database is ready for use!")
        print("\nNext steps:")
        print("1. Run 'python add_stock.py' to add stock data")
        print("2. Use SQLite browser or Python to query the data")
    else:
        print("\n❌ Database creation failed.")