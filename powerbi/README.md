# Power BI version

No `.pbix` is included (Power BI Desktop is Windows only and I couldn't run it where I built this).
Load `data/financials.csv` and add these measures:

```
Actual Revenue = CALCULATE(SUM(financials[actual]), financials[type] = "revenue")
Actual Expenses = CALCULATE(SUM(financials[actual]), financials[type] = "expense")
Profit = [Actual Revenue] - [Actual Expenses]
Margin = DIVIDE([Profit], [Actual Revenue])
Revenue YoY = DIVIDE([Actual Revenue] - CALCULATE([Actual Revenue], SAMEPERIODLASTYEAR(Dates[Date])),
                     CALCULATE([Actual Revenue], SAMEPERIODLASTYEAR(Dates[Date])))
Expense Variance % = DIVIDE(SUM(financials[budget]) - SUM(financials[actual]), SUM(financials[budget]))
```

Create a Dates table from the `month` column, relate it to `financials`, and colour the variance column
red below -10% and amber below -5% (same thresholds as `bi_platform/kpi.py`).
