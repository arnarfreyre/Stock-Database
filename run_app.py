#!/usr/bin/env python3
"""
Main entry point for running the Stock Market Application
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.app import app
from src.config import API_HOST, API_PORT, DEBUG_MODE, DATABASE_PATH

def main():
    """Main function to run the Flask application."""
    
    # Check if database exists
    if not DATABASE_PATH.exists():
        print(f"❌ Database not found: {DATABASE_PATH}")
        print("\nTo initialize the database, run:")
        print("  python init_db.py")
        return 1
    
    print("🚀 Starting Stock Market Application...")
    print(f"📊 Database: {DATABASE_PATH}")
    print(f"🌐 Server: http://{API_HOST}:{API_PORT}")
    print("\nPress Ctrl+C to stop the server")
    
    # Run the Flask app
    app.run(debug=DEBUG_MODE, host=API_HOST, port=API_PORT)
    return 0

if __name__ == '__main__':
    sys.exit(main())