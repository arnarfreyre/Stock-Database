# Stock Price Visualization System

A comprehensive web-based stock price visualization application with moving averages analysis, built with Flask backend and interactive Chart.js frontend.

## Features

- **Interactive Price Charts**: Historical daily close prices with customizable date ranges
- **Moving Averages**: 5-day, 20-day, and 40-day moving averages
- **Volume Analysis**: Trading volume visualization with bar charts
- **Real-time Updates**: Pull latest data from Yahoo Finance
- **Statistics Dashboard**: Current price, daily change, period high/low, average volume, and volatility
- **Responsive Design**: Beautiful UI using existing styles.css
- **Database Storage**: SQLite database with optimized per-stock tables

## System Architecture

```
├── Backend (Python/Flask)
│   ├── app.py              # Flask REST API server
│   ├── create_database.py  # Database initialization
│   ├── add_stock.py        # Stock data management
│   └── stock_market.db     # SQLite database
│
├── Frontend (HTML/JavaScript)
│   ├── index.html          # Main web interface
│   ├── app.js              # JavaScript application logic
│   └── styles.css          # Styling (pre-existing)
│
└── Data
    └── ticker-data.csv     # Sample ticker data
```

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Setup Instructions

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create the database** (if not already created):
   ```bash
   python create_database.py
   ```

3. **Add stock data to database**:
   ```bash
   python add_stock.py
   ```
   - Enter stock ticker (e.g., AAPL, MSFT, GOOGL)
   - Select time period for historical data
   - The script will fetch data from Yahoo Finance

4. **Start the Flask server**:
   ```bash
   python app.py
   ```
   The server will start at `http://localhost:5000`

5. **Open the web interface**:
   - Open `index.html` in your web browser
   - Or navigate to `file:///path/to/index.html`
   - Make sure the Flask server is running

## Usage Guide

### Viewing Stock Charts

1. **Select a Stock**: Choose from the dropdown menu of available stocks
2. **Set Date Range**: Adjust start and end dates (defaults to last 6 months)
3. **Choose Moving Averages**: Toggle MA-5, MA-20, and MA-40 checkboxes
4. **Load Chart**: Click "Load Chart" button to display the visualization

### Updating Stock Data

1. Select the stock you want to update
2. Click "Update from Yahoo Finance" button
3. The system will fetch the latest data and refresh the charts

### Understanding the Charts

- **Price Chart**: Shows daily closing prices as a red line with optional moving averages
  - Blue dashed line: 5-day moving average
  - Green dashed line: 20-day moving average
  - Purple dashed line: 40-day moving average

- **Volume Chart**: Bar chart showing daily trading volumes

- **Statistics Panel**: 
  - Current Price: Latest closing price
  - Daily Change: Price change from previous day
  - Period High/Low: Maximum and minimum prices in selected period
  - Average Volume: Mean trading volume
  - Volatility: Annualized price volatility percentage

## API Endpoints

The Flask backend provides the following REST API endpoints:

- `GET /api/stocks` - List all available stocks
- `GET /api/stock/<ticker>/info` - Get stock information
- `GET /api/stock/<ticker>/prices` - Get historical price data
  - Query params: `start_date`, `end_date`
- `POST /api/stock/<ticker>/update` - Update stock data from Yahoo Finance
- `GET /api/health` - Health check endpoint

## Database Schema

### stocks_master table
- `ticker` - Stock symbol (PRIMARY KEY)
- `company_name` - Company full name
- `sector` - Business sector
- `exchange` - Stock exchange
- `table_name` - Dynamic table name for price data
- `total_records` - Number of price records
- `date_range_start/end` - Available data range

### {ticker}_prices tables (dynamic)
- `date` - Trading date (PRIMARY KEY)
- `open`, `high`, `low`, `close` - OHLC prices
- `volume` - Trading volume
- `ma_5`, `ma_20`, `ma_50` - Moving averages
- Note: MA-40 is calculated dynamically in the application

## Technical Implementation

### Moving Average Calculation
The 40-day moving average is calculated on-the-fly in the Flask backend since the database stores MA-50:

```python
def calculate_moving_average(prices, window=40):
    # Simple moving average calculation
    ma = []
    for i in range(len(prices)):
        if i < window - 1:
            ma.append(None)
        else:
            avg = sum(prices[i - window + 1:i + 1]) / window
            ma.append(round(avg, 4))
    return ma
```

### Chart.js Configuration
The application uses Chart.js v3+ for rendering interactive charts with:
- Line charts for price data
- Bar charts for volume data
- Responsive design
- Custom tooltips and formatting
- Multiple dataset support for overlaying moving averages

## Troubleshooting

### Common Issues

1. **"Database not found" error**:
   - Run `python create_database.py` first

2. **"No stocks in database" message**:
   - Add stocks using `python add_stock.py`

3. **Charts not loading**:
   - Ensure Flask server is running (`python app.py`)
   - Check browser console for errors
   - Verify API endpoint is accessible at `http://localhost:5000/api/health`

4. **CORS errors**:
   - Flask-CORS is configured to allow all origins
   - If issues persist, check browser security settings

5. **Missing dependencies**:
   - Run `pip install -r requirements.txt`
   - Ensure all packages are installed successfully

## Performance Optimization

- **Database**: Each stock has its own table for optimal query performance
- **Indexing**: Date columns are indexed for fast retrieval
- **Caching**: Browser caches static assets
- **Data Transfer**: Only requested date ranges are fetched
- **Chart Rendering**: Point radius set to 0 for better performance with large datasets

## Security Considerations

- Input validation for ticker symbols
- SQL injection protection through parameterized queries
- CORS configured for development (restrict in production)
- No sensitive data stored in frontend

## Future Enhancements

- [ ] Add more technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Implement user authentication
- [ ] Add portfolio tracking features
- [ ] Export charts as images
- [ ] Real-time price updates via WebSocket
- [ ] Compare multiple stocks on same chart
- [ ] Add candlestick chart option
- [ ] Mobile app version

## License

This project is for educational purposes. Stock data is provided by Yahoo Finance.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API documentation
3. Examine browser console for JavaScript errors
4. Verify Python dependencies are installed

---

**Note**: This application requires an active internet connection to fetch stock data from Yahoo Finance and to load Chart.js from CDN.