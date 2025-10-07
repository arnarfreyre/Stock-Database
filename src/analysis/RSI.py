import yfinance as yf
import numpy as np





stock = 'AAPL'

data = yf.Ticker(stock).info

for i in data:
    print(i)