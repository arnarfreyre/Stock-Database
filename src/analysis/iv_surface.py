import yfinance as yf
import datetime as dt
from dateutil.relativedelta import relativedelta
import jax.numpy as jnp
from jax import grad
from jax.scipy.stats import norm as jnorm
from scipy.interpolate import griddata
import numpy as np
import logging

logger = logging.getLogger(__name__)

"""------------------------------------------------------------------------------------------------------------------"""

class IVSurfaceCalculator:
    """Calculate implied volatility surface for options."""

    def __init__(self):
        self.loss_grad = grad(self._loss, argnums=5)  # Differentiate with respect to sigma_guess

    @staticmethod
    def get_options_data(ticker, min_expiry_index=0, max_expiry_index=10):
        """
        Fetch options data for both calls and puts.

        Args:
            ticker: Stock ticker symbol
            min_expiry_index: Starting index for expiration dates
            max_expiry_index: Ending index for expiration dates

        Returns:
            dict: Contains calls and puts data with time to expiry, strikes, and prices
        """
        try:
            yf_ticker = yf.Ticker(ticker)

            # Get available expiration dates
            if not hasattr(yf_ticker, 'options') or len(yf_ticker.options) == 0:
                raise ValueError(f"{ticker} does not have listed options")

            valid_dates = yf_ticker.options[min_expiry_index:max_expiry_index]

            if len(valid_dates) == 0:
                raise ValueError(f"No valid expiration dates found for {ticker}")

            # Get current stock price and info
            spot_price = yf_ticker.history(period="1d")['Close'].iloc[-1]

            # Initialize data structures
            calls_data = {'T': [], 'K': [], 'prices': [], 'expiries': []}
            puts_data = {'T': [], 'K': [], 'prices': [], 'expiries': []}

            today = dt.datetime.now()

            for expiry_date_str in valid_dates:
                try:
                    # Fetch option chain for this expiry
                    option_chain = yf_ticker.option_chain(expiry_date_str)

                    # Calculate time to expiry in years
                    expiry_date = dt.datetime.strptime(expiry_date_str, '%Y-%m-%d')
                    time_to_expiry = (expiry_date - today).days / 365.25

                    if time_to_expiry <= 0:
                        continue  # Skip expired options

                    # Process calls
                    calls_df = option_chain.calls[['strike', 'lastPrice', 'bid', 'ask', 'volume']]
                    valid_calls = calls_df[
                        (calls_df['lastPrice'] > 0.01) &  # Has valid price
                        (calls_df['volume'] > 0)  # Has some volume
                    ]

                    for _, row in valid_calls.iterrows():
                        calls_data['T'].append(time_to_expiry)
                        calls_data['K'].append(row['strike'])
                        # Use last price if available, otherwise use bid-ask midpoint
                        price = row['lastPrice'] if row['lastPrice'] > 0 else (row['bid'] + row['ask']) / 2
                        calls_data['prices'].append(price)
                        calls_data['expiries'].append(expiry_date_str)

                    # Process puts
                    puts_df = option_chain.puts[['strike', 'lastPrice', 'bid', 'ask', 'volume']]
                    valid_puts = puts_df[
                        (puts_df['lastPrice'] > 0.01) &  # Has valid price
                        (puts_df['volume'] > 0)  # Has some volume
                    ]

                    for _, row in valid_puts.iterrows():
                        puts_data['T'].append(time_to_expiry)
                        puts_data['K'].append(row['strike'])
                        # Use last price if available, otherwise use bid-ask midpoint
                        price = row['lastPrice'] if row['lastPrice'] > 0 else (row['bid'] + row['ask']) / 2
                        puts_data['prices'].append(price)
                        puts_data['expiries'].append(expiry_date_str)

                except Exception as e:
                    logger.warning(f"Failed to process expiry {expiry_date_str}: {e}")
                    continue

            return {
                'calls': calls_data,
                'puts': puts_data,
                'spot_price': spot_price,
                'ticker': ticker
            }

        except Exception as e:
            logger.error(f"Error fetching options data for {ticker}: {e}")
            raise

    @staticmethod
    def black_scholes(S, K, T, r, q, sigma, otype="call"):
        """Calculate Black-Scholes option price."""
        d1 = (jnp.log(S/K) + (r - q + (sigma**2)/2) * T) / (sigma * jnp.sqrt(T))
        d2 = d1 - (sigma * jnp.sqrt(T))

        if otype == "call":
            return S * jnp.exp(-q * T) * jnorm.cdf(d1) - K * jnp.exp(-r * T) * jnorm.cdf(d2)
        else:
            return K * jnp.exp(-r * T) * jnorm.cdf(-d2) - S * jnp.exp(-q * T) * jnorm.cdf(-d1)

    def _loss(self, S, K, T, r, q, sigma_guess, price, otype):
        """Loss function for IV optimization."""
        theoretical_price = self.black_scholes(S, K, T, r, q, sigma_guess, otype)
        return theoretical_price - price

    def solve_for_iv(self, S, K, T, r, q, price, otype="call", sigma_guess=0.2,
                     n_iter=100, epsilon=0.001):
        """
        Solve for implied volatility using Newton-Raphson method with JAX gradients.
        """
        sigma = sigma_guess

        for i in range(n_iter):
            loss_val = self._loss(S, K, T, r, q, sigma, price, otype)

            if abs(loss_val) < epsilon:
                break

            loss_grad_val = self.loss_grad(S, K, T, r, q, sigma, price, otype)

            # Newton-Raphson update with bounds
            if abs(loss_grad_val) > 1e-10:  # Avoid division by zero
                sigma = sigma - loss_val / loss_grad_val
                # Keep sigma in reasonable bounds [0.01, 5.0]
                sigma = float(np.clip(sigma, 0.01, 5.0))
            else:
                break

        return float(sigma)

    def calculate_surface(self, ticker, risk_free_rate=None, dividend_yield=None,
                         min_expiry_index=0, max_expiry_index=10):
        """
        Calculate IV surface for both calls and puts.

        Args:
            ticker: Stock ticker symbol
            risk_free_rate: Risk-free rate (if None, fetches from ^TNX)
            dividend_yield: Dividend yield (if None, fetches from ticker info)
            min_expiry_index: Starting index for expiration dates
            max_expiry_index: Ending index for expiration dates

        Returns:
            dict: Contains surface data for calls and puts
        """
        try:
            # Fetch options data
            options_data = self.get_options_data(ticker, min_expiry_index, max_expiry_index)

            # Get market parameters
            S = options_data['spot_price']

            # Fetch risk-free rate if not provided
            if risk_free_rate is None:
                try:
                    r = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1] / 100
                except:
                    r = 0.05  # Default to 5% if fetch fails
                    logger.warning("Failed to fetch risk-free rate, using 5% default")
            else:
                r = risk_free_rate

            # Fetch dividend yield if not provided
            if dividend_yield is None:
                try:
                    q = yf.Ticker(ticker).info.get('dividendYield', 0) or 0
                except:
                    q = 0
                    logger.warning("Failed to fetch dividend yield, using 0% default")
            else:
                q = dividend_yield

            # Calculate IV for calls and puts
            surfaces = {}

            for option_type in ['calls', 'puts']:
                data = options_data[option_type]

                if len(data['T']) == 0:
                    logger.warning(f"No valid {option_type} data for {ticker}")
                    surfaces[option_type] = None
                    continue

                # Calculate IV for each option
                iv_values = []
                valid_T = []
                valid_K = []

                for i in range(len(data['T'])):
                    try:
                        T = data['T'][i]
                        K = data['K'][i]
                        price = data['prices'][i]

                        # Skip if price is too low or time to expiry is too short
                        if price < 0.01 or T < 0.01:
                            continue

                        # Calculate IV
                        iv = self.solve_for_iv(S, K, T, r, q, price,
                                              otype=option_type[:-1])  # Remove 's' from calls/puts

                        # Validate IV is reasonable
                        if 0.01 <= iv <= 5.0:
                            iv_values.append(iv)
                            valid_T.append(T)
                            valid_K.append(K)

                    except Exception as e:
                        logger.debug(f"Failed to calculate IV for {option_type} K={K}, T={T}: {e}")
                        continue

                if len(iv_values) < 5:
                    logger.warning(f"Insufficient valid IV points for {option_type}: {len(iv_values)}")
                    surfaces[option_type] = None
                    continue

                # Create mesh grid for interpolation
                try:
                    T_unique = np.unique(valid_T)
                    K_min, K_max = min(valid_K), max(valid_K)

                    # Create regular grid for interpolation
                    T_grid_1d = np.linspace(min(T_unique), max(T_unique), 30)
                    K_grid_1d = np.linspace(K_min, K_max, 30)
                    T_grid, K_grid = np.meshgrid(T_grid_1d, K_grid_1d)

                    # Interpolate IV values onto grid
                    points = np.array([(t, k) for t, k in zip(valid_T, valid_K)])
                    sigma_grid = griddata(points, np.array(iv_values),
                                        (T_grid, K_grid), method='cubic')

                    # Handle NaN values from extrapolation
                    # Use nearest neighbor interpolation to fill NaNs
                    nan_mask = np.isnan(sigma_grid)
                    if np.any(nan_mask):
                        sigma_grid_nearest = griddata(points, np.array(iv_values),
                                                     (T_grid, K_grid), method='nearest')
                        sigma_grid[nan_mask] = sigma_grid_nearest[nan_mask]

                    surfaces[option_type] = {
                        'T_grid': T_grid.tolist(),
                        'K_grid': K_grid.tolist(),
                        'sigma_grid': sigma_grid.tolist(),
                        'raw_points': {
                            'T': valid_T,
                            'K': valid_K,
                            'iv': iv_values
                        }
                    }

                except Exception as e:
                    logger.error(f"Failed to create surface grid for {option_type}: {e}")
                    surfaces[option_type] = None

            # Return complete surface data
            return {
                'ticker': ticker,
                'spot_price': float(S),
                'risk_free_rate': float(r),
                'dividend_yield': float(q),
                'surfaces': surfaces,
                'timestamp': dt.datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to calculate IV surface for {ticker}: {e}")
            raise


# Create singleton instance
iv_calculator = IVSurfaceCalculator()


def get_iv_surface_data(ticker, **kwargs):
    """
    Convenience function to get IV surface data.

    Args:
        ticker: Stock ticker symbol
        **kwargs: Additional arguments for calculate_surface

    Returns:
        dict: IV surface data for both calls and puts
    """
    return iv_calculator.calculate_surface(ticker, **kwargs)