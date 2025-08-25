# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Initialize/reset the database (creates stock_market.db)
python init_db.py

# Add stock data to the database
python add_stock_cli.py <TICKER> [period]
# Example: python add_stock_cli.py AAPL 1y
# Periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

# Run the full application (starts Flask server on port 5001)
python run_app.py

# Direct Flask server start (for development)
python src/backend/app.py
```

### Dependencies Installation
```bash
pip install -r requirements.txt
# Required: yfinance, pandas, numpy, flask, flask-cors
```

## Architecture Overview

### Core System Design
The application uses a **dynamic table-per-stock architecture** for optimal database performance. Each stock ticker gets its own dedicated SQLite table (e.g., `AAPL_prices`) rather than storing all price data in a single table. This design provides:
- Fast query performance for individual stocks
- Efficient storage with per-stock indexing
- Scalability for adding new stocks without affecting existing data

### Key Components Integration

1. **Database Layer** (`src/database/`)
   - `initialize_db.py` creates the master schema with `stocks_master` table tracking all stocks
   - Dynamic table creation happens in `StockDataManager` when new stocks are added
   - Each stock table includes OHLC data, volume, and pre-calculated moving averages

2. **Backend API** (`src/backend/`)
   - `app.py` provides Flask REST API endpoints with CORS enabled
   - `stock_manager.py` handles Yahoo Finance integration and database operations
   - API validates tickers against `ticker_reference` table before operations

3. **Configuration** (`src/config/`)
   - Centralized configuration in `config.py` defines all paths and settings
   - Database path, API settings, and default parameters are configured here
   - Moving average windows and other calculation parameters are stored in DB config table

### Data Flow
1. User requests stock via CLI or API
2. `StockDataManager` validates ticker format and checks existing data
3. If new stock: creates dedicated table, fetches from Yahoo Finance
4. Calculates technical indicators (MA-5, MA-20, MA-50, RSI) during import
5. Updates `stocks_master` with metadata and statistics
6. API serves data from individual stock tables with optimized queries

### Key Design Decisions
- **SQLite with dynamic tables**: Chosen for simplicity and performance with per-stock data isolation
- **Pre-calculated indicators**: Moving averages calculated during import for faster queries
- **Modular architecture**: Clear separation between data, backend, frontend, and configuration
- **Yahoo Finance integration**: Using yfinance library for reliable market data

## API Endpoints

All endpoints are served from `http://localhost:5001/api/`

- `GET /api/search/tickers?q=<query>` - Search stocks by symbol or company name
- `GET /api/stocks` - List all stocks in database
- `GET /api/stock/<ticker>/check` - Check if stock exists and has data
- `GET /api/stock/<ticker>/info` - Get stock metadata
- `GET /api/stock/<ticker>/prices` - Get historical prices with moving averages
- `POST /api/stock/<ticker>/load` - Load new stock or update existing data
- `GET /api/health` - API health check

## Database Schema

### Master Tables
- `stocks_master` - Central registry of all stocks with metadata
- `ticker_reference` - Searchable ticker database (symbol, name, sector, industry)
- `config` - System configuration parameters
- `data_sources` - Tracks data fetch history

### Dynamic Stock Tables
Each stock gets a table named `{TICKER}_prices` with:
- Date-indexed OHLC data
- Pre-calculated moving averages (5, 20, 50, 200-day)
- RSI-14 technical indicator
- Volume data

## Important Implementation Details

### Table Naming Convention
Stock tables follow the pattern `{TICKER}_prices` where special characters in tickers are replaced:
- Hyphens (`-`) → underscores (`_`)  
- Periods (`.`) → underscores (`_`)
- Example: `BRK-B` becomes `BRK_B_prices`

### Moving Average Calculation
The 40-day MA is calculated on-the-fly in the API (`app.py`) using `calculate_moving_average()` from `src/utils/calculations.py`, while 5, 20, and 50-day MAs are pre-calculated during data import.

### Error Handling Patterns
- Database operations use try-except with rollback on failure
- API endpoints return consistent JSON with `success` flag and `error` field
- Yahoo Finance failures are handled gracefully with user-friendly messages

## Frontend Structure

The frontend (in `src/frontend/`) uses vanilla JavaScript with Chart.js for visualization. Key files:
- `index.html` - Main application interface
- `app.js` - JavaScript application logic and API integration
- `styles.css` - Application styling

The frontend dynamically loads from CDN:
- Chart.js for interactive price charts
- Bootstrap for responsive design

## Testing

Currently no test suite exists. When implementing tests, consider:
- Unit tests for calculation functions in `src/utils/calculations.py`
- Integration tests for database operations in `StockDataManager`
- API endpoint tests for Flask routes