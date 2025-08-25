#!/usr/bin/env python3
"""
Initialize the database for the Stock Market Application
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.initialize_db import create_database, import_ticker_data
from src.config import DATABASE_PATH, TICKER_DATA_PATH

def main():
    """Main function to initialize the database."""
    
    print("🔨 Stock Market Database Initialization")
    print("=" * 50)
    
    # Create database
    print("\n📊 Creating database structure...")
    if create_database():
        print("✅ Database created successfully!")
        
        # Import ticker data if available
        if TICKER_DATA_PATH.exists():
            print(f"\n📥 Importing ticker data from {TICKER_DATA_PATH}...")
            if import_ticker_data():
                print("✅ Ticker data imported successfully!")
            else:
                print("⚠️ Ticker data import failed")
        else:
            print(f"\n⚠️ Ticker data file not found: {TICKER_DATA_PATH}")
            print("   Skipping ticker data import.")
        
        print("\n✅ Database initialization complete!")
        print(f"   Database location: {DATABASE_PATH}")
        print("\nTo run the application:")
        print("  python run_app.py")
    else:
        print("❌ Database initialization failed")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())