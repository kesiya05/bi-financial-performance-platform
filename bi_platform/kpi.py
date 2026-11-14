"""Financial KPIs, comparisons and budget variance. Everything reads from SQL."""

AMBER, RED = 0.05, 0.10   # adverse variance thresholds


def summary(con) -> list[dict]:
    rows = [dict(r) for r in con.execute("SELECT * FROM monthly_summary ORDER BY month")]
    for r in rows:
        r["margin"] = r["profit"] / r["revenue"] if r["revenue"] else 0.0
    return rows


def _prev_month(month: str, back: int = 1) -> str:
    y, m = int(month[:4]), int(month[5:])
    idx = y * 12 + (m - 1) - back
    return f"{idx // 12}-{idx % 12 + 1:02d}"


def _change(now: float, before: float | None):
    if before in (None, 0):
        return None
    return (now - before) / abs(before)


def compare(rows: list[dict], month: str) -> dict:
    """Month-on-month and year-on-year change for revenue, expenses and profit. None when there is no prior period."""
    by = {r["month"]: r for r in rows}
    if month not in by:
        raise KeyError(month)
    cur = by[month]
    out = {"month": month}
    for label, key in (("mom", _prev_month(month, 1)), ("yoy", _prev_month(month, 12))):
        prev = by.get(key)
        for field in ("revenue", "expenses", "profit"):
            out[f"{field}_{label}"] = _change(cur[field], prev[field] if prev else None)
    return out


def yearly(rows: list[dict]) -> list[dict]:
    years: dict[str, dict] = {}
    for r in rows:
        y = years.setdefault(r["month"][:4], {"year": r["month"][:4], "revenue": 0.0, "expenses": 0.0, "profit": 0.0})
        for f in ("revenue", "expenses", "profit"):
            y[f] += r[f]
    out = sorted(years.values(), key=lambda y: y["year"])
    for i, y in enumerate(out):
        y["margin"] = y["profit"] / y["revenue"]
        y["revenue_growth"] = _change(y["revenue"], out[i - 1]["revenue"]) if i else None
    return out


def flag(kind: str, actual: float, budget: float) -> tuple[float, str]:
    """Variance as a share of budget, where a positive number is always GOOD for the business."""
    if budget == 0:
        return 0.0, "ok"
    var = (actual - budget) / budget if kind == "revenue" else (budget - actual) / budget
    if var <= -RED:
        return var, "red"
    if var <= -AMBER:
        return var, "amber"
    return var, "ok"


def budget_vs_actual(con, period: str) -> list[dict]:
    """period is 'YYYY-MM' for one month or 'YYYY' for a whole year."""
    q = """SELECT type, category, SUM(actual) AS actual, SUM(budget) AS budget
           FROM financials WHERE month LIKE ? GROUP BY type, category ORDER BY type DESC, category"""
    out = []
    for r in con.execute(q, (period + "%",)):
        var, status = flag(r["type"], r["actual"], r["budget"])
        out.append({"type": r["type"], "category": r["category"], "actual": r["actual"], "budget": r["budget"],
                    "variance_pct": var, "variance_abs": r["actual"] - r["budget"], "status": status})
    return out


def flagged_lines(con, months: list[str]) -> list[dict]:
    """Every month x category line that is amber or red, worst first."""
    hits = []
    for m in months:
        for line in budget_vs_actual(con, m):
            if line["status"] != "ok":
                hits.append({"month": m, **line})
    return sorted(hits, key=lambda h: h["variance_pct"])
