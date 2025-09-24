import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from numpy.ma.extras import average


def get_weights(start,end,total):
    w1 = np.linspace(start, end, total)
    w2 = -1 * w1 + 1
    return w1,w2

def Yearly_log_returns_and_deviation(stock_ticker):
    ticker = yf.Ticker(stock_ticker)
    hist = ticker.history(period='5y')['Close'].to_numpy()
    daily_log_returns = np.log(hist[1:len(hist)] / hist[0:len(hist) - 1])
    yearly_log_returns = average(daily_log_returns) * 252

    # ddof = 1, makes us calculate the std with 1/n-1 instead of default numpy 1/n
    yearly_deviation = np.std(daily_log_returns, ddof=1) * np.sqrt(252)

    return daily_log_returns,yearly_log_returns,yearly_deviation

def get_cov_matrix(log_returns_list):
    cov_matrix = np.cov(log_returns_list)
    return cov_matrix



#Tickers
t1 = 'AAPL'
t2 = 'MSFT'

# Weight range
w_start = -1
w_end = 1
w_total = 100


""" --------------------Calculating-------------------- """
w1, w2 = get_weights(w_start,w_end,w_total)
rf = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]/100
d_log_r1,y_log_r1,std1 = Yearly_log_returns_and_deviation(t1)
d_log_r2,y_log_r2,std2 = Yearly_log_returns_and_deviation(t2)

""" Covariance """
cov_matrix = get_cov_matrix([d_log_r1,d_log_r2])
annual_covar = cov_matrix[0][1]*252
rho = annual_covar/(std1*std2)


portfolio_std = []
portfolio_returns = []
sharpe_ratio = []

for i in range(w_total):
    """ Calculating Return, deviation and sharpe ratio for different weights."""
    ret_val_r = w1[i]*y_log_r1 + w2[i]*y_log_r2
    ret_val_std1 = np.sqrt((w1[i]*std1)**2+(w2[i]*std2)**2+2*w1[i]*w2[i]*std1*std2*rho)
    sharpe = (ret_val_r-rf)/ret_val_std1

    sharpe_ratio.append(sharpe)
    portfolio_returns.append(ret_val_r)
    portfolio_std.append(ret_val_std1)


max_sharpe_idx = np.argmax(sharpe_ratio)
max_sharpe = sharpe_ratio[max_sharpe_idx]
optimal_W1 = w1[max_sharpe_idx]
optimal_W2 = w2[max_sharpe_idx]

min_var_idx = np.argmin(portfolio_std)
min_var_sharpe = sharpe_ratio[min_var_idx]
min_var_W1 = w1[min_var_idx]
min_var_W2 = w2[min_var_idx]
"""----------------------------------------------------------------------------"""




print("-"*50)
print("Average yearly returns")
print("-"*50)
print(f"Average yearly returns of {t1}: {round(y_log_r1*100,4)}%")
print(f"Average yearly returns of {t2}: {round(y_log_r2*100,4)}%")
print("-"*50)

print("Average yearly deviation")
print("-"*50)
print(f"Average yearly deviation of {t1}: {round(std1*100,4)}%")
print(f"Average yearly deviation of {t2}: {round(std2*100,4)}%")
print("-"*50)

print("Annual Covariance")
print("-"*50)
print(f"Annual Covariance of {t1} and {t2}: {round(annual_covar*100,4)}%")
print("-"*50)

print("Annual Covariance")
print("-"*50)
print(f"Annual Covariance of {t1} and {t2}: {round(annual_covar*100,4)}%")
print("-"*50)
print(" Optimal Weights of portfolio ")
print("-"*50)
print(f" weights: {round(optimal_W1,4)} of {t1}, {round(optimal_W2,4)} of {t2}")
print(f"Max sharpe ratio {round(max_sharpe,4)}")


plt.plot(portfolio_std, portfolio_returns)
plt.plot(portfolio_std[max_sharpe_idx], portfolio_returns[max_sharpe_idx],
            'ro', label='Max Sharpe')
plt.plot(portfolio_std[min_var_idx], portfolio_returns[min_var_idx],
            'bo', label='Min Var Portfolio')
plt.xlabel("Variance")
plt.ylabel("Returns")
plt.title(f"Sharpe Ratio for {t1}-{t2}")
plt.legend()
plt.show()
plt.close()
