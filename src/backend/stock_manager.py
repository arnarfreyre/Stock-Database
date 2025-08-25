#!/usr/bin/env python3
"""
Stock Data Manager - Manages stock data operations with dynamic table creation
Each stock gets its own dedicated table for optimal performance
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import sqlite3
import os
from datetime import datetime, timedelta
import re
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, List
from src.config import DATABASE_PATH, DEFAULT_PERIOD

class StockDataManager:
    """Manages stock data operations with dynamic table creation."""
    
    def __init__(self, db_path=None):
        """
        Initialize the StockDataManager.
        
        Args:
            db_path (str): Path to the SQLite database
        """
        self.db_path = db_path if db_path else str(DATABASE_PATH)
        self.conn = None
        self.cursor = None
        
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            print("Please run 'python src/database/initialize_db.py' first.")
            return False
            
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            print(f"❌ Database connection error: {e}")
            return False
            
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            
    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate ticker symbol format.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Ticker should be 1-10 alphanumeric characters
        pattern = r'^[A-Z0-9\-\.]{1,10}$'
        return bool(re.match(pattern, ticker.upper()))
        
    def sanitize_table_name(self, ticker: str) -> str:
        """
        Convert ticker to valid table name.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            str: Sanitized table name
        """
        # Replace special characters with underscores
        table_name = ticker.upper().replace('-', '_').replace('.', '_')
        return f"{table_name}_prices"
        
    def ticker_exists(self, ticker: str) -> bool:
        """
        Check if ticker already exists in database.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            bool: True if exists, False otherwise
        """
        self.cursor.execute("SELECT COUNT(*) FROM stocks_master WHERE ticker = ?", (ticker.upper(),))
        return self.cursor.fetchone()[0] > 0
        
    def create_stock_table(self, ticker: str) -> bool:
        """
        Create a dedicated table for a specific stock.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            bool: True if successful, False otherwise
        """
        table_name = self.sanitize_table_name(ticker)
        
        try:
            # Create the stock-specific table
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    date DATE PRIMARY KEY NOT NULL,
                    open DECIMAL(10,4),
                    high DECIMAL(10,4),
                    low DECIMAL(10,4),
                    close DECIMAL(10,4) NOT NULL,
                    adjusted_close DECIMAL(10,4),
                    volume INTEGER,
                    ma_5 DECIMAL(10,4),
                    ma_20 DECIMAL(10,4),
                    ma_50 DECIMAL(10,4),
                    ma_200 DECIMAL(10,4),
                    rsi_14 DECIMAL(5,2),
                    macd DECIMAL(10,4),
                    macd_signal DECIMAL(10,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (open > 0 OR open IS NULL),
                    CHECK (high > 0 OR high IS NULL),
                    CHECK (low > 0 OR low IS NULL),
                    CHECK (close > 0),
                    CHECK (volume >= 0 OR volume IS NULL),
                    CHECK (high >= low OR high IS NULL OR low IS NULL)
                )
            '''
            self.cursor.execute(create_table_sql)
            
            # Create indexes for the new table
            self.cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{table_name}_date 
                ON {table_name}(date DESC)
            ''')
            
            # Create a view for latest prices of this stock
            self.cursor.execute(f'''
                CREATE VIEW IF NOT EXISTS {ticker.upper()}_latest AS
                SELECT 
                    sm.ticker,
                    sm.company_name,
                    sm.sector,
                    sm.exchange,
                    p.date,
                    p.open,
                    p.high,
                    p.low,
                    p.close,
                    p.volume,
                    p.ma_5,
                    p.ma_20,
                    p.ma_50,
                    p.ma_200
                FROM stocks_master sm
                INNER JOIN {table_name} p ON p.date = (
                    SELECT MAX(date) FROM {table_name}
                )
                WHERE sm.ticker = '{ticker.upper()}'
            ''')
            
            print(f"✓ Created table '{table_name}' for {ticker}")
            print(f"✓ Created view '{ticker.upper()}_latest' for quick access")
            
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Error creating table: {e}")
            return False
            
    def calculate_moving_averages(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate moving averages for the price data.
        
        Args:
            prices (pd.DataFrame): DataFrame with price data
            
        Returns:
            pd.DataFrame: DataFrame with added moving average columns
        """
        # Get MA periods from config
        self.cursor.execute("SELECT value FROM config WHERE key = 'ma_periods'")
        ma_periods_str = self.cursor.fetchone()
        
        if ma_periods_str:
            ma_periods = [int(p) for p in ma_periods_str[0].split(',')]
        else:
            ma_periods = [5, 20, 50, 200]
            
        # Calculate moving averages
        for period in ma_periods:
            col_name = f'ma_{period}'
            if len(prices) >= period:
                prices[col_name] = prices['Close'].rolling(window=period).mean()
            else:
                prices[col_name] = None
                
        # Calculate RSI (14-day)
        if len(prices) >= 14:
            delta = prices['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            prices['rsi_14'] = 100 - (100 / (1 + rs))
        else:
            prices['rsi_14'] = None
            
        return prices
        
    def fetch_stock_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Fetch stock data from Yahoo Finance.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for data
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with stock data or None if error
        """
        try:
            print(f"\n📊 Fetching data for {ticker}...")
            
            # Create ticker object
            stock = yf.Ticker(ticker)
            
            # Fetch historical data
            hist = stock.history(period=period)
            
            if hist.empty:
                print(f"❌ No data found for ticker: {ticker}")
                return None
                
            # Get stock info
            info = stock.info
            
            # Store company info
            company_name = info.get('longName', info.get('shortName', ticker))
            sector = info.get('sector', 'Unknown')
            exchange = info.get('exchange', 'Unknown')
            currency = info.get('currency', 'USD')
            
            table_name = self.sanitize_table_name(ticker)
            
            # Check if this is a new stock
            is_new_stock = not self.ticker_exists(ticker)
            
            if is_new_stock:
                # Create the dedicated table for this stock
                if not self.create_stock_table(ticker):
                    return None
                    
                # Add to master table
                self.cursor.execute('''
                    INSERT INTO stocks_master 
                    (ticker, company_name, sector, exchange, currency, table_name, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ticker.upper(), company_name, sector, exchange, currency, table_name, datetime.now()))
                print(f"✓ Added {ticker} ({company_name}) to stocks master")
                
            else:
                # Update existing stock info
                self.cursor.execute('''
                    UPDATE stocks_master 
                    SET company_name = ?, sector = ?, exchange = ?, currency = ?, last_updated = ?
                    WHERE ticker = ?
                ''', (company_name, sector, exchange, currency, datetime.now(), ticker.upper()))
                print(f"✓ Updated {ticker} information in master table")
                
            # Calculate technical indicators
            hist = self.calculate_moving_averages(hist)
            
            return hist
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None
            
    def save_price_data(self, ticker: str, data: pd.DataFrame) -> int:
        """
        Save price data to the stock's dedicated table.
        
        Args:
            ticker (str): Stock ticker symbol
            data (pd.DataFrame): DataFrame with price data
            
        Returns:
            int: Number of records saved
        """
        table_name = self.sanitize_table_name(ticker)
        records_saved = 0
        records_updated = 0
        
        try:
            for date, row in data.iterrows():
                # Check if record exists
                self.cursor.execute(f'''
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE date = ?
                ''', (date.date(),))
                
                exists = self.cursor.fetchone()[0] > 0
                
                # Prepare data
                price_data = (
                    date.date(),
                    float(row['Open']) if not pd.isna(row['Open']) else None,
                    float(row['High']) if not pd.isna(row['High']) else None,
                    float(row['Low']) if not pd.isna(row['Low']) else None,
                    float(row['Close']),
                    float(row['Close']),  # Using Close as adjusted_close
                    int(row['Volume']) if not pd.isna(row['Volume']) else None,
                    float(row['ma_5']) if 'ma_5' in row and not pd.isna(row['ma_5']) else None,
                    float(row['ma_20']) if 'ma_20' in row and not pd.isna(row['ma_20']) else None,
                    float(row['ma_50']) if 'ma_50' in row and not pd.isna(row['ma_50']) else None,
                    float(row['ma_200']) if 'ma_200' in row and not pd.isna(row['ma_200']) else None,
                    float(row['rsi_14']) if 'rsi_14' in row and not pd.isna(row['rsi_14']) else None
                )
                
                if exists:
                    # Update existing record
                    self.cursor.execute(f'''
                        UPDATE {table_name} 
                        SET open = ?, high = ?, low = ?, close = ?, adjusted_close = ?,
                            volume = ?, ma_5 = ?, ma_20 = ?, ma_50 = ?, ma_200 = ?, rsi_14 = ?
                        WHERE date = ?
                    ''', price_data[1:] + (date.date(),))
                    records_updated += 1
                else:
                    # Insert new record
                    self.cursor.execute(f'''
                        INSERT INTO {table_name} 
                        (date, open, high, low, close, adjusted_close, 
                         volume, ma_5, ma_20, ma_50, ma_200, rsi_14)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', price_data)
                    records_saved += 1
                    
            # Update master table statistics
            self.cursor.execute(f'''
                UPDATE stocks_master 
                SET total_records = (SELECT COUNT(*) FROM {table_name}),
                    date_range_start = (SELECT MIN(date) FROM {table_name}),
                    date_range_end = (SELECT MAX(date) FROM {table_name})
                WHERE ticker = ?
            ''', (ticker.upper(),))
            
            # Log data source
            self.cursor.execute('''
                INSERT INTO data_sources 
                (ticker, source_name, records_added, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                ticker.upper(),
                'yfinance',
                records_saved + records_updated,
                data.index[0].date(),
                data.index[-1].date(),
                'success'
            ))
            
            self.conn.commit()
            
            print(f"\n✅ Data saved to '{table_name}' table!")
            print(f"   New records: {records_saved}")
            print(f"   Updated records: {records_updated}")
            print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")
            
            return records_saved + records_updated
            
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            self.conn.rollback()
            return 0
            
    def display_latest_data(self, ticker: str):
        """
        Display the latest data for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
        """
        try:
            # Query the stock-specific view
            view_name = f"{ticker.upper()}_latest"
            self.cursor.execute(f'SELECT * FROM {view_name}')
            
            result = self.cursor.fetchone()
            
            if result:
                print(f"\n📈 Latest Data for {ticker}:")
                print(f"   Company: {result[1]}")
                print(f"   Sector: {result[2]}")
                print(f"   Exchange: {result[3]}")
                print(f"   Date: {result[4]}")
                print(f"   Open: ${result[5]:.2f}" if result[5] else "   Open: N/A")
                print(f"   High: ${result[6]:.2f}" if result[6] else "   High: N/A")
                print(f"   Low: ${result[7]:.2f}" if result[7] else "   Low: N/A")
                print(f"   Close: ${result[8]:.2f}")
                print(f"   Volume: {result[9]:,}" if result[9] else "   Volume: N/A")
                
                print(f"\n📊 Moving Averages:")
                print(f"   MA-5: ${result[10]:.2f}" if result[10] else "   MA-5: N/A")
                print(f"   MA-20: ${result[11]:.2f}" if result[11] else "   MA-20: N/A")
                print(f"   MA-50: ${result[12]:.2f}" if result[12] else "   MA-50: N/A")
                print(f"   MA-200: ${result[13]:.2f}" if result[13] else "   MA-200: N/A")
                
                # Get table statistics
                table_name = self.sanitize_table_name(ticker)
                self.cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                record_count = self.cursor.fetchone()[0]
                print(f"\n📋 Table Statistics:")
                print(f"   Table Name: {table_name}")
                print(f"   Total Records: {record_count}")
                
        except sqlite3.Error as e:
            print(f"❌ Error retrieving data: {e}")
            
    def list_all_stocks(self):
        """Display all stocks in the database."""
        try:
            self.cursor.execute('''
                SELECT ticker, company_name, sector, total_records, 
                       date_range_start, date_range_end, table_name
                FROM stocks_master
                ORDER BY ticker
            ''')
            
            stocks = self.cursor.fetchall()
            
            if stocks:
                print("\n📊 Stocks in Database:")
                print("-" * 80)
                for stock in stocks:
                    print(f"\n{stock[0]} - {stock[1]}")
                    print(f"   Sector: {stock[2]}")
                    print(f"   Records: {stock[3] or 0}")
                    print(f"   Date Range: {stock[4]} to {stock[5]}" if stock[4] else "   No data yet")
                    print(f"   Table: {stock[6]}")
                print("-" * 80)
                print(f"Total stocks: {len(stocks)}")
            else:
                print("\n📭 No stocks in database yet")
                
        except sqlite3.Error as e:
            print(f"❌ Error listing stocks: {e}")


def get_user_input() -> Tuple[str, str]:
    """
    Get ticker and period from user input.
    
    Returns:
        Tuple[str, str]: Ticker symbol and time period
    """
    print("\n" + "=" * 60)
    print("ADD STOCK TO DATABASE (Dynamic Tables)")
    print("=" * 60)
    
    # Get ticker
    while True:
        ticker = input("\nEnter stock ticker (or 'list' to see all stocks, 'quit' to exit): ").strip().upper()
        
        if ticker.lower() == 'quit':
            return None, None
            
        if ticker.lower() == 'list':
            return 'LIST', None
            
        manager = StockDataManager()
        if manager.connect():
            if manager.validate_ticker(ticker):
                manager.close()
                break
            else:
                print(f"❌ Invalid ticker format: {ticker}")
                print("   Ticker should be 1-10 alphanumeric characters")
            manager.close()
    
    # Get time period
    print("\nSelect time period for historical data:")
    print("  1. 1 month")
    print("  2. 3 months")
    print("  3. 6 months")
    print("  4. 1 year (default)")
    print("  5. 2 years")
    print("  6. 5 years")
    print("  7. Maximum available")
    
    choice = input("\nEnter choice (1-7) or press Enter for default: ").strip()
    
    period_map = {
        '1': '1mo',
        '2': '3mo',
        '3': '6mo',
        '4': '1y',
        '5': '2y',
        '6': '5y',
        '7': 'max'
    }
    
    period = period_map.get(choice, '1y')
    
    return ticker, period


def main():
    """Main function to run the stock data addition process."""
    
    print("\n🚀 Stock Data Manager - Dynamic Table System")
    print("Each stock gets its own dedicated table for optimal performance")
    print("Commands: 'list' - show all stocks, 'quit' - exit\n")
    
    while True:
        # Get user input
        ticker, period = get_user_input()
        
        if ticker is None:
            print("\n👋 Goodbye!")
            break
            
        # Create manager
        manager = StockDataManager()
        
        if not manager.connect():
            continue
            
        try:
            # Handle list command
            if ticker == 'LIST':
                manager.list_all_stocks()
                manager.close()
                continue
                
            # Check if ticker exists and ask for confirmation
            if manager.ticker_exists(ticker):
                response = input(f"\n⚠️  {ticker} already exists. Update with latest data? (y/n): ")
                if response.lower() != 'y':
                    manager.close()
                    continue
            else:
                print(f"\n✨ Creating new table for {ticker}...")
                    
            # Fetch and save data
            data = manager.fetch_stock_data(ticker, period)
            
            if data is not None and not data.empty:
                records = manager.save_price_data(ticker, data)
                
                if records > 0:
                    # Display latest data
                    manager.display_latest_data(ticker)
                    
            # Ask if user wants to add another stock
            another = input("\n\nAdd another stock? (y/n): ").strip().lower()
            if another != 'y':
                print("\n👋 Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled by user")
            break
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            
        finally:
            manager.close()


if __name__ == "__main__":
    # Check for yfinance installation
    try:
        import yfinance
    except ImportError:
        print("❌ yfinance library not installed.")
        print("Please run: pip install yfinance pandas numpy")
        sys.exit(1)
        
    main()