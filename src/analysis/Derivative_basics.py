import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


class VIII_Solvers:
    def __init__(self,S0 = None,K = None,T = None,r = None,sigma = None,n_sim = 0,t = 0, q = 0):
        self.S0 = S0
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.n_sim = n_sim
        self.t = t
        self.q = q  # Continuous dividend yield
        return

    def mc_call(self):
        random_vals = np.random.normal(0, 1, self.n_sim, )

        shock = self.sigma * np.sqrt(self.T) * random_vals
        drift = (self.r - self.q - (self.sigma ** 2) / 2)
        S_T = self.S0 * np.exp(drift * self.T + shock)

        call_payoff = np.maximum(S_T - self.K, 0)
        call_price = np.average(call_payoff) * np.exp(-self.r * self.T)

        return float(call_price)

    def mc_put(self):

        random_vals = np.random.normal(0, 1, self.n_sim, )

        shock = self.sigma * np.sqrt(self.T) * random_vals
        drift = (self.r - self.q - (self.sigma ** 2) / 2)

        S_T = self.S0 * np.exp(drift * self.T + shock)

        put_payoff = np.maximum(self.K - S_T, 0)

        put_price = np.average(put_payoff) * np.exp(-self.r * self.T)

        return float(put_price)

    def d1(self):
        d1 = (np.log(self.S0 / self.K) + (self.r - self.q + (self.sigma ** 2) / 2) * (self.T - self.t)) / (
                    self.sigma * np.sqrt(self.T - self.t))
        return d1

    def d2(self):
        d2 = self.d1() - self.sigma * np.sqrt(self.T - self.t)
        return d2

    def BSM_call(self):
        d1 = self.d1()
        d2 = self.d2()
        tau = self.T - self.t
        call_price = self.S0 * np.exp(-self.q * tau) * norm.cdf(d1) - self.K * np.exp(-self.r * tau) * norm.cdf(d2)
        return call_price

    def BSM_put(self):
        d1 = self.d1()
        d2 = self.d2()
        tau = self.T - self.t
        put_price = self.K * np.exp(-self.r * tau) * norm.cdf(-d2) - self.S0 * np.exp(-self.q * tau) * norm.cdf(-d1)
        return put_price

    def objective(self,sigma,market_price):
        original_sigma = self.sigma
        self.sigma = sigma

        price_diff = self.BSM_call() - market_price

        self.sigma = original_sigma
        return price_diff

    def BSM_IV(self,market_price):
        implied_vol = brentq(self.objective, 0.01, 5.0, args=(market_price))
        return implied_vol

    def call_delta(self):
        """
        delta with continuous dividends
        ∆ = e^(-qT) * N(d1)
        """
        d1 = self.d1()
        tau = self.T - self.t
        delta = np.exp(-self.q * tau) * norm.cdf(d1)
        return delta

    def call_gamma(self):
        """
        Γ with continuous dividends = e^(-qT) * N'(d1) / (S * σ * sqrt(T-t))

        N'(d1) = f(d1) = 1/sqrt(2*π) * exp(-x^2/2), Normal distribution using mu = 0, σ = 1
        """
        tau = self.T - self.t
        N_prime_d1 = np.exp((-self.d1()**2) / 2) / np.sqrt(2*np.pi)
        gamma = np.exp(-self.q * tau) * N_prime_d1 / (self.S0 * self.sigma * np.sqrt(tau))
        return gamma

    def call_vega(self):
        """
        Vega with continuous dividends = S * e^(-qT) * sqrt(T-t) * N'(d1)
        """
        tau = self.T - self.t
        N_prime_d1 = np.exp((-self.d1()**2) / 2) / np.sqrt(2*np.pi)
        vega = self.S0 * np.exp(-self.q * tau) * np.sqrt(tau) * N_prime_d1
        return vega

    def call_theta(self):
        """
        Theta with continuous dividends for call option
        Θ = -e^(-qT) * S * N'(d1) * σ / (2*sqrt(T-t)) + q * S * e^(-qT) * N(d1) - r * K * e^(-rT) * N(d2)
        """
        tau = self.T - self.t
        d1 = self.d1()
        d2 = self.d2()
        N_prime_d1 = np.exp((-d1 ** 2) / 2) / np.sqrt(2 * np.pi)

        term1 = -np.exp(-self.q * tau) * self.S0 * N_prime_d1 * self.sigma / (2 * np.sqrt(tau))
        term2 = self.q * self.S0 * np.exp(-self.q * tau) * norm.cdf(d1)
        term3 = -self.r * self.K * np.exp(-self.r * tau) * norm.cdf(d2)

        theta = term1 + term2 + term3
        return theta





if __name__ == "__main__":

    S0 = 100
    K = 105
    T = 1
    r = 0.05
    sigma = 0.2
    n_sim = 100000

    market_price = 6.8

    solver = VIII_Solvers(S0, K, T, r, sigma, n_sim)

    monte_call = solver.mc_call()
    monte_put = solver.mc_put()



    print("\nUsing monte Carlo simulations:")
    print(f"Call Price: {monte_call:.4f}, Put Price: {monte_put:.4f}\n")

    BSM_call = solver.BSM_call()

    print("Using Black & Scholes framework")
    print(f"Call Price: {BSM_call:.4f}")

    IV = solver.BSM_IV(market_price)

    print(f"Implied volatility: {IV:.4f}\n")


    print("The Greeks")
    delta = solver.call_delta()
    gamma = solver.call_gamma()
    vega = solver.call_vega()
    theta = solver.call_theta()
    print(f"Delta: {delta:.4f}, Gamma: {gamma:.4f}")
    print(f"Vega: {vega:.4f}, Theta: {theta:.4f}")