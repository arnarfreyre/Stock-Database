import yfinance as yf
import jax.numpy as jnp
from jax import grad
from jax.scipy.stats import norm as jnorm



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

def solve_for_iv(S,K,T,r,q,sigma_guess,price,otype="call",N_iter = 50000,epsilon = 0.01,verbose = True):

    sigma = sigma_guess
    for i in range(N_iter):
        print(f"Iteration: {i}")
        loss_val = loss(S,K,T,r,q,sigma,price,otype)

        if verbose:
            print(f"Current error in theoretical vs market price:\n {loss_val}")

        if abs(loss_val) < epsilon:
            break

        else:

            loss_grad_val = loss_grad(S,K,T,r,q,sigma,price,otype)
            sigma = sigma - loss_val/loss_grad_val

    return sigma


""" Variables """
stock = 'AAPL'
S = yf.Ticker(stock).history(period="1d")['Close'].iloc[-1]
K = 270
T = 1/12
price = 1.36
r = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]/100

try:
    q = yf.Ticker(stock).info.get('dividendYield')/100
except TypeError:
    q=0

sigma = 0.2
otype = "call"



sigma = solve_for_iv(S,K,T,r,q,sigma,price,otype)
print(f"Theoretical price: {price:.2f}")
print(f"Theoretical Sigma: {sigma}")



