import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# Fetch data
data = yf.download("^GSPC", period="2y", progress=False)
data = data.dropna()
# Calculate returns
overnight_returns = data["Open"] / data["Close"].shift(1) - 1 # Close → Open
intraday_returns = data["Close"] / data["Open"] - 1 # Open → Close
# Cumulative returns
cum_overnight = (1 + overnight_returns).cumprod()
cum_intraday = (1 + intraday_returns).cumprod()
# Plot
plt.figure(figsize=(12,6))
plt.plot(cum_overnight, label="Overnight (Close → Open)")
plt.plot(cum_intraday, label="Intraday (Open → Close)")
plt.title("Cumulative Return: Overnight vs Intraday (S&P 500)")
plt.xlabel("Date")
plt.ylabel("Cumulative Growth")
plt.legend()
plt.grid(True)
plt.show()
