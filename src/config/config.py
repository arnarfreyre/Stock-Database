"""
Configuration settings for the Stock Market Application
"""

import os
from pathlib import Path

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / 'src'
DATA_DIR = SRC_DIR / 'data'
DATABASE_DIR = SRC_DIR / 'database'

# Database configuration
DATABASE_PATH = DATABASE_DIR / 'stock_market.db'
TICKER_DATA_PATH = DATA_DIR / 'ticker-data.csv'

# API configuration
API_HOST = '0.0.0.0'
API_PORT = 5001
DEBUG_MODE = True

# Frontend configuration
FRONTEND_DIR = SRC_DIR / 'frontend'

# Stock data configuration
DEFAULT_PERIOD = '1y'
DEFAULT_MA_WINDOWS = [5, 20, 40, 50]
MAX_SEARCH_RESULTS = 50

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'