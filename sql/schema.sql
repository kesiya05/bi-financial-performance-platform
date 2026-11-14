CREATE TABLE IF NOT EXISTS financials (
    month     TEXT NOT NULL,                                   -- YYYY-MM
    type      TEXT NOT NULL CHECK (type IN ('revenue','expense')),
    category  TEXT NOT NULL,
    actual    REAL NOT NULL,
    budget    REAL NOT NULL,
    PRIMARY KEY (month, category)
);

-- Profit per month, the base of every KPI.
CREATE VIEW IF NOT EXISTS monthly_summary AS
SELECT month,
       SUM(CASE WHEN type = 'revenue' THEN actual ELSE 0 END) AS revenue,
       SUM(CASE WHEN type = 'expense' THEN actual ELSE 0 END) AS expenses,
       SUM(CASE WHEN type = 'revenue' THEN actual ELSE -actual END) AS profit,
       SUM(CASE WHEN type = 'revenue' THEN budget ELSE 0 END) AS budget_revenue,
       SUM(CASE WHEN type = 'expense' THEN budget ELSE 0 END) AS budget_expenses
FROM financials
GROUP BY month;
