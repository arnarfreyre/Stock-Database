# Stock Market Analysis Application

A comprehensive web-based stock market analysis platform with real-time data visualization, technical indicators, and modular architecture designed for scalability.

## 🏗️ Project Structure

```
├── src/                      # Source code directory
│   ├── backend/              # Backend services
│   │   ├── app.py            # Flask REST API server
│   │   └── stock_manager.py  # Stock data management
│   │
│   ├── frontend/             # Frontend assets
│   │   ├── index.html        # Main web interface
│   │   ├── app.js            # JavaScript application
│   │   └── styles.css        # Styling
│   │
│   ├── database/             # Database operations
│   │   ├── initialize_db.py  # Database initialization
│   │   └── stock_market.db   # SQLite database
│   │
│   ├── config/               # Configuration management
│   │   └── config.py         # Application settings
│   │
│   ├── utils/                # Utility functions
│   │   ├── get-tickers.py    # Gets market tickers
│   │   └── calculations.py   # Technical indicators
│   │
│   ├── analysis/             # Analysis tools (future expansions)
│   │   ├── iv_bsm_solver.py  # Calculates IV using BSM
│   │   ├── iv_surface.py     # Calculates IV surface
│   │   ├── sharpe_ratio.py   # Calculates sharpe ratio for 2 stocks
│   │   └── stock_analyzer.py # Advanced analysis module
│   │
│   └── data/                # Data storage
│       └── ticker-data.csv  # Ticker reference data
│
├── docs/                    # Documentation
├── tests/                   # Test suite
├── run_app.py              # Main application runner
├── init_db.py              # Database initialization script
├── add_stock_cli.py        # CLI for adding stocks
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🚀 Features

### Current Features
- **Interactive Price Charts**: Real-time visualization with Chart.js
- **Technical Indicators**: 
  - Moving Averages (5, 20, 40, 50-day)
  - Volume Analysis
  - Price Statistics
- **Data Management**: 
  - Yahoo Finance integration
  - SQLite database with optimized per-stock tables
  - Dynamic data updates
- **Search Functionality**: Ticker search by symbol or company name
- **Responsive Design**: Mobile-friendly interface

### Analysis Module (Ready for Expansion)
The `src/analysis/` directory contains a modular framework for adding advanced analysis tools:
- **Technical Analysis**: RSI, MACD, Bollinger Bands (framework ready)
- **Pattern Recognition**: Chart pattern identification (placeholder)
- **Support/Resistance**: Automatic level detection (placeholder)
- **Trend Analysis**: Trend strength and direction (placeholder)
- **Backtesting**: Strategy testing framework (placeholder)

## 📦 Installation

### Prerequisites
- Python 3.7+
- pip package manager
- Modern web browser

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd stock-market-app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python init_db.py
   ```

4. **Add stock data**:
   ```bash
   python add_stock_cli.py AAPL 1y
   python add_stock_cli.py MSFT 1y
   python add_stock_cli.py GOOGL 1y
   ```

5. **Run the application**:
   ```bash
   python run_app.py
   ```

6. **Open browser**:
   Navigate to `http://localhost:5001`

## 🛠️ Development

### Running Individual Components

**Flask API Server**:
```bash
python src/backend/app.py
```

**Database Initialization**:
```bash
python src/database/initialize_db.py
```

**Add Stocks via CLI**:
```bash
python add_stock_cli.py <TICKER> [period]
# Periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
```

### Configuration

Edit `src/config/config.py` to modify:
- Database paths
- API host/port settings
- Default parameters
- File locations

## 📊 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search/tickers` | Search tickers by symbol/name |
| GET | `/api/stocks` | List all available stocks |
| GET | `/api/stock/<ticker>/check` | Check if stock has data |
| GET | `/api/stock/<ticker>/info` | Get stock information |
| GET | `/api/stock/<ticker>/prices` | Get historical prices |
| POST | `/api/stock/<ticker>/load` | Load stock data from Yahoo |
| POST | `/api/stock/<ticker>/update` | Update existing stock data |
| GET | `/api/health` | Health check |

### Example Usage

```javascript
// Search for stocks
fetch('http://localhost:5001/api/search/tickers?q=apple')
  .then(response => response.json())
  .then(data => console.log(data));

// Get price data
fetch('http://localhost:5001/api/stock/AAPL/prices?start_date=2024-01-01')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🔧 Extending the Application

### Adding New Analysis Tools

1. **Create new module** in `src/analysis/`:
   ```python
   # src/analysis/your_analyzer.py
   from src.analysis.stock_analyzer import StockAnalyzer
   
   class YourAnalyzer(StockAnalyzer):
       def your_analysis_method(self):
           # Your implementation
           pass
   ```

2. **Add API endpoint** in `src/backend/app.py`:
   ```python
   @app.route('/api/analysis/your-endpoint', methods=['GET'])
   def your_analysis():
       # Your endpoint logic
       pass
   ```

3. **Update frontend** in `src/frontend/app.js`:
   ```javascript
   function callYourAnalysis() {
       // Your frontend code
   }
   ```

### Adding New Technical Indicators

Add to `src/utils/calculations.py`:
```python
def calculate_your_indicator(prices, **params):
    # Your calculation logic
    return indicator_values
```

## 📈 Database Schema

### stocks_master
- Primary table for stock metadata
- One record per stock ticker
- Links to individual price tables

### ticker_reference
- Comprehensive ticker database
- Symbol, name, sector, industry information

### {ticker}_prices (Dynamic Tables)
- Individual table per stock for performance
- OHLC data, volume, moving averages
- Date-indexed for fast queries

## 🧪 Testing

```bash
# Run tests (when implemented)
python -m pytest tests/
```

## 🔒 Security Considerations

- Input validation for all user inputs
- Parameterized SQL queries (injection protection)
- CORS configured for development
- No sensitive data in frontend code

## 🚀 Future Roadmap

### Phase 1: Enhanced Analysis
- [ ] Complete RSI, MACD, Bollinger Bands implementation
- [ ] Add pattern recognition algorithms
- [ ] Implement support/resistance detection

### Phase 2: Advanced Features
- [ ] Portfolio management system
- [ ] Multi-stock comparison charts
- [ ] Real-time WebSocket updates
- [ ] Export functionality (CSV, PDF)

### Phase 3: Machine Learning
- [ ] Price prediction models
- [ ] Sentiment analysis integration
- [ ] Automated trading signals

### Phase 4: Enterprise Features
- [ ] User authentication system
- [ ] Role-based access control
- [ ] API rate limiting
- [ ] Cloud deployment ready

## 📝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is for educational purposes. Stock data provided by Yahoo Finance.

## 🆘 Support

For issues or questions:
1. Check the documentation
2. Review API endpoints
3. Verify dependencies are installed
4. Check browser console for errors

---

**Note**: Internet connection required for Yahoo Finance data and CDN resources.