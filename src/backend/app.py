#!/usr/bin/env python3
"""
Flask backend for stock price visualization
Provides REST API endpoints for fetching stock data from SQLite database
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from src.config import DATABASE_PATH, API_HOST, API_PORT, DEBUG_MODE
from src.utils.calculations import calculate_moving_average
from src.analysis.volatility_calculator import calculate_volatility_from_prices

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/search/tickers', methods=['GET'])
def search_tickers():
    """Search for tickers by symbol or company name."""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 results
        
        if not query or len(query) < 1:
            return jsonify({'success': True, 'results': []})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search in ticker_reference table
        # Use LIKE for partial matching, prioritize symbol matches
        search_pattern = f'%{query}%'
        
        cursor.execute('''
            SELECT symbol, name, sector, industry
            FROM ticker_reference
            WHERE symbol LIKE ? OR name LIKE ?
            ORDER BY 
                CASE 
                    WHEN symbol = ? THEN 1
                    WHEN symbol LIKE ? THEN 2
                    WHEN name LIKE ? THEN 3
                    ELSE 4
                END,
                symbol
            LIMIT ?
        ''', (search_pattern, search_pattern, query.upper(), f'{query.upper()}%', f'{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'symbol': row['symbol'],
                'name': row['name'],
                'sector': row['sector'] or 'N/A',
                'industry': row['industry'] or 'N/A'
            })
        
        conn.close()
        return jsonify({'success': True, 'results': results})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/api/stock/<ticker>/check', methods=['GET'])
def check_stock_data(ticker):
    """Check if a stock has data in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if ticker exists in stocks_master (has data)
        cursor.execute('''
            SELECT ticker, company_name, total_records, date_range_start, date_range_end
            FROM stocks_master
            WHERE ticker = ?
        ''', (ticker.upper(),))
        
        stock_data = cursor.fetchone()
        
        # Check if ticker exists in ticker_reference (searchable)
        cursor.execute('''
            SELECT symbol, name, sector, industry
            FROM ticker_reference
            WHERE symbol = ?
        ''', (ticker.upper(),))
        
        ticker_info = cursor.fetchone()
        
        conn.close()
        
        if ticker_info:
            result = {
                'success': True,
                'ticker_exists': True,
                'has_data': stock_data is not None,
                'ticker_info': {
                    'symbol': ticker_info['symbol'],
                    'name': ticker_info['name'],
                    'sector': ticker_info['sector'],
                    'industry': ticker_info['industry']
                }
            }
            
            if stock_data:
                result['data_info'] = {
                    'total_records': stock_data['total_records'],
                    'date_range_start': stock_data['date_range_start'],
                    'date_range_end': stock_data['date_range_end']
                }
            
            return jsonify(result)
        else:
            return jsonify({
                'success': True,
                'ticker_exists': False,
                'has_data': False
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/<ticker>/load', methods=['POST'])
def load_stock_data(ticker):
    """Load stock data from Yahoo Finance for a ticker that doesn't have data yet."""
    try:
        import yfinance as yf
        from src.backend.stock_manager import StockDataManager
        
        # Create manager and connect
        manager = StockDataManager()
        if not manager.connect():
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        # Check if ticker already has data
        if manager.ticker_exists(ticker):
            # Update existing stock
            period = request.json.get('period', '1y') if request.json else '1y'
            data = manager.fetch_stock_data(ticker, period)
            
            if data is None or data.empty:
                manager.close()
                return jsonify({'success': False, 'error': 'Failed to fetch data from Yahoo Finance'}), 500
            
            records = manager.save_price_data(ticker, data)
            manager.close()
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated {records} records for {ticker.upper()}',
                'records_added': records,
                'action': 'updated'
            })
        else:
            # Load new stock data
            period = request.json.get('period', '1y') if request.json else '1y'
            
            # Validate ticker
            if not manager.validate_ticker(ticker):
                manager.close()
                return jsonify({'success': False, 'error': 'Invalid ticker format'}), 400
            
            # Fetch data from Yahoo Finance
            data = manager.fetch_stock_data(ticker, period)
            
            if data is None or data.empty:
                manager.close()
                return jsonify({'success': False, 'error': f'No data found for ticker {ticker.upper()} on Yahoo Finance'}), 404
            
            # Save to database (this will create the table and add to stocks_master)
            records = manager.save_price_data(ticker, data)
            
            manager.close()
            
            return jsonify({
                'success': True,
                'message': f'Successfully loaded {records} records for {ticker.upper()}',
                'records_added': records,
                'action': 'created'
            })
    
    except ImportError:
        return jsonify({'success': False, 'error': 'yfinance not installed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/<ticker>/update', methods=['POST'])
def update_stock_data(ticker):
    """Update stock data by fetching latest from yfinance."""
    # This endpoint now just calls load_stock_data which handles both new and existing stocks
    return load_stock_data(ticker)

@app.route('/api/stock/<ticker>/volatility', methods=['GET'])
def get_stock_volatility(ticker):
    """Calculate and return volatility metrics for a stock."""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        period_days = request.args.get('period', '252')  # Default to 252 trading days (1 year)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table name for the ticker
        cursor.execute('''
            SELECT table_name, company_name FROM stocks_master WHERE ticker = ?
        ''', (ticker.upper(),))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'Stock not found'}), 404
        
        table_name = result['table_name']
        company_name = result['company_name']
        
        # Build query for price data
        if not start_date and not end_date:
            # Default: Get last N trading days
            try:
                period_int = int(period_days)
            except ValueError:
                period_int = 252
                
            query = f'''
                SELECT date, close
                FROM {table_name}
                WHERE date >= (SELECT date
                             FROM {table_name}
                             ORDER BY date
                             DESC LIMIT 1 OFFSET {period_int - 1})
                ORDER BY date ASC
            '''
            params = []
        else:
            # Use provided date range
            query = f'''
                SELECT date, close
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
        
        if not rows or len(rows) < 2:
            conn.close()
            return jsonify({'success': False, 'error': 'Insufficient data for volatility calculation (need at least 2 data points)'}), 400
        
        # Extract prices and dates
        dates = []
        prices = []
        
        for row in rows:
            dates.append(row['date'])
            prices.append(float(row['close']))
        
        conn.close()
        
        # Calculate volatility metrics
        volatility_metrics = calculate_volatility_from_prices(prices, dates)
        
        # Add additional context
        volatility_metrics['ticker'] = ticker.upper()
        volatility_metrics['company_name'] = company_name
        volatility_metrics['date_range'] = {
            'start': dates[0],
            'end': dates[-1]
        }
        
        return jsonify({
            'success': True,
            'ticker': ticker.upper(),
            'metrics': volatility_metrics
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock/<ticker>/cumulative-returns', methods=['GET'])
def get_cumulative_returns(ticker):
    """Calculate and return cumulative returns (overnight vs intraday) for a stock."""
    try:
        # Import the analysis function
        from src.analysis.cumulative_returns import calculate_cumulative_returns
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if stock exists
        cursor.execute('SELECT company_name FROM stocks_master WHERE ticker = ?', (ticker.upper(),))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': f'Stock {ticker} not found in database'}), 404
        
        company_name = result['company_name']
        
        # Build query for price data
        table_name = f"{ticker.upper().replace('-', '_').replace('.', '_')}_prices"
        
        query = f'''
            SELECT date, open, close, high, low, volume
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
        
        conn.close()
        
        if not rows or len(rows) < 2:
            return jsonify({
                'success': False, 
                'error': 'Insufficient data for calculation (need at least 2 trading days)'
            }), 400
        
        # Convert rows to list of dicts for the analysis function
        price_data = []
        for row in rows:
            price_data.append({
                'date': row['date'],
                'open': float(row['open']),
                'close': float(row['close']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row['volume']) if row['volume'] else 0
            })
        
        # Calculate cumulative returns
        results = calculate_cumulative_returns(price_data, ticker.upper())
        
        # Add company name to results
        results['company_name'] = company_name
        
        return jsonify(results)
    
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
    if not DATABASE_PATH.exists():
        print(f"❌ Database not found: {DATABASE_PATH}")
        print("Please run 'python src/database/initialize_db.py' first.")
        exit(1)
    
    print("🚀 Starting Flask server...")
    print("📊 Stock Price Visualization API")
    print("🌐 Server running at http://localhost:5001")
    print("\nAvailable endpoints:")
    print("  GET  /api/search/tickers - Search tickers by symbol or name")
    print("  GET  /api/stocks - List all stocks")
    print("  GET  /api/stock/<ticker>/check - Check if stock has data")
    print("  GET  /api/stock/<ticker>/info - Get stock information")
    print("  GET  /api/stock/<ticker>/prices - Get historical prices")
    print("  GET  /api/stock/<ticker>/volatility - Calculate volatility metrics")
    print("  POST /api/stock/<ticker>/load - Load stock data from Yahoo Finance")
    print("  POST /api/stock/<ticker>/update - Update stock data")
    print("  GET  /api/health - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=DEBUG_MODE, host=API_HOST, port=API_PORT)