"""
Cumulative Returns Analysis Module
Calculates overnight and intraday cumulative returns from stock price data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def calculate_cumulative_returns(prices: List[Dict], ticker: str) -> Dict:
    """
    Calculate overnight and intraday cumulative returns from price data.
    
    Args:
        prices: List of price dictionaries with date, open, close, high, low, volume
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing cumulative returns data and statistics
    """
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(prices)
    
    # Ensure we have the required columns
    if 'date' not in df.columns or 'open' not in df.columns or 'close' not in df.columns:
        raise ValueError("Price data must contain date, open, and close columns")
    
    # Sort by date
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Remove any rows with NaN values in critical columns
    df = df.dropna(subset=['open', 'close'])
    
    if len(df) < 2:
        raise ValueError("Insufficient data for calculation (need at least 2 trading days)")
    
    # Calculate returns
    # Intraday returns: (Close / Open) - 1
    intraday_returns = (df['close'] / df['open']) - 1
    
    # Overnight returns: (Open / Previous Close) - 1
    # First day has no overnight return
    overnight_returns = pd.Series([0.0])
    overnight_calc = pd.Series((df['open'].iloc[1:].values / df['close'].iloc[:-1].values) - 1)
    overnight_returns = pd.concat([overnight_returns, overnight_calc], ignore_index=True)
    
    # Calculate cumulative returns
    cumulative_overnight = (1 + overnight_returns).cumprod()
    cumulative_intraday = (1 + intraday_returns).cumprod()
    
    # Calculate statistics
    total_overnight_return = (cumulative_overnight.iloc[-1] - 1) * 100
    total_intraday_return = (cumulative_intraday.iloc[-1] - 1) * 100
    
    # Calculate annualized returns
    trading_days = len(df)
    years = trading_days / 252  # Approximate trading days per year
    
    if years > 0:
        annualized_overnight = (np.power(cumulative_overnight.iloc[-1], 1/years) - 1) * 100
        annualized_intraday = (np.power(cumulative_intraday.iloc[-1], 1/years) - 1) * 100
    else:
        annualized_overnight = 0
        annualized_intraday = 0
    
    # Calculate win rates
    overnight_wins = (overnight_returns > 0).sum()
    intraday_wins = (intraday_returns > 0).sum()
    overnight_win_rate = (overnight_wins / len(overnight_returns)) * 100
    intraday_win_rate = (intraday_wins / len(intraday_returns)) * 100
    
    # Find best and worst days
    best_overnight_idx = overnight_returns.idxmax()
    worst_overnight_idx = overnight_returns.idxmin()
    best_intraday_idx = intraday_returns.idxmax()
    worst_intraday_idx = intraday_returns.idxmin()
    
    # Prepare return data
    result = {
        'success': True,
        'ticker': ticker,
        'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
        'cumulative_overnight': cumulative_overnight.tolist(),
        'cumulative_intraday': cumulative_intraday.tolist(),
        'overnight_returns': overnight_returns.tolist(),
        'intraday_returns': intraday_returns.tolist(),
        'statistics': {
            'total_overnight_return': round(total_overnight_return, 2),
            'total_intraday_return': round(total_intraday_return, 2),
            'annualized_overnight': round(annualized_overnight, 2),
            'annualized_intraday': round(annualized_intraday, 2),
            'overnight_win_rate': round(overnight_win_rate, 1),
            'intraday_win_rate': round(intraday_win_rate, 1),
            'best_overnight': {
                'return': round(overnight_returns.iloc[best_overnight_idx] * 100, 2),
                'date': df['date'].iloc[best_overnight_idx].strftime('%Y-%m-%d')
            },
            'worst_overnight': {
                'return': round(overnight_returns.iloc[worst_overnight_idx] * 100, 2),
                'date': df['date'].iloc[worst_overnight_idx].strftime('%Y-%m-%d')
            },
            'best_intraday': {
                'return': round(intraday_returns.iloc[best_intraday_idx] * 100, 2),
                'date': df['date'].iloc[best_intraday_idx].strftime('%Y-%m-%d')
            },
            'worst_intraday': {
                'return': round(intraday_returns.iloc[worst_intraday_idx] * 100, 2),
                'date': df['date'].iloc[worst_intraday_idx].strftime('%Y-%m-%d')
            },
            'trading_days': trading_days,
            'start_date': df['date'].iloc[0].strftime('%Y-%m-%d'),
            'end_date': df['date'].iloc[-1].strftime('%Y-%m-%d')
        }
    }
    
    return result


def calculate_rolling_returns(prices: List[Dict], window: int = 20) -> Dict:
    """
    Calculate rolling cumulative returns for a given window size.
    
    Args:
        prices: List of price dictionaries
        window: Rolling window size in days
        
    Returns:
        Dictionary with rolling returns data
    """
    
    df = pd.DataFrame(prices)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = df.dropna(subset=['open', 'close'])
    
    # Calculate daily returns
    intraday_returns = (df['close'] / df['open']) - 1
    overnight_returns = pd.Series([0.0], index=[0])
    overnight_returns = pd.concat([
        overnight_returns,
        (df['open'].iloc[1:].values / df['close'].iloc[:-1].values) - 1
    ]).reset_index(drop=True)
    
    # Calculate rolling cumulative returns
    rolling_overnight = pd.Series(index=df.index, dtype=float)
    rolling_intraday = pd.Series(index=df.index, dtype=float)
    
    for i in range(window - 1, len(df)):
        window_overnight = overnight_returns.iloc[i-window+1:i+1]
        window_intraday = intraday_returns.iloc[i-window+1:i+1]
        
        rolling_overnight.iloc[i] = (1 + window_overnight).prod() - 1
        rolling_intraday.iloc[i] = (1 + window_intraday).prod() - 1
    
    return {
        'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
        'rolling_overnight': rolling_overnight.tolist(),
        'rolling_intraday': rolling_intraday.tolist(),
        'window': window
    }