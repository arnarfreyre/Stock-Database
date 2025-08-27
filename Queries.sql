-- Calculate annualized historical volatility for AAPL (assuming 252 trading days)
WITH daily_returns AS (
    SELECT
        date,
        close,
        LN(close / LAG(close) OVER (ORDER BY date)) as log_return
    FROM SONY_prices
    WHERE date >= (SELECT date
                 FROM SONY_prices
                 ORDER BY date
                 DESC LIMIT 1 OFFSET 251)
ORDER BY date
),
volatility_calc AS (
    SELECT
        COUNT(*) as num_observations,
        AVG(log_return) as mean_return,
        -- Sample standard deviation of log returns
        SQRT(SUM(POWER(log_return - (SELECT AVG(log_return) FROM daily_returns), 2)) / (COUNT(*) - 1)) as daily_volatility
    FROM daily_returns
    WHERE log_return IS NOT NULL
)
SELECT
    daily_volatility,
    daily_volatility * SQRT(252) as annualized_volatility,
    daily_volatility * SQRT(252) * 100 as annualized_volatility_pct,
    num_observations
FROM volatility_calc;


insert into ticker_reference
    Values ('^GSPC','S&P 500','Index','Index','2025-08-27 15:20:00','2025-08-27 15:20:00');

DELETE FROM ticker_reference
WHERE symbol = 'GSPC';