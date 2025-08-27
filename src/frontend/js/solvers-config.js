// solvers-config.js - Configuration for solvers.html
const solversConfig = [

    {
        id: 1,
        title: "Historic Volatility Calculator",
        description: "Calculate annualized historic volatility and comprehensive risk metrics from stock price data. Includes daily, weekly, and monthly volatility, return statistics, and volatility percentiles.",
        path: "Toolbox/volatility-calculator.html",
        status: "available"
    },
    {
        id: 2,
        title: "Forward Rate Calculator",
        description: "Calculate forward prices for various assets including stocks, commodities, and currencies. Supports continuous and discrete dividend yields, storage costs, and convenience yields.",
        path: null,
        status: "coming-soon"
    },
    {
        id: 3,
        title: "Cumulative Returns Calculator",
        description: "Analyze and visualize overnight vs intraday cumulative returns from historical stock data. Compare performance patterns, calculate total and annualized returns, and identify best/worst performing periods.",
        path: "Toolbox/cumulative-returns.html",
        status: "available"
    }
];

// Export for browser use
if (typeof window !== 'undefined') {
    window.solversConfig = solversConfig;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = solversConfig;
}