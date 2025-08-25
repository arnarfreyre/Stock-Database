"""
Calculation utilities for technical indicators and analysis
"""

from typing import List, Optional
import numpy as np

def calculate_moving_average(prices: List[float], window: int) -> List[Optional[float]]:
    """
    Calculate moving average for given window size.
    
    Args:
        prices: List of price values
        window: Window size for moving average
        
    Returns:
        List of moving average values (None for insufficient data points)
    """
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

def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of price values
        period: Period for RSI calculation (default: 14)
        
    Returns:
        List of RSI values
    """
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    rsi_values = [None] * period
    
    # Calculate price changes
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # Calculate initial average gain/loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Calculate RSI values
    for i in range(period, len(prices)):
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(round(rsi, 2))
        
        # Update averages (Wilder's smoothing)
        if i < len(gains):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    
    return rsi_values

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> tuple:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: List of price values
        period: Period for moving average (default: 20)
        std_dev: Number of standard deviations (default: 2)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band) lists
    """
    ma = calculate_moving_average(prices, period)
    
    upper_band = []
    lower_band = []
    
    for i in range(len(prices)):
        if ma[i] is None:
            upper_band.append(None)
            lower_band.append(None)
        else:
            # Calculate standard deviation
            window_prices = prices[i - period + 1:i + 1]
            std = np.std(window_prices)
            
            upper_band.append(round(ma[i] + (std_dev * std), 4))
            lower_band.append(round(ma[i] - (std_dev * std), 4))
    
    return upper_band, ma, lower_band

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: List of price values
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line EMA period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram) lists
    """
    if len(prices) < slow:
        return [None] * len(prices), [None] * len(prices), [None] * len(prices)
    
    # Calculate EMAs
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    # Calculate MACD line
    macd_line = []
    for i in range(len(prices)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(ema_fast[i] - ema_slow[i])
    
    # Calculate signal line
    signal_line = calculate_ema([m for m in macd_line if m is not None], signal)
    
    # Adjust signal line to match original length
    signal_adjusted = [None] * (len(prices) - len(signal_line)) + signal_line
    
    # Calculate histogram
    histogram = []
    for i in range(len(prices)):
        if macd_line[i] is None or signal_adjusted[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_adjusted[i])
    
    return macd_line, signal_adjusted, histogram

def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        prices: List of price values
        period: Period for EMA calculation
        
    Returns:
        List of EMA values
    """
    if len(prices) < period:
        return [None] * len(prices)
    
    ema = [None] * (period - 1)
    
    # Calculate initial SMA
    sma = sum(prices[:period]) / period
    ema.append(sma)
    
    # Calculate EMA
    multiplier = 2 / (period + 1)
    
    for i in range(period, len(prices)):
        ema_value = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(round(ema_value, 4))
    
    return ema