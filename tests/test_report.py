from bi_platform.db import connect
from bi_platform.report import build_report, markdown, write_all
from generate_data import write_csv


def test_report_files_and_content(tmp_path):
    con = connect(write_csv(str(tmp_path / "f.csv")))
    rep = write_all(con, "2025-07", tmp_path / "out")
    for name in ("kpi_report_2025-07.md", "dashboard.html", "budget_vs_actual_2025-07.xlsx"):
        assert (tmp_path / "out" / name).stat().st_size > 400, name
    text = markdown(rep)
    assert "Maintenance" in text and "over budget" in text
    assert "month on month" in text


def test_quiet_month_says_so(tmp_path):
    con = connect(write_csv(str(tmp_path / "f.csv")))
    rep = build_report(con, "2023-03")
    assert "Needs attention" in markdown(rep)
