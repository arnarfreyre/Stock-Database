#!/usr/bin/env python3
"""
Command-line interface for adding stocks to the database
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.stock_manager import StockDataManager
from src.config import DEFAULT_PERIOD

def main():
    """Main function for adding stocks via CLI."""
    
    if len(sys.argv) < 2:
        print("Usage: python add_stock_cli.py <TICKER> [period]")
        print("\nPeriod options:")
        print("  1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max")
        print(f"  Default: {DEFAULT_PERIOD}")
        print("\nExample:")
        print("  python add_stock_cli.py AAPL 1y")
        return 1
    
    ticker = sys.argv[1].upper()
    period = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PERIOD
    
    print(f"📊 Adding stock: {ticker}")
    print(f"📅 Period: {period}")
    print("-" * 40)
    
    # Create manager and add stock
    manager = StockDataManager()
    
    if not manager.connect():
        print("❌ Failed to connect to database")
        return 1
    
    try:
        # Check if ticker already exists
        if manager.ticker_exists(ticker):
            print(f"⚠️ Stock {ticker} already exists in database")
            response = input("Update with latest data? (y/n): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                manager.close()
                return 0
        
        # Fetch and save data
        print(f"📥 Fetching data from Yahoo Finance...")
        data = manager.fetch_stock_data(ticker, period)
        
        if data is None or data.empty:
            print(f"❌ No data found for {ticker}")
            manager.close()
            return 1
        
        print(f"💾 Saving {len(data)} records to database...")
        records = manager.save_price_data(ticker, data)
        
        print(f"✅ Successfully added {records} records for {ticker}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        manager.close()
        return 1
    
    manager.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())