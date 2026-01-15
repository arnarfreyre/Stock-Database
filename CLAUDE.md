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
# Core: yfinance, pandas, numpy, flask, flask-cors
# Analysis: jax, jaxlib, scipy (for IV surface calculations with automatic differentiation)
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
- `GET /api/stock/<ticker>/volatility` - Calculate volatility metrics
- `GET /api/stock/<ticker>/cumulative-returns` - Calculate overnight vs intraday returns
- `GET /api/iv-surface/<ticker>` - Calculate implied volatility surface (calls and puts)
- `POST /api/stock/<ticker>/load` - Load new stock or update existing data
- `POST /api/stock/<ticker>/update` - Update existing stock data
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
- Carets (`^`) → underscores (`_`) for indices
- Example: `BRK-B` becomes `BRK_B_prices`, `^GSPC` becomes `_GSPC_prices`

### Moving Average Calculation
The 40-day MA is calculated on-the-fly in the API (`app.py`) using `calculate_moving_average()` from `src/utils/calculations.py`, while 5, 20, 50, and 200-day MAs are pre-calculated during data import.

### Error Handling Patterns
- Database operations use try-except with rollback on failure
- API endpoints return consistent JSON with `success` flag and `error` field
- Yahoo Finance failures are handled gracefully with user-friendly messages

## Frontend Structure

The frontend (in `src/frontend/`) uses vanilla JavaScript with Chart.js for visualization. Key files:
- `index.html` - Main application interface
- `app.js` - JavaScript application logic and API integration
- `styles.css` - Application styling
- `my-tools.html` - Main toolbox page displaying available financial calculators

The frontend dynamically loads from CDN:
- Chart.js for interactive price charts
- Bootstrap for responsive design

## Toolbox Architecture

### Overview
The toolbox is a collection of financial engineering calculators and analysis tools accessible through the web interface. Each tool follows a consistent architecture pattern where **computation-heavy operations are handled by Python scripts** while the **toolbox frontend displays results interactively**.

### Directory Structure
```
src/
├── frontend/
│   ├── Toolbox/                    # HTML interfaces for individual tools
│   │   ├── volatility-calculator.html
│   │   └── cumulative-returns.html
│   ├── js/
│   │   ├── solvers-config.js      # Tool registry and configuration
│   │   └── render-utils.js        # Dynamic card rendering utilities
│   └── my-tools.html              # Main toolbox page
├── analysis/                       # Python calculation modules
│   ├── volatility_calculator.py   # Volatility metrics computation
│   └── cumulative_returns.py      # Returns analysis computation
└── backend/
    └── app.py                      # Flask API endpoints connecting frontend to Python
```

### Architecture Pattern
Each tool follows this three-layer architecture:

1. **Python Calculation Layer** (`src/analysis/`)
   - Contains the heavy computational logic
   - Implements statistical calculations, financial models, and data analysis
   - Returns structured data (dictionaries/JSON) with calculated metrics
   - Example: `volatility_calculator.py` calculates annualized volatility, VaR, percentiles

2. **API Endpoint Layer** (`src/backend/app.py`)
   - Flask routes that expose Python calculations as REST endpoints
   - Handles data retrieval from database
   - Calls Python calculation modules with appropriate parameters
   - Returns JSON responses to frontend
   - Example: `/api/stock/<ticker>/volatility` endpoint uses `calculate_volatility_from_prices()`

3. **Frontend Display Layer** (`src/frontend/Toolbox/`)
   - HTML/JavaScript interface for user interaction
   - Makes AJAX calls to API endpoints
   - Renders results using charts, tables, and formatted displays
   - Handles user input validation and UI state management
   - Example: `volatility-calculator.html` displays volatility metrics and term structure charts

### Tool Registration System

Tools are registered in `src/frontend/js/solvers-config.js`:
```javascript
const solversConfig = [
    {
        id: 1,
        title: "Historic Volatility Calculator",
        description: "Calculate annualized historic volatility...",
        path: "Toolbox/volatility-calculator.html",  // Path to tool HTML
        status: "available"                           // or "coming-soon"
    },
    // Additional tools...
];
```

The main toolbox page (`my-tools.html`) uses `render-utils.js` to:
- Dynamically render tool cards from the configuration
- Handle navigation to individual tools
- Display availability status

### Existing Tools

#### 1. Historic Volatility Calculator
- **Frontend**: `Toolbox/volatility-calculator.html`
- **Backend**: `/api/stock/<ticker>/volatility` endpoint
- **Python**: `src/analysis/volatility_calculator.py`
- **Functionality**: 
  - Calculates daily, weekly, monthly, and annualized volatility
  - Computes return statistics (mean, min, max, skewness, kurtosis)
  - Generates volatility percentiles and term structure
  - Provides robust volatility measures (winsorized, MAD)

#### 2. Cumulative Returns Calculator
- **Frontend**: `Toolbox/cumulative-returns.html`
- **Backend**: `/api/stock/<ticker>/cumulative-returns` endpoint
- **Python**: `src/analysis/cumulative_returns.py`
- **Functionality**:
  - Analyzes overnight vs intraday returns
  - Calculates cumulative performance metrics
  - Identifies best/worst performing periods
  - Compares return patterns

#### 3. Implied Volatility Surface
- **Frontend**: `Toolbox/iv-surface.html`
- **Backend**: `/api/iv-surface/<ticker>` endpoint
- **Python**: `src/analysis/iv_surface.py`
- **Functionality**:
  - Fetches real-time options chain data via yfinance
  - Calculates IV using Newton-Raphson with JAX automatic differentiation
  - Generates 3D interpolated surfaces for calls and puts
  - Filters deep ITM options (unreliable IV extraction)
  - Uses Black-Scholes model with dividend yield adjustment

### Creating New Tools - Step-by-Step Guide

#### Step 1: Create Python Calculation Module
Create a new file in `src/analysis/` (e.g., `option_pricer.py`):
``` python
def calculate_option_price(spot, strike, rate, volatility, time):
    """
    Core calculation logic for option pricing.
    Returns dictionary with calculated metrics.
    """
    # Implement Black-Scholes or other model
    return {
        'call_price': calculated_call,
        'put_price': calculated_put,
        'greeks': {...}
    }
```

#### Step 2: Add API Endpoint
Add route in `src/backend/app.py`:
``` python
from src.analysis.option_pricer import calculate_option_price

@app.route('/api/option/price', methods=['POST'])
def price_option():
    data = request.json
    result = calculate_option_price(
        spot=data['spot'],
        strike=data['strike'],
        # ... other parameters
    )
    return jsonify({'success': True, 'result': result})
```

#### Step 3: Create HTML Frontend
Create `src/frontend/Toolbox/option-pricer.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Option Pricer</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <!-- Input form -->
    <!-- Results display -->
    <script>
        async function calculateOption() {
            const response = await fetch('/api/option/price', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...})
            });
            // Display results
        }
    </script>
</body>
</html>
```

#### Step 4: Register in Configuration
Add to `src/frontend/js/solvers-config.js`:
``` javascript
{
    id: 3,
    title: "Black-Scholes Option Pricer",
    description: "Calculate option prices and Greeks",
    path: "Toolbox/option-pricer.html",
    status: "available"
}
```

### Best Practices for Tool Development

1. **Separation of Concerns**
   - Keep ALL heavy computation in Python modules
   - Use frontend ONLY for display and user interaction
   - API endpoints should be thin wrappers around Python functions

2. **Error Handling**
   - Python modules should validate inputs and return error dictionaries
   - API endpoints should catch exceptions and return appropriate HTTP codes
   - Frontend should display user-friendly error messages

3. **Data Flow**
   - Frontend collects user input → API validates and fetches data → Python calculates → API returns JSON → Frontend displays

4. **Testing**
   - Unit test Python calculation modules independently
   - Test API endpoints with various input scenarios
   - Verify frontend handles all response types (success, error, edge cases)

5. **Performance**
   - Pre-calculate expensive metrics during data import when possible
   - Cache frequently requested calculations
   - Use pagination for large result sets

## Testing

Currently no formal test suite exists. When implementing tests, consider:
- Unit tests for calculation functions in `src/utils/calculations.py`
- Integration tests for database operations in `StockDataManager`
- API endpoint tests for Flask routes

## Analysis Modules

The application includes analysis modules in `src/analysis/`:
- `volatility_calculator.py` - Volatility metrics calculation (historic vol, VaR, percentiles)
- `cumulative_returns.py` - Overnight vs intraday return analysis
- `iv_surface.py` - Implied volatility surface calculator using JAX autodiff
- `iv_bsm_solver.py` - Standalone Black-Scholes IV solver (development/testing)
- `sharpe_ratio.py` - Sharpe ratio comparison for stock pairs
- `RSI.py` - Relative Strength Index calculation
- `stock_analyzer.py` - Framework for additional analysis tools

### IV Surface Technical Details
The IV surface calculator (`iv_surface.py`) uses:
- **JAX automatic differentiation** for efficient gradient computation in Newton-Raphson
- **Black-Scholes formula** with continuous dividend yield adjustment
- **Linear interpolation** with nearest-neighbor fallback for stable surface generation
- **Moneyness filtering**: Excludes deep ITM options (K/S < 0.9 for calls, K/S > 1.1 for puts) where IV extraction is numerically unstable
- **API caching**: 5-minute cache with LRU eviction (max 100 entries)