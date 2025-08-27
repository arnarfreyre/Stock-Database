import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


def fetch_stock_data(tickers, period='1y'):
    """
    Fetch historical stock data for given tickers
    """
    print(f"Fetching data for {', '.join(tickers)}...")

    try:
        # Try batch download first
        data = yf.download(tickers, period=period, progress=False)

        # Handle different yfinance data structures
        if len(tickers) == 1:
            # Single ticker - simple column structure
            if 'Adj Close' in data.columns:
                prices = pd.DataFrame(data['Adj Close'])
            else:
                prices = pd.DataFrame(data['Close'])
            prices.columns = tickers
        else:
            # Multiple tickers - multi-level column structure
            if 'Adj Close' in data.columns.get_level_values(0):
                prices = data['Adj Close']
            elif 'Close' in data.columns.get_level_values(0):
                prices = data['Close']
            else:
                # Fallback: try to get any price column
                prices = data.iloc[:, data.columns.get_level_values(0) == 'Close']
                if prices.empty:
                    prices = data.iloc[:, :len(tickers)]

        # Ensure column names are the ticker symbols
        if hasattr(prices.columns, 'levels'):
            prices.columns = tickers
        elif len(prices.columns) == len(tickers):
            prices.columns = tickers

    except Exception as e:
        print(f"Batch download failed: {e}")
        print("Trying individual ticker downloads...")

        # Fallback: Download each ticker individually
        prices = pd.DataFrame()
        for ticker in tickers:
            try:
                ticker_data = yf.Ticker(ticker).history(period=period)
                prices[ticker] = ticker_data['Close']
            except Exception as ticker_error:
                print(f"Error downloading {ticker}: {ticker_error}")
                raise

        # Ensure we have a proper DatetimeIndex
        if not prices.empty:
            prices.index = pd.to_datetime(prices.index)

    # Final validation
    if prices.empty:
        raise ValueError("No data could be fetched for the specified tickers")

    print(f"Successfully fetched data. Shape: {prices.shape}")
    print(f"Date range: {prices.index[0].date()} to {prices.index[-1].date()}")

    return prices


def calculate_portfolio_metrics(weights, returns, cov_matrix, risk_free_rate=0.045):
    """
    Calculate portfolio return, volatility, and Sharpe ratio
    """
    # Portfolio return (annualized)
    portfolio_return = np.sum(returns * weights) * 252

    # Portfolio volatility (annualized)
    portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))

    # Sharpe ratio
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol

    return portfolio_return, portfolio_vol, sharpe_ratio


def create_3d_sharpe_surface(tickers=['MSFT', 'AAPL', 'TSLA'],
                             grid_points=50,
                             risk_free_rate=0.045):
    """
    Create 3D surface plot of Sharpe ratios for different portfolio weights
    """
    # Fetch stock data
    stock_data = fetch_stock_data(tickers)

    # Calculate daily returns
    returns = stock_data.pct_change().dropna()

    # Calculate mean returns and covariance matrix
    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    # Create grid of weights for first two stocks
    w1_range = np.linspace(0, 1, grid_points)
    w2_range = np.linspace(0, 1, grid_points)

    # Create meshgrid
    W1, W2 = np.meshgrid(w1_range, w2_range)

    # Calculate W3 (weight of third stock)
    W3 = 1 - W1 - W2

    # Initialize array for Sharpe ratios
    sharpe_ratios = np.zeros_like(W1)

    # Calculate Sharpe ratio for each valid weight combination
    for i in range(grid_points):
        for j in range(grid_points):
            w1, w2, w3 = W1[i, j], W2[i, j], W3[i, j]

            # Check if weights are valid (all non-negative and sum to 1)
            if w3 >= 0:
                weights = np.array([w1, w2, w3])
                _, _, sharpe = calculate_portfolio_metrics(
                    weights, mean_returns, cov_matrix, risk_free_rate
                )
                sharpe_ratios[i, j] = sharpe
            else:
                # Invalid weight combination
                sharpe_ratios[i, j] = np.nan

    # Create 3D plot
    fig = plt.figure(figsize=(14, 10))

    # First subplot: 3D surface
    ax1 = fig.add_subplot(121, projection='3d')

    # Mask invalid values
    masked_sharpe = np.ma.masked_invalid(sharpe_ratios)

    # Create surface plot
    surf = ax1.plot_surface(W1, W2, masked_sharpe,
                            cmap=cm.viridis,
                            alpha=0.9,
                            edgecolor='none',
                            vmin=np.nanmin(sharpe_ratios),
                            vmax=np.nanmax(sharpe_ratios))

    # Labels and title
    ax1.set_xlabel(f'{tickers[0]} Weight', fontsize=10)
    ax1.set_ylabel(f'{tickers[1]} Weight', fontsize=10)
    ax1.set_zlabel('Sharpe Ratio', fontsize=10)
    ax1.set_title('3D Sharpe Ratio Surface', fontsize=12, fontweight='bold')

    # Add colorbar
    fig.colorbar(surf, ax=ax1, shrink=0.5, aspect=5)

    # Second subplot: Contour plot (top view)
    ax2 = fig.add_subplot(122)

    # Create contour plot
    contour = ax2.contourf(W1, W2, masked_sharpe, levels=20, cmap=cm.viridis)
    ax2.contour(W1, W2, masked_sharpe, levels=10, colors='black', alpha=0.3, linewidths=0.5)

    # Add constraint line (w1 + w2 = 1)
    ax2.plot([0, 1], [1, 0], 'r--', linewidth=2, label='w1 + w2 + w3 = 1')

    # Labels and title
    ax2.set_xlabel(f'{tickers[0]} Weight', fontsize=10)
    ax2.set_ylabel(f'{tickers[1]} Weight', fontsize=10)
    ax2.set_title('Sharpe Ratio Contour Plot', fontsize=12, fontweight='bold')
    ax2.legend()

    # Add colorbar
    fig.colorbar(contour, ax=ax2)

    # Find optimal portfolio
    valid_mask = ~np.isnan(sharpe_ratios)
    if np.any(valid_mask):
        max_sharpe_idx = np.nanargmax(sharpe_ratios)
        max_sharpe_pos = np.unravel_index(max_sharpe_idx, sharpe_ratios.shape)
        optimal_w1 = W1[max_sharpe_pos]
        optimal_w2 = W2[max_sharpe_pos]
        optimal_w3 = W3[max_sharpe_pos]
        max_sharpe = sharpe_ratios[max_sharpe_pos]

        # Mark optimal point
        ax1.scatter([optimal_w1], [optimal_w2], [max_sharpe],
                    color='red', s=100, marker='*', label='Optimal')
        ax2.plot(optimal_w1, optimal_w2, 'r*', markersize=15, label='Optimal')

        # Print optimal weights
        print("\n" + "=" * 50)
        print("PORTFOLIO OPTIMIZATION RESULTS")
        print("=" * 50)
        print(f"\nOptimal Portfolio Weights:")
        print(f"  {tickers[0]}: {optimal_w1:.1%}")
        print(f"  {tickers[1]}: {optimal_w2:.1%}")
        print(f"  {tickers[2]}: {optimal_w3:.1%}")
        print(f"\nMaximum Sharpe Ratio: {max_sharpe:.3f}")

        # Calculate additional metrics for optimal portfolio
        weights_opt = np.array([optimal_w1, optimal_w2, optimal_w3])
        ret_opt, vol_opt, _ = calculate_portfolio_metrics(
            weights_opt, mean_returns, cov_matrix, risk_free_rate
        )
        print(f"Expected Annual Return: {ret_opt:.1%}")
        print(f"Annual Volatility: {vol_opt:.1%}")
        print(f"Risk-Free Rate Used: {risk_free_rate:.1%}")

    plt.suptitle(f'Sharpe Ratio Analysis: {", ".join(tickers)} Portfolio\n' +
                 f'(Based on 1 Year Historical Data)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

    # Additional analysis plot
    create_individual_metrics_plot(stock_data, tickers, risk_free_rate)

    return sharpe_ratios, W1, W2, W3


def create_individual_metrics_plot(stock_data, tickers, risk_free_rate=0.045):
    """
    Create additional plots showing individual stock performance
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Calculate returns
    returns = stock_data.pct_change().dropna()

    # Plot 1: Normalized price performance
    ax1 = axes[0, 0]
    normalized = stock_data / stock_data.iloc[0]
    for ticker in tickers:
        ax1.plot(normalized.index, normalized[ticker], label=ticker, linewidth=2)
    ax1.set_title('Normalized Price Performance (1 Year)', fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Normalized Price')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Return distribution
    ax2 = axes[0, 1]
    for ticker in tickers:
        ax2.hist(returns[ticker], bins=50, alpha=0.5, label=ticker, density=True)
    ax2.set_title('Daily Return Distributions', fontweight='bold')
    ax2.set_xlabel('Daily Return')
    ax2.set_ylabel('Density')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Risk-Return scatter
    ax3 = axes[1, 0]
    annual_returns = returns.mean() * 252
    annual_vols = returns.std() * np.sqrt(252)
    sharpe_individual = (annual_returns - risk_free_rate) / annual_vols

    colors = ['blue', 'green', 'red']
    for i, ticker in enumerate(tickers):
        ax3.scatter(annual_vols[ticker], annual_returns[ticker],
                    s=200, alpha=0.7, color=colors[i], label=ticker)
        ax3.annotate(f'{ticker}\nSR: {sharpe_individual[ticker]:.2f}',
                     (annual_vols[ticker], annual_returns[ticker]),
                     xytext=(5, 5), textcoords='offset points', fontsize=9)

    ax3.set_xlabel('Annual Volatility')
    ax3.set_ylabel('Annual Return')
    ax3.set_title('Risk-Return Profile', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # Plot 4: Correlation matrix
    ax4 = axes[1, 1]
    corr_matrix = returns.corr()
    im = ax4.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
    ax4.set_xticks(range(len(tickers)))
    ax4.set_yticks(range(len(tickers)))
    ax4.set_xticklabels(tickers)
    ax4.set_yticklabels(tickers)
    ax4.set_title('Correlation Matrix', fontweight='bold')

    # Add correlation values
    for i in range(len(tickers)):
        for j in range(len(tickers)):
            text = ax4.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                            ha="center", va="center", color="black", fontsize=10)

    plt.colorbar(im, ax=ax4)

    plt.suptitle('Individual Stock Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()


# Main execution
if __name__ == "__main__":
    # You can modify these parameters
    TICKERS = ['MSFT', 'AAPL', 'TSLA']  # Stock tickers
    GRID_POINTS = 50  # Resolution of the grid (higher = more detailed but slower)
    RISK_FREE_RATE = 0.045  # Current approximate US Treasury 1-year rate (4.5%)

    print("Starting 3D Sharpe Ratio Analysis...")
    print(f"Stocks: {', '.join(TICKERS)}")
    print(f"Risk-free rate: {RISK_FREE_RATE:.1%}\n")

    # Create the visualization
    sharpe_surface, w1_grid, w2_grid, w3_grid = create_3d_sharpe_surface(
        tickers=TICKERS,
        grid_points=GRID_POINTS,
        risk_free_rate=RISK_FREE_RATE
    )

    print("\n" + "=" * 50)
    print("Analysis Complete!")
    print("=" * 50)