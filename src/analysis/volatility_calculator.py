#!/usr/bin/env python3
"""
Volatility Calculator Module
Provides comprehensive volatility analysis for stock price data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class VolatilityCalculator:
    """
    Calculate various volatility metrics for stock price data.
    Assumes 252 trading days per year for annualization.
    """
    
    TRADING_DAYS_PER_YEAR = 252
    TRADING_DAYS_PER_MONTH = 21
    TRADING_DAYS_PER_WEEK = 5
    
    def __init__(self, prices: List[float], dates: Optional[List[str]] = None,
                 filter_outliers: bool = False, outlier_threshold: float = 0.10,
                 filter_future_dates: bool = True):
        """
        Initialize the volatility calculator with price data.
        
        Args:
            prices: List of stock prices (closing prices)
            dates: Optional list of corresponding dates
            filter_outliers: Whether to filter extreme outliers
            outlier_threshold: Threshold for outlier detection (default 10% daily move)
            filter_future_dates: Whether to filter future dates
        """
        self.raw_prices = np.array(prices)
        self.raw_dates = dates
        self.filter_outliers = filter_outliers
        self.outlier_threshold = outlier_threshold
        self.filter_future_dates = filter_future_dates
        self.data_quality_warnings = []
        
        # Process and clean data
        self.prices, self.dates = self._clean_data()
        self.log_returns = self._calculate_log_returns()
        
    def _clean_data(self) -> Tuple[np.ndarray, Optional[List[str]]]:
        """
        Clean and validate price data.
        
        Returns:
            Tuple of cleaned prices and dates
        """
        prices = self.raw_prices.copy()
        dates = self.raw_dates.copy() if self.raw_dates else None
        
        # Filter future dates
        if self.filter_future_dates and dates:
            today = datetime.now().strftime('%Y-%m-%d')
            valid_indices = []
            for i, date in enumerate(dates):
                if date <= today:
                    valid_indices.append(i)
                else:
                    self.data_quality_warnings.append(f"Future date detected and filtered: {date}")
            
            if valid_indices:
                prices = prices[valid_indices]
                dates = [dates[i] for i in valid_indices]
        
        # Filter extreme outliers in returns
        if self.filter_outliers and len(prices) > 1:
            returns = prices[1:] / prices[:-1] - 1
            outlier_indices = []
            
            for i, ret in enumerate(returns):
                if abs(ret) > self.outlier_threshold:
                    outlier_indices.append(i + 1)  # +1 because returns start from index 1
                    if dates:
                        self.data_quality_warnings.append(
                            f"Outlier detected: {ret*100:.2f}% move on {dates[i+1] if dates else f'index {i+1}'}"
                        )
            
            # Remove outliers by keeping only non-outlier indices
            if outlier_indices:
                keep_indices = [i for i in range(len(prices)) if i not in outlier_indices]
                prices = prices[keep_indices]
                if dates:
                    dates = [dates[i] for i in keep_indices]
        
        return prices, dates
    
    def _calculate_log_returns(self) -> np.ndarray:
        """
        Calculate log returns from price data.
        Log return = ln(price_t / price_t-1)
        """
        if len(self.prices) < 2:
            return np.array([])
        
        # Calculate log returns
        price_ratios = self.prices[1:] / self.prices[:-1]
        
        # Check for invalid prices (zeros or negatives)
        if np.any(price_ratios <= 0):
            # Filter out invalid ratios to avoid log errors
            valid_mask = price_ratios > 0
            if not np.any(valid_mask):
                return np.array([])
            price_ratios = price_ratios[valid_mask]
            
        return np.log(price_ratios)
    
    def calculate_daily_volatility(self) -> float:
        """
        Calculate daily volatility (standard deviation of log returns).
        """
        if len(self.log_returns) < 2:
            return 0.0
        
        return np.std(self.log_returns, ddof=1)  # Using sample standard deviation
    
    def calculate_annualized_volatility(self) -> float:
        """
        Calculate annualized volatility.
        Annualized vol = daily vol * sqrt(252)
        """
        daily_vol = self.calculate_daily_volatility()
        return daily_vol * np.sqrt(self.TRADING_DAYS_PER_YEAR)
    
    def calculate_monthly_volatility(self) -> float:
        """
        Calculate monthly volatility.
        Monthly vol = daily vol * sqrt(21)
        """
        daily_vol = self.calculate_daily_volatility()
        return daily_vol * np.sqrt(self.TRADING_DAYS_PER_MONTH)
    
    def calculate_weekly_volatility(self) -> float:
        """
        Calculate weekly volatility.
        Weekly vol = daily vol * sqrt(5)
        """
        daily_vol = self.calculate_daily_volatility()
        return daily_vol * np.sqrt(self.TRADING_DAYS_PER_WEEK)
    
    def calculate_robust_volatility(self, method: str = 'winsorized', 
                                   winsorize_limits: Tuple[float, float] = (0.01, 0.01)) -> float:
        """
        Calculate robust volatility using alternative methods.
        
        Args:
            method: 'winsorized' or 'mad' (Median Absolute Deviation)
            winsorize_limits: Lower and upper percentile limits for winsorization
        
        Returns:
            Annualized robust volatility
        """
        if len(self.log_returns) < 2:
            return 0.0
        
        if method == 'winsorized':
            # Winsorize returns (cap extreme values)
            lower_percentile = winsorize_limits[0] * 100
            upper_percentile = (1 - winsorize_limits[1]) * 100
            
            lower_bound = np.percentile(self.log_returns, lower_percentile)
            upper_bound = np.percentile(self.log_returns, upper_percentile)
            
            winsorized_returns = np.clip(self.log_returns, lower_bound, upper_bound)
            daily_vol = np.std(winsorized_returns, ddof=1)
            
        elif method == 'mad':
            # Median Absolute Deviation - more robust to outliers
            median_return = np.median(self.log_returns)
            mad = np.median(np.abs(self.log_returns - median_return))
            # Scale MAD to be comparable to standard deviation
            # For normal distribution, std = MAD * 1.4826
            daily_vol = mad * 1.4826
            
        else:
            # Fallback to standard method
            daily_vol = self.calculate_daily_volatility()
        
        return daily_vol * np.sqrt(self.TRADING_DAYS_PER_YEAR)
    
    def calculate_return_statistics(self) -> Dict[str, float]:
        """
        Calculate comprehensive return statistics.
        """
        if len(self.log_returns) < 2:
            return {
                'mean_return': 0.0,
                'min_return': 0.0,
                'max_return': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'trading_days': len(self.prices)
            }
        
        # Calculate skewness manually using numpy
        def calculate_skewness(returns):
            if len(returns) < 3:
                return 0.0
            mean = np.mean(returns)
            std = np.std(returns, ddof=1)
            if std == 0:
                return 0.0
            n = len(returns)
            skew = (n / ((n - 1) * (n - 2))) * np.sum(((returns - mean) / std) ** 3)
            return skew
        
        # Calculate kurtosis manually using numpy (excess kurtosis)
        def calculate_kurtosis(returns):
            if len(returns) < 4:
                return 0.0
            mean = np.mean(returns)
            std = np.std(returns, ddof=1)
            if std == 0:
                return 0.0
            n = len(returns)
            kurt = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((returns - mean) / std) ** 4)
            kurt -= 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
            return kurt
        
        return {
            'mean_return': np.mean(self.log_returns),
            'min_return': np.min(self.log_returns),
            'max_return': np.max(self.log_returns),
            'skewness': calculate_skewness(self.log_returns),
            'kurtosis': calculate_kurtosis(self.log_returns),
            'trading_days': len(self.prices)
        }
    
    def calculate_volatility_percentiles(self, window: int = 20) -> Dict[str, float]:
        """
        Calculate rolling volatility and return percentiles.
        
        Args:
            window: Rolling window size for volatility calculation (default 20 days)
        """
        if len(self.log_returns) < window:
            return {
                'current_percentile': 50.0,
                'volatility_25th': self.calculate_daily_volatility(),
                'volatility_50th': self.calculate_daily_volatility(),
                'volatility_75th': self.calculate_daily_volatility(),
                'volatility_95th': self.calculate_daily_volatility()
            }
        
        # Calculate rolling volatility
        rolling_vols = []
        for i in range(window, len(self.log_returns) + 1):
            window_returns = self.log_returns[i-window:i]
            rolling_vols.append(np.std(window_returns, ddof=1))
        
        rolling_vols = np.array(rolling_vols)
        current_vol = self.calculate_daily_volatility()
        
        # Calculate where current volatility stands in historical distribution (percentile rank)
        # Manual implementation of percentileofscore
        count_below = np.sum(rolling_vols < current_vol)
        count_equal = np.sum(rolling_vols == current_vol)
        percentile_rank = ((count_below + 0.5 * count_equal) / len(rolling_vols)) * 100
        
        return {
            'current_percentile': percentile_rank,
            'volatility_25th': np.percentile(rolling_vols, 25),
            'volatility_50th': np.percentile(rolling_vols, 50),
            'volatility_75th': np.percentile(rolling_vols, 75),
            'volatility_95th': np.percentile(rolling_vols, 95)
        }
    
    def calculate_volatility_term_structure(self) -> Dict[str, float]:
        """
        Calculate volatility for different time periods to show term structure.
        """
        results = {}
        
        # Calculate volatility for different lookback periods
        periods = [5, 10, 20, 60, 120]  # Days
        
        for period in periods:
            if len(self.log_returns) >= period:
                recent_returns = self.log_returns[-period:]
                period_vol = np.std(recent_returns, ddof=1) * np.sqrt(self.TRADING_DAYS_PER_YEAR)
                results[f'volatility_{period}d'] = period_vol
            else:
                results[f'volatility_{period}d'] = None
        
        return results
    
    def get_comprehensive_metrics(self) -> Dict:
        """
        Calculate and return all volatility metrics.
        """
        metrics = {
            # Core volatility metrics
            'daily_volatility': self.calculate_daily_volatility(),
            'annualized_volatility': self.calculate_annualized_volatility(),
            'weekly_volatility': self.calculate_weekly_volatility(),
            'monthly_volatility': self.calculate_monthly_volatility(),
            
            # Robust volatility metrics
            'robust_volatility_winsorized': self.calculate_robust_volatility(method='winsorized'),
            'robust_volatility_mad': self.calculate_robust_volatility(method='mad'),
            
            # Return statistics
            **self.calculate_return_statistics(),
            
            # Volatility percentiles
            **self.calculate_volatility_percentiles(),
            
            # Term structure
            **self.calculate_volatility_term_structure(),
            
            # Data quality info
            'data_quality_warnings': self.data_quality_warnings,
            'original_data_points': len(self.raw_prices),
            'cleaned_data_points': len(self.prices),
            'outliers_removed': len(self.raw_prices) - len(self.prices),
            
            # Additional info
            'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_points': len(self.prices),
            'returns_used': len(self.log_returns)
        }
        
        # Convert percentages for display
        metrics['daily_volatility_pct'] = metrics['daily_volatility'] * 100
        metrics['annualized_volatility_pct'] = metrics['annualized_volatility'] * 100
        metrics['weekly_volatility_pct'] = metrics['weekly_volatility'] * 100
        metrics['monthly_volatility_pct'] = metrics['monthly_volatility'] * 100
        metrics['robust_volatility_winsorized_pct'] = metrics['robust_volatility_winsorized'] * 100
        metrics['robust_volatility_mad_pct'] = metrics['robust_volatility_mad'] * 100
        
        # Convert returns to percentages
        metrics['mean_return_pct'] = metrics['mean_return'] * 100
        metrics['min_return_pct'] = metrics['min_return'] * 100
        metrics['max_return_pct'] = metrics['max_return'] * 100
        
        return metrics


def calculate_volatility_from_prices(prices: List[float], 
                                    dates: Optional[List[str]] = None,
                                    filter_outliers: bool = False,
                                    outlier_threshold: float = 0.10,
                                    filter_future_dates: bool = True) -> Dict:
    """
    Convenience function to calculate volatility metrics from price data.
    
    Args:
        prices: List of stock prices
        dates: Optional list of dates
        filter_outliers: Whether to filter extreme outliers
        outlier_threshold: Threshold for outlier detection (default 10% daily move)
        filter_future_dates: Whether to filter future dates
        
    Returns:
        Dictionary containing all volatility metrics
    """
    calculator = VolatilityCalculator(prices, dates, filter_outliers, 
                                     outlier_threshold, filter_future_dates)
    return calculator.get_comprehensive_metrics()


def calculate_correlation_matrix(price_series: Dict[str, List[float]]) -> pd.DataFrame:
    """
    Calculate correlation matrix for multiple stock price series.
    
    Args:
        price_series: Dictionary with ticker as key and price list as value
        
    Returns:
        Correlation matrix as DataFrame
    """
    returns_dict = {}
    
    for ticker, prices in price_series.items():
        prices_array = np.array(prices)
        if len(prices_array) > 1:
            returns = np.log(prices_array[1:] / prices_array[:-1])
            returns_dict[ticker] = returns
    
    # Create DataFrame and calculate correlation
    returns_df = pd.DataFrame(returns_dict)
    return returns_df.corr()


def calculate_value_at_risk(prices: List[float], 
                           confidence_level: float = 0.95,
                           holding_period: int = 1) -> Dict[str, float]:
    """
    Calculate Value at Risk (VaR) using historical simulation.
    
    Args:
        prices: List of stock prices
        confidence_level: Confidence level for VaR (default 95%)
        holding_period: Holding period in days (default 1 day)
        
    Returns:
        Dictionary with VaR metrics
    """
    if len(prices) < 2:
        return {'var': 0.0, 'cvar': 0.0}
    
    prices_array = np.array(prices)
    returns = np.log(prices_array[1:] / prices_array[:-1])
    
    # Scale returns for holding period
    scaled_returns = returns * np.sqrt(holding_period)
    
    # Calculate VaR
    var_percentile = (1 - confidence_level) * 100
    var = np.percentile(scaled_returns, var_percentile)
    
    # Calculate Conditional VaR (CVaR) - expected loss beyond VaR
    cvar = np.mean(scaled_returns[scaled_returns <= var])
    
    return {
        'var': abs(var),  # Return as positive value
        'cvar': abs(cvar),
        'confidence_level': confidence_level,
        'holding_period': holding_period
    }