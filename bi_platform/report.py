"""Automated monthly KPI report: Markdown, HTML and Excel from one function call."""
import html
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import PatternFill

from .kpi import budget_vs_actual, compare, flagged_lines, summary, yearly

e = html.escape


def pct(x, signed=False):
    if x is None:
        return "n/a"
    return f"{x * 100:+.1f}%" if signed else f"{x * 100:.1f}%"


def money(x):
    return f"{x:,.0f}"


def build_report(con, month: str) -> dict:
    rows = summary(con)
    cur = next(r for r in rows if r["month"] == month)
    cmp = compare(rows, month)
    lines = budget_vs_actual(con, month)
    ytd = budget_vs_actual(con, month[:4])
    problems = [x for x in lines if x["status"] != "ok"]
    return {"month": month, "current": cur, "compare": cmp, "lines": lines, "ytd": ytd,
            "problems": problems, "years": yearly(rows)}


def markdown(rep: dict) -> str:
    c, k = rep["current"], rep["compare"]
    out = [f"# Monthly KPI report: {rep['month']}  (synthetic data)", "",
           f"- Revenue **{money(c['revenue'])}** (month on month {pct(k['revenue_mom'], True)}, year on year {pct(k['revenue_yoy'], True)})",
           f"- Expenses **{money(c['expenses'])}** (MoM {pct(k['expenses_mom'], True)}, YoY {pct(k['expenses_yoy'], True)})",
           f"- Profit **{money(c['profit'])}**, margin **{pct(c['margin'])}** (profit YoY {pct(k['profit_yoy'], True)})", "",
           "## Budget vs actual", "", "| Line | Actual | Budget | Variance | Flag |", "|---|---:|---:|---:|---|"]
    for x in rep["lines"]:
        out.append(f"| {x['category']} | {money(x['actual'])} | {money(x['budget'])} | {pct(x['variance_pct'], True)} | {x['status']} |")
    out += ["", "## Needs attention", ""]
    if rep["problems"]:
        for x in rep["problems"]:
            word = "under budget" if x["type"] == "revenue" else "over budget"
            out.append(f"- **{x['category']}** is {abs(x['variance_pct']) * 100:.1f}% {word} ({money(abs(x['variance_abs']))}).")
    else:
        out.append("- Nothing outside tolerance this month.")
    return "\n".join(out) + "\n"


def html_page(rep: dict) -> str:
    c = rep["current"]
    rows = "".join(
        f"<tr class={x['status']}><td>{e(x['category'])}</td><td class=r>{money(x['actual'])}</td><td class=r>{money(x['budget'])}</td>"
        f"<td class=r>{pct(x['variance_pct'], True)}</td><td>{x['status']}</td></tr>" for x in rep["lines"])
    yrs = "".join(f"<tr><td>{y['year']}</td><td class=r>{money(y['revenue'])}</td><td class=r>{money(y['profit'])}</td><td class=r>{pct(y['margin'])}</td><td class=r>{pct(y['revenue_growth'], True)}</td></tr>" for y in rep["years"])
    return f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>KPI report {rep['month']}</title><style>body{{font:16px/1.5 system-ui,sans-serif;max-width:820px;margin:0 auto;padding:1rem}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}td,th{{border-bottom:1px solid #ddd;padding:.35rem;text-align:left}}.r{{text-align:right}}
tr.red td{{background:#f6d9d4}}tr.amber td{{background:#f8ebc8}}</style></head><body>
<h1>Management dashboard: {rep['month']}</h1><p>Synthetic data.</p>
<p><b>Revenue</b> {money(c['revenue'])} &nbsp; <b>Profit</b> {money(c['profit'])} &nbsp; <b>Margin</b> {pct(c['margin'])}</p>
<h2>Budget vs actual</h2><table><tr><th>Line<th class=r>Actual<th class=r>Budget<th class=r>Variance<th>Flag</tr>{rows}</table>
<h2>Year by year</h2><table><tr><th>Year<th class=r>Revenue<th class=r>Profit<th class=r>Margin<th class=r>Revenue growth</tr>{yrs}</table></body></html>"""


def excel(rep: dict, path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = f"Budget vs actual {rep['month']}"
    ws.append(["Line", "Type", "Actual", "Budget", "Variance %", "Flag"])
    fills = {"red": "F6D9D4", "amber": "F8EBC8"}
    for x in rep["lines"]:
        ws.append([x["category"], x["type"], round(x["actual"], 2), round(x["budget"], 2), x["variance_pct"], x["status"]])
        if x["status"] in fills:
            for cell in ws[ws.max_row]:
                cell.fill = PatternFill("solid", fgColor=fills[x["status"]])
        ws.cell(row=ws.max_row, column=5).number_format = "0.0%"
    ws.column_dimensions["A"].width = 20
    wb.save(path)


def write_all(con, month: str, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rep = build_report(con, month)
    (out / f"kpi_report_{month}.md").write_text(markdown(rep), encoding="utf-8")
    (out / "dashboard.html").write_text(html_page(rep), encoding="utf-8")
    excel(rep, out / f"budget_vs_actual_{month}.xlsx")
    return rep


__all__ = ["build_report", "markdown", "html_page", "excel", "write_all", "flagged_lines"]
