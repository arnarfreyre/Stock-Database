// solvers-config.js - Configuration for solvers.html
const solversConfig = [
    {
        id: 1,
        title: "Forward Rate Calculator",
        description: "Calculate forward prices for various assets including stocks, commodities, and currencies. Supports continuous and discrete dividend yields, storage costs, and convenience yields.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 2,
        title: "Forward & Options Payoff Plotter",
        description: "Interactive tool for plotting payoffs at maturity for forwards, calls, and puts with customizable positions",
        path: null,
        status: "coming-soon"
    },
    {
        id: 3,
        title: "Bond Price & Duration Calculator",
        description: "Calculate bond prices, yields to maturity, duration, and convexity. Supports various day count conventions and compounding frequencies.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 4,
        title: "Binomial Option Model",
        description: "Interactive binomial tree for pricing American and European options. Visualize the option price evolution and early exercise decisions.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 5,
        title: "Interest Rate Swap Valuation",
        description: "Value plain vanilla and basis swaps. Calculate swap rates, DV01, and perform scenario analysis with yield curve shifts.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 6,
        title: "Monte Carlo Simulator",
        description: "Simulate asset price paths for exotic option pricing. Supports various stochastic processes including GBM, jump diffusion, and stochastic volatility.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 7,
        title: "Futures Margin Calculator",
        description: "Calculate initial and maintenance margins for futures positions. Simulate margin calls and analyze the impact of price movements.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 8,
        title: "Portfolio Greeks Calculator",
        description: "Aggregate Greeks for multi-asset option portfolios. Perform risk analysis and hedging ratio calculations.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 9,
        title: "Volatility Surface Builder",
        description: "Construct and visualize implied volatility surfaces from option prices. Interpolate volatilities for any strike and maturity combination.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 10,
        title: "Black-Scholes Option Pricer",
        description: "Price European options using the Black-Scholes model. Calculate option values, implied volatility, and all Greeks (Delta, Gamma, Theta, Vega, Rho).",
        path: null,
        status: "coming-soon"
    },
];

// Export for browser use
if (typeof window !== 'undefined') {
    window.solversConfig = solversConfig;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = solversConfig;
}