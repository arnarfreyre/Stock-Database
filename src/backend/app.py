#!/usr/bin/env python3
"""
Flask backend for stock price visualization
Provides REST API endpoints for fetching stock data from SQLite database
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from src.config import DATABASE_PATH, API_HOST, API_PORT, DEBUG_MODE
from src.utils.calculations import calculate_moving_average
from src.analysis.volatility_calculator import calculate_volatility_from_prices
from src.analysis.iv_surface import get_iv_surface_data
from src.analysis.Derivative_basics import VIII_Solvers
from functools import lru_cache
import time
import yfinance as yf

# Get the frontend directory path
FRONTEND_DIR = Path(__file__).parent.parent / 'frontend'

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path='')
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
        
        # Get the table name from stocks_master (handles indices with ^ properly)
        cursor.execute('SELECT table_name FROM stocks_master WHERE ticker = ?', (ticker.upper(),))
        table_result = cursor.fetchone()
        
        if not table_result:
            conn.close()
            return jsonify({'success': False, 'error': f'Table not found for stock {ticker}'}), 404
        
        table_name = table_result['table_name']
        
        # Build query for price data
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


@app.route('/api/available-stocks',methods = ['GET'])
def get_available_stocks():
    try:
        csv_path = Path(__file__).parent.parent / 'data' / 'nasdaq_screener.csv'
        if not csv_path.exists():
            return jsonify({
                'success': False,
                'error': 'nasdaq_screener.csv not found in path, '
                'run utils/get-tickers.py'}),404

        df = pd.read_csv(csv_path)
        headers = df.columns.to_list()

        # Filter out records without symbols and fill missing sector/industry
        available_stocks = (
            df[['symbol','name','sector','industry']]
            .fillna({
                'symbol': 'N/A',
                'sector': 'N/A',
                'industry': 'N/A'
            })
            .to_dict('records')
        )

        return jsonify({
            'success': True,
            'available_stocks': available_stocks,
            'Total Stocks':len(available_stocks)})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


iv_surface_cache = {}
@app.route('/api/iv-surface/<ticker>', methods=['GET'])
def get_iv_surface(ticker):
    """
    Get implied volatility surface data for both calls and puts.

    Returns JSON with surface data suitable for Plotly.js rendering.
    """
    try:
        # Validate ticker exists in reference table
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT symbol, name FROM ticker_reference
            WHERE symbol = ?
        ''', (ticker.upper(),))

        ticker_info = cursor.fetchone()
        conn.close()

        if not ticker_info:
            return jsonify({
                'success': False,
                'error': f'Ticker {ticker.upper()} not found in reference database'
            }), 404

        # Check cache first (5-minute TTL)
        cache_key = ticker.upper()
        current_time = time.time()

        if cache_key in iv_surface_cache:
            cached_data, cached_time = iv_surface_cache[cache_key]
            if current_time - cached_time < 300:  # 5 minutes
                print(f"✅ Returning cached IV surface for {ticker}")
                return jsonify({
                    'success': True,
                    'data': cached_data,
                    'cached': True
                })

        # Get query parameters
        min_expiry = request.args.get('min_expiry', 0, type=int)
        max_expiry = request.args.get('max_expiry', 10, type=int)

        print(f"📊 Calculating IV surface for {ticker}...")

        # Calculate IV surface
        surface_data = get_iv_surface_data(
            ticker.upper(),
            min_expiry_index=min_expiry,
            max_expiry_index=max_expiry
        )

        # Check if we have valid surface data
        if not surface_data['surfaces'].get('calls') and not surface_data['surfaces'].get('puts'):
            return jsonify({
                'success': False,
                'error': f'Insufficient options data for {ticker}. The stock may not have liquid options.',
                'error_code': 'INSUFFICIENT_DATA'
            }), 400

        # Cache the result
        iv_surface_cache[cache_key] = (surface_data, current_time)

        # Limit cache size to 100 entries (remove oldest if needed)
        if len(iv_surface_cache) > 100:
            oldest_key = min(iv_surface_cache.keys(),
                            key=lambda k: iv_surface_cache[k][1])
            del iv_surface_cache[oldest_key]

        return jsonify({
            'success': True,
            'data': surface_data,
            'cached': False
        })

    except ValueError as e:
        error_msg = str(e)
        if "does not have listed options" in error_msg:
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'NO_OPTIONS'
            }), 404
        else:
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'VALIDATION_ERROR'
            }), 400

    except Exception as e:
        print(f"❌ Error calculating IV surface for {ticker}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate IV surface. Please try again.',
            'error_code': 'CALCULATION_ERROR',
            'details': str(e)
        }), 500

@app.route('/api/option/price', methods=['POST'])
def calculate_option_price():
    """
    Calculate option prices and Greeks using Black-Scholes-Merton model.

    Request body:
    {
        "spot_price": 100,       # Current stock price
        "strike_price": 105,     # Strike price
        "time_to_maturity": 1,   # Time to maturity in years
        "risk_free_rate": 0.05,  # Risk-free rate (decimal)
        "volatility": 0.2,       # Volatility (decimal)
        "n_simulations": 100000  # Optional: Monte Carlo simulations
    }
    """
    try:
        data = request.json

        # Validate required parameters
        required = ['spot_price', 'strike_price', 'time_to_maturity', 'risk_free_rate', 'volatility']
        for param in required:
            if param not in data:
                return jsonify({'success': False, 'error': f'Missing required parameter: {param}'}), 400

        S0 = float(data['spot_price'])
        K = float(data['strike_price'])
        T = float(data['time_to_maturity'])
        r = float(data['risk_free_rate'])
        sigma = float(data['volatility'])
        q = float(data.get('dividend_yield', 0))  # Continuous dividend yield
        n_sim = int(data.get('n_simulations', 100000))

        # Validate parameters
        if S0 <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return jsonify({'success': False, 'error': 'All values must be positive'}), 400

        # Create solver instance with dividend yield
        solver = VIII_Solvers(S0=S0, K=K, T=T, r=r, sigma=sigma, n_sim=n_sim, t=0, q=q)

        # Calculate BSM prices
        bsm_call = solver.BSM_call()
        bsm_put = solver.BSM_put()

        # Calculate Greeks
        delta = solver.call_delta()
        gamma = solver.call_gamma()
        vega = solver.call_vega()
        theta = solver.call_theta()

        # Calculate d1 and d2 for display
        d1 = solver.d1()
        d2 = solver.d2()

        # Calculate put Greeks using put-call parity relationships (with dividends)
        import numpy as np
        from scipy.stats import norm
        put_delta = delta - np.exp(-q * T)  # Put delta = Call delta - e^(-qT)
        put_gamma = gamma  # Same as call gamma
        put_vega = vega  # Same as call vega
        # Put theta calculation with dividends
        N_prime_d1 = np.exp((-d1 ** 2) / 2) / np.sqrt(2 * np.pi)
        put_theta = (-np.exp(-q * T) * S0 * N_prime_d1 * sigma / (2 * np.sqrt(T))
                     - q * S0 * np.exp(-q * T) * norm.cdf(-d1)
                     + r * K * np.exp(-r * T) * norm.cdf(-d2))

        # Calculate Monte Carlo prices
        mc_call = solver.mc_call()
        mc_put = solver.mc_put()

        # Calculate moneyness
        moneyness = S0 / K
        if moneyness > 1.02:
            call_moneyness = 'ITM'
            put_moneyness = 'OTM'
        elif moneyness < 0.98:
            call_moneyness = 'OTM'
            put_moneyness = 'ITM'
        else:
            call_moneyness = 'ATM'
            put_moneyness = 'ATM'

        result = {
            'success': True,
            'inputs': {
                'spot_price': S0,
                'strike_price': K,
                'time_to_maturity': T,
                'time_to_maturity_days': int(T * 365),
                'risk_free_rate': r,
                'volatility': sigma,
                'dividend_yield': q,
                'n_simulations': n_sim
            },
            'bsm': {
                'call_price': float(bsm_call),
                'put_price': float(bsm_put),
                'd1': float(d1),
                'd2': float(d2)
            },
            'monte_carlo': {
                'call_price': float(mc_call),
                'put_price': float(mc_put),
                'call_error_pct': abs(mc_call - bsm_call) / bsm_call * 100 if bsm_call > 0 else 0,
                'put_error_pct': abs(mc_put - bsm_put) / bsm_put * 100 if bsm_put > 0 else 0
            },
            'greeks': {
                'call': {
                    'delta': float(delta),
                    'gamma': float(gamma),
                    'vega': float(vega),
                    'theta': float(theta),
                    'theta_daily': float(theta / 365)
                },
                'put': {
                    'delta': float(put_delta),
                    'gamma': float(put_gamma),
                    'vega': float(put_vega),
                    'theta': float(put_theta),
                    'theta_daily': float(put_theta / 365)
                }
            },
            'analysis': {
                'moneyness': float(moneyness),
                'call_moneyness_status': call_moneyness,
                'put_moneyness_status': put_moneyness,
                'intrinsic_value_call': max(S0 - K, 0),
                'intrinsic_value_put': max(K - S0, 0),
                'time_value_call': float(bsm_call) - max(S0 - K, 0),
                'time_value_put': float(bsm_put) - max(K - S0, 0)
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/option/market-prices/<ticker>', methods=['GET'])
def get_market_option_prices(ticker):
    """
    Get real market option prices from Yahoo Finance for comparison.

    Query params:
    - strike: Optional target strike price
    - expiry_index: Optional expiry date index (0 = nearest)
    """
    try:
        stock = yf.Ticker(ticker.upper())

        # Get available expiration dates
        expirations = stock.options
        if not expirations:
            return jsonify({
                'success': False,
                'error': f'{ticker.upper()} does not have listed options'
            }), 404

        # Get expiry index (default to nearest)
        expiry_index = request.args.get('expiry_index', 0, type=int)
        if expiry_index >= len(expirations):
            expiry_index = 0

        expiry_date = expirations[expiry_index]

        # Get option chain
        opt_chain = stock.option_chain(expiry_date)
        calls = opt_chain.calls
        puts = opt_chain.puts

        # Get current stock price
        info = stock.info
        spot_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')

        if not spot_price:
            # Fallback: get from history
            hist = stock.history(period='1d')
            if not hist.empty:
                spot_price = float(hist['Close'].iloc[-1])
            else:
                return jsonify({'success': False, 'error': 'Could not fetch current price'}), 500

        # Get target strike if specified
        target_strike = request.args.get('strike', type=float)

        # Calculate days to expiry
        from datetime import datetime
        expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
        days_to_expiry = (expiry_dt - datetime.now()).days
        time_to_maturity = max(days_to_expiry, 1) / 365.0

        # Filter and format option data
        def format_options(df, target_strike=None):
            options = []
            for _, row in df.iterrows():
                strike = float(row['strike'])

                # If target strike specified, only include close matches
                if target_strike and abs(strike - target_strike) > target_strike * 0.1:
                    continue

                opt = {
                    'strike': strike,
                    'last_price': float(row['lastPrice']) if pd.notna(row['lastPrice']) else None,
                    'bid': float(row['bid']) if pd.notna(row['bid']) else None,
                    'ask': float(row['ask']) if pd.notna(row['ask']) else None,
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                    'open_interest': int(row['openInterest']) if pd.notna(row['openInterest']) else 0,
                    'implied_volatility': float(row['impliedVolatility']) if pd.notna(row['impliedVolatility']) else None
                }

                # Calculate mid price
                if opt['bid'] and opt['ask']:
                    opt['mid_price'] = (opt['bid'] + opt['ask']) / 2
                else:
                    opt['mid_price'] = opt['last_price']

                options.append(opt)

            return sorted(options, key=lambda x: x['strike'])

        call_options = format_options(calls, target_strike)
        put_options = format_options(puts, target_strike)

        # Find ATM options (closest to spot price)
        atm_call = min(call_options, key=lambda x: abs(x['strike'] - spot_price)) if call_options else None
        atm_put = min(put_options, key=lambda x: abs(x['strike'] - spot_price)) if put_options else None

        result = {
            'success': True,
            'ticker': ticker.upper(),
            'spot_price': float(spot_price),
            'expiry_date': expiry_date,
            'days_to_expiry': days_to_expiry,
            'time_to_maturity': time_to_maturity,
            'available_expirations': list(expirations[:10]),  # First 10 expirations
            'atm_call': atm_call,
            'atm_put': atm_put,
            'calls': call_options[:20],  # Limit to 20 strikes
            'puts': put_options[:20]
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Frontend routes
@app.route('/')
def serve_index():
    """Serve the main index.html file."""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files from the frontend directory."""
    # Check if the file exists
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_DIR, path)
    # If it's a directory, try to serve index.html from it
    index_path = file_path / 'index.html'
    if index_path.exists():
        return send_from_directory(FRONTEND_DIR, f'{path}/index.html')
    # Return 404 for non-existent files
    return "Not Found", 404

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