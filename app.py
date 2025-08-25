#!/usr/bin/env python3
"""
Flask backend for stock price visualization
Provides REST API endpoints for fetching stock data from SQLite database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DATABASE_PATH = 'stock_market.db'

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_moving_average(prices, window):
    """Calculate moving average for given window size."""
    if len(prices) < window:
        return [None] * len(prices)
    
    ma = []
    for i in range(len(prices)):
        if i < window - 1:
            ma.append(None)
        else:
            avg = sum(prices[i - window + 1:i + 1]) / window
            ma.append(round(avg, 4))
    return ma

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """Get list of all stocks in database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, company_name, sector, exchange, 
                   total_records, date_range_start, date_range_end
            FROM stocks_master
            WHERE is_active = 1
            ORDER BY ticker
        ''')
        
        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'ticker': row['ticker'],
                'company_name': row['company_name'],
                'sector': row['sector'],
                'exchange': row['exchange'],
                'total_records': row['total_records'],
                'date_range_start': row['date_range_start'],
                'date_range_end': row['date_range_end']
            })
        
        conn.close()
        return jsonify({'success': True, 'stocks': stocks})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/<ticker>/info', methods=['GET'])
def get_stock_info(ticker):
    """Get stock information and metadata."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, company_name, sector, exchange, currency,
                   total_records, date_range_start, date_range_end, last_updated
            FROM stocks_master
            WHERE ticker = ?
        ''', (ticker.upper(),))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        info = {
            'ticker': row['ticker'],
            'company_name': row['company_name'],
            'sector': row['sector'],
            'exchange': row['exchange'],
            'currency': row['currency'],
            'total_records': row['total_records'],
            'date_range_start': row['date_range_start'],
            'date_range_end': row['date_range_end'],
            'last_updated': row['last_updated']
        }
        
        conn.close()
        return jsonify({'success': True, 'info': info})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/<ticker>/prices', methods=['GET'])
def get_stock_prices(ticker):
    """Get historical prices for a stock with moving averages."""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table name for the ticker
        cursor.execute('''
            SELECT table_name FROM stocks_master WHERE ticker = ?
        ''', (ticker.upper(),))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        table_name = result['table_name']
        
        # Build query for price data
        query = f'''
            SELECT date, open, high, low, close, volume, 
                   ma_5, ma_20, ma_50
            FROM {table_name}
        '''
        
        params = []
        conditions = []
        
        if start_date:
            conditions.append('date >= ?')
            params.append(start_date)
        
        if end_date:
            conditions.append('date <= ?')
            params.append(end_date)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY date ASC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return jsonify({'success': False, 'error': 'No data found for specified date range'}), 404
        
        # Process data
        dates = []
        prices = []
        volumes = []
        opens = []
        highs = []
        lows = []
        ma_5 = []
        ma_20 = []
        ma_50 = []
        
        for row in rows:
            dates.append(row['date'])
            prices.append(float(row['close']))
            volumes.append(int(row['volume']) if row['volume'] else 0)
            opens.append(float(row['open']) if row['open'] else None)
            highs.append(float(row['high']) if row['high'] else None)
            lows.append(float(row['low']) if row['low'] else None)
            ma_5.append(float(row['ma_5']) if row['ma_5'] else None)
            ma_20.append(float(row['ma_20']) if row['ma_20'] else None)
            ma_50.append(float(row['ma_50']) if row['ma_50'] else None)
        
        # Calculate 40-day moving average
        ma_40 = calculate_moving_average(prices, 40)
        
        # Prepare response data
        data = {
            'dates': dates,
            'prices': prices,
            'volumes': volumes,
            'open': opens,
            'high': highs,
            'low': lows,
            'ma_5': ma_5,
            'ma_20': ma_20,
            'ma_40': ma_40,  # Calculated 40-day MA
            'ma_50': ma_50,
            'ticker': ticker.upper(),
            'total_points': len(dates)
        }
        
        conn.close()
        return jsonify({'success': True, 'data': data})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/<ticker>/update', methods=['POST'])
def update_stock_data(ticker):
    """Update stock data by fetching latest from yfinance."""
    try:
        import yfinance as yf
        from add_stock import StockDataManager
        
        # Create manager and connect
        manager = StockDataManager()
        if not manager.connect():
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        # Check if ticker exists
        if not manager.ticker_exists(ticker):
            manager.close()
            return jsonify({'success': False, 'error': 'Stock not found in database'}), 404
        
        # Fetch latest data (default 1 year)
        period = request.json.get('period', '1y') if request.json else '1y'
        data = manager.fetch_stock_data(ticker, period)
        
        if data is None or data.empty:
            manager.close()
            return jsonify({'success': False, 'error': 'Failed to fetch data from Yahoo Finance'}), 500
        
        # Save to database
        records = manager.save_price_data(ticker, data)
        
        manager.close()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully updated {records} records for {ticker.upper()}',
            'records_updated': records
        })
    
    except ImportError:
        return jsonify({'success': False, 'error': 'yfinance not installed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM stocks_master')
        stock_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'stocks_count': stock_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found: {DATABASE_PATH}")
        print("Please run 'python create_database.py' first.")
        exit(1)
    
    print("🚀 Starting Flask server...")
    print("📊 Stock Price Visualization API")
    print("🌐 Server running at http://localhost:5001")
    print("\nAvailable endpoints:")
    print("  GET  /api/stocks - List all stocks")
    print("  GET  /api/stock/<ticker>/info - Get stock information")
    print("  GET  /api/stock/<ticker>/prices - Get historical prices")
    print("  POST /api/stock/<ticker>/update - Update stock data")
    print("  GET  /api/health - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5001)