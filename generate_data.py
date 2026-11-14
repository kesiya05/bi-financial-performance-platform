"""SYNTHETIC finance data for a small restaurant group: 36 months of actuals and budget.

    python generate_data.py     # writes data/financials.csv

Not real. A few overspends are planted on purpose (marketing in the second half of 2025, a
maintenance spike in July 2025, labour creeping up) so the variance flags have something to find.
"""
import csv
import os
import random

REVENUE = {"Dine-in": 520_000, "Delivery": 210_000, "Catering": 70_000}   # base per month
EXPENSE = {"Food & beverage": 0.31, "Labour": 0.32, "Rent": 62_000, "Utilities": 24_000,
           "Marketing": 22_000, "Maintenance": 11_000, "Admin": 28_000}      # % of revenue, or fixed amount
SEASON = {1: 0.92, 2: 0.9, 3: 0.97, 4: 1.0, 5: 1.05, 6: 1.08, 7: 1.1, 8: 1.07, 9: 1.0, 10: 1.0, 11: 1.03, 12: 1.18}
FIELDS = ["month", "type", "category", "actual", "budget"]


def generate(seed: int = 11):
    rnd = random.Random(seed)
    rows = []
    for year in (2023, 2024, 2025):
        growth = {2023: 1.0, 2024: 1.06, 2025: 1.11}[year]
        for m in range(1, 13):
            month = f"{year}-{m:02d}"
            budget_rev = {}
            for cat, base in REVENUE.items():
                b = base * SEASON[m] * growth
                budget_rev[cat] = b
                drift = 1.0 + (0.03 if cat == "Delivery" and year == 2025 else 0.0)
                rows.append({"month": month, "type": "revenue", "category": cat,
                             "actual": round(b * drift * rnd.uniform(0.96, 1.04), 2), "budget": round(b, 2)})
            total_budget_rev = sum(budget_rev.values())
            for cat, v in EXPENSE.items():
                b = total_budget_rev * v if v < 1 else v * (1.02 ** (year - 2023))
                a = b * rnd.uniform(0.97, 1.03)
                if cat == "Marketing" and year == 2025 and m >= 7:
                    a = b * rnd.uniform(1.22, 1.32)
                if cat == "Maintenance" and month == "2025-07":
                    a = b * 2.4
                if cat == "Labour" and year == 2025:
                    a = b * (1.0 + 0.012 * m)
                rows.append({"month": month, "type": "expense", "category": cat, "actual": round(a, 2), "budget": round(b, 2)})
    return rows


def write_csv(path="data/financials.csv", seed: int = 11):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(generate(seed))
    return path


if __name__ == "__main__":
    print("wrote", write_csv())
