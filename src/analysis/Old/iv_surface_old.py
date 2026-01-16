import yfinance as yf
import datetime as dt
from dateutil.relativedelta import relativedelta
import jax.numpy as jnp
from jax import grad
from jax.scipy.stats import norm as jnorm
from scipy.interpolate import griddata
import numpy as np
import plotly.graph_objects as go
"""------------------------------------------------------------------------------------------------------------------"""



def get_data(stock, date_start, date_end):
    ticker = yf.Ticker(stock)
    valid_dates = [i for i in ticker.options]
    valid_dates = valid_dates[date_start:]
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


def black_scholes(S,K,T,r,q,sigma,otype = "call"):
    d1 = (jnp.log(S/K)+(r-q+(sigma**2)/2)*T)/(sigma*jnp.sqrt(T))
    d2 = d1 -(sigma * jnp.sqrt(T))

    if otype == "call":
        call = S*jnp.exp(-q*T)*jnorm.cdf(d1)-K*jnp.exp(-r*T)*jnorm.cdf(d2)
        return call
    else:
        put = K*jnp.exp(-r*T)*jnorm.cdf(-d2)-S*jnp.exp(-q*T)*jnorm.cdf(-d1)
        return put

def loss(S,K,T,r,q,sigma_guess,price,otype):

    theoretical_price = black_scholes(S,K,T,r,q,sigma_guess,otype)
    market_price = price

    return theoretical_price - market_price


loss_grad = grad(loss,argnums = 5) # Diffra python fall??? wth. argnum = 5 þýðir diffra tiliti til Sigma_guess

def solve_for_iv(S,K,T,r,q,sigma_guess,price,otype="call",N_iter = 1000,epsilon = 0.001,verbose = True):

    sigma = sigma_guess
    for i in range(N_iter):
        loss_val = loss(S,K,T,r,q,sigma,price,otype)

        if abs(loss_val) < epsilon:
            break

        else:

            loss_grad_val = loss_grad(S,K,T,r,q,sigma,price,otype)
            sigma = sigma - loss_val/loss_grad_val

    return sigma


"""-----------------------------------Inputs---------------------------------"""
#** This will only show options where strike > Spot **

stock = 'POET'
otype = "call"

"""-------------------------------------------------------------------------"""




S = yf.Ticker(stock).history(period="1d")['Close'].iloc[-1]
r = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]/100
try:
    q = yf.Ticker(stock).info.get('dividendYield')/100
except TypeError:
    q=0
sigma = 0.2 # estimate


T_lis,K_lis,price_lis = get_data(stock,1,10)
T_plot = []
K_plot = []
sigma_plot = []
moneyness_plot = []
for i in range(len(T_lis)):
    print(f"\n Stock Price of {stock}: {S}, Dividend Yield: {q}%, Risk Free Rate: {r}, order type: {otype}\n")
    for j in range(len(price_lis[i])):

        K = K_lis[i][j]
        if K > S:
            price = price_lis[i][j]
            T = T_lis[i]
            sigma = solve_for_iv(S, K, T, r, q, sigma, price, otype)
            calculated_price = black_scholes(S,K,T,r,q,sigma,otype)
            T_plot.append(T)
            K_plot.append(K)
            sigma_plot.append(sigma)
            moneyness_plot.append(S/K)
            print(f" Using Strike: {K}, Time to expiration {T%.4}")
            print(f" Implied Volatility: {sigma}")
            print(f" Calculated Call Price: {calculated_price} - Market Price: {price}\n")




# Create a mesh grid for interpolation
T_unique = np.unique(T_plot)
K_unique = np.linspace(min(K_plot), max(K_plot), 50)
T_grid, K_grid = np.meshgrid(T_unique, K_unique)

# Interpolate implied volatilities onto the grid
points = np.array([(t, k) for t, k in zip(T_plot, K_plot)])
sigma_grid = griddata(points, np.array(sigma_plot), (T_grid, K_grid), method='cubic')

# Create the 3D surface plot
fig = go.Figure(data=[go.Surface(
    x=T_grid,
    y=K_grid,
    z=sigma_grid,
    colorscale='Viridis',
    showscale=True,
    colorbar=dict(
        title="Implied Volatility",  # Simple title without titleside
        tickmode="linear",
        tick0=0,
        dtick=0.05
    )
)])

# Update layout
fig.update_layout(
    title=f'{stock} Implied Volatility Surface',
    scene=dict(
        xaxis=dict(
            title='Time to Maturity (Years)',
            gridcolor='white',
            gridwidth=2,
        ),
        yaxis=dict(
            title='Strike Price ($)',
            gridcolor='white',
            gridwidth=2,
        ),
        zaxis=dict(
            title='Implied Volatility',
            gridcolor='white',
            gridwidth=2,
        ),
        camera=dict(
            eye=dict(x=1.5, y=-1.5, z=1.3)
        )
    ),
    width=900,
    height=700,
    margin=dict(l=0, r=0, b=0, t=50)
)

# Show the plot
fig.show()


