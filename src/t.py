import yfinance as yf
import jax.numpy as jnp
from jax import grad
from jax.scipy.stats import norm as jnorm



def black_scholes(S,K,T,r,q,sigma,otype):
    d1 = (jnp.log(S/K)+(r-q+(sigma**2)/2)*T)/(sigma*jnp.sqrt(T))
    d2 = d1 -(sigma * jnp.sqrt(T))

    if otype == "call":
        call = S*jnp.exp(-q*T)*jnorm.cdf(d1)-K*jnp.exp(-r*T)*jnorm.cdf(d2)
        return call
    else:
        put = K*jnp.exp(-r*T)*jnorm.cdf(-d2)-S*jnp.exp(-q*T)*jnorm.cdf(-d1)
        call = S * jnp.exp(-q * T) * jnorm.cdf(d1) - K * jnp.exp(-r * T) * jnorm.cdf(d2)
        print(call)
        print(put)
        return put




""" Variables """

S = 51.91
K = 51.91
T = 2/12
r = 0.02

q = 0

sigma = 0.11
otype = "put"



sigma = black_scholes(S,K,T,r,q,sigma,otype)

print(f"Theoretical Sigma: {sigma}")