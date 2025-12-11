import yfinance as yf
import datetime as dt
from dateutil.relativedelta import relativedelta


def get_data(stock, date_start, date_end):
    ticker = yf.Ticker(stock)
    valid_dates = [i for i in ticker.options]
    valid_dates = valid_dates[date_start:date_end]
    option_dict = dict.fromkeys(valid_dates, )

    today = dt.datetime(dt.date.today().year, dt.date.today().month, dt.date.today().day)
    T_lis = []
    K_lis = []
    price_lis = []

    for key in option_dict.keys():
        option_dict[key] = ticker.option_chain(key).calls[['strike', 'lastPrice']]
        K_lis.append(option_dict[key]['strike'].values.tolist())
        price_lis.append(option_dict[key]['lastPrice'].values.tolist())

        """ Getting T values"""
        end_date = dt.datetime(int(key[0:4]), int(key[5:7]), int(key[8:10]))
        diff_years = relativedelta(end_date, today).years + relativedelta(end_date, today).months / 12 + relativedelta(
            end_date,
            today).days / 365
        T_lis.append(diff_years)

    return T_lis, K_lis, price_lis





stock = 'AAPL'
r = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1] / 100
S = yf.Ticker(stock).history(period="1d")['Close'].iloc[-1]
otype = "call"
try:
    q = yf.Ticker(stock).info.get('dividendYield')/100
except TypeError:
    q=0
sigma = 0.2 # estimate


T_lis,price_lis,K_lis = get_data(stock,0,2)


for i in range(len(T_lis)):

    for j in range(len(price_lis[i])):
        K = K_lis[i][j]
        price = price_lis[i][j]
        print(f"Time To expiration: {T_lis[i]} - Strike: {K} - Price: {price}")







