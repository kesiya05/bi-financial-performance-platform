import pytest

from bi_platform.db import connect
from bi_platform.kpi import budget_vs_actual, compare, flag, flagged_lines, summary, yearly
from generate_data import generate, write_csv


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    return connect(write_csv(str(tmp_path_factory.mktemp("d") / "f.csv")))


def test_generator_shape_and_determinism():
    rows = generate(3)
    assert rows == generate(3)
    assert len(rows) == 36 * 10          # 3 revenue + 7 expense lines per month
    assert {r["type"] for r in rows} == {"revenue", "expense"}


def test_summary_profit_is_revenue_minus_expenses(con):
    for r in summary(con):
        assert r["profit"] == pytest.approx(r["revenue"] - r["expenses"])
        assert r["margin"] == pytest.approx(r["profit"] / r["revenue"])
    assert len(summary(con)) == 36


def test_mom_and_yoy(con):
    rows = summary(con)
    by = {r["month"]: r for r in rows}
    c = compare(rows, "2025-03")
    assert c["revenue_mom"] == pytest.approx(by["2025-03"]["revenue"] / by["2025-02"]["revenue"] - 1)
    assert c["revenue_yoy"] == pytest.approx(by["2025-03"]["revenue"] / by["2024-03"]["revenue"] - 1)
    first = compare(rows, "2023-01")
    assert first["revenue_mom"] is None and first["revenue_yoy"] is None   # no prior period, not a crash
    assert compare(rows, "2023-02")["revenue_mom"] is not None
    with pytest.raises(KeyError):
        compare(rows, "2030-01")


def test_year_rollup(con):
    ys = yearly(summary(con))
    assert [y["year"] for y in ys] == ["2023", "2024", "2025"]
    assert ys[0]["revenue_growth"] is None and ys[1]["revenue_growth"] > 0


@pytest.mark.parametrize("kind,actual,budget,expected", [
    ("expense", 100, 100, "ok"), ("expense", 104, 100, "ok"), ("expense", 106, 100, "amber"),
    ("expense", 111, 100, "red"), ("expense", 80, 100, "ok"),
    ("revenue", 94, 100, "amber"), ("revenue", 85, 100, "red"), ("revenue", 120, 100, "ok"),
])
def test_flag_rules(kind, actual, budget, expected):
    assert flag(kind, actual, budget)[1] == expected


def test_flag_zero_budget_is_safe():
    assert flag("expense", 50, 0) == (0.0, "ok")


def test_planted_overspends_are_found(con):
    jul = {x["category"]: x for x in budget_vs_actual(con, "2025-07")}
    assert jul["Maintenance"]["status"] == "red"
    assert jul["Marketing"]["status"] == "red"
    hits = flagged_lines(con, [f"2025-{m:02d}" for m in range(1, 13)])
    assert hits and hits[0]["variance_pct"] <= hits[-1]["variance_pct"]   # worst first
    assert any(h["category"] == "Marketing" and h["month"] >= "2025-07" for h in hits)


def test_year_budget_view_sums_months(con):
    year = {x["category"]: x for x in budget_vs_actual(con, "2024")}
    months = [budget_vs_actual(con, f"2024-{m:02d}") for m in range(1, 13)]
    total = sum(next(x for x in ms if x["category"] == "Rent")["actual"] for ms in months)
    assert year["Rent"]["actual"] == pytest.approx(total)
