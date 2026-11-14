import sys

from generate_data import write_csv

from .db import ROOT, connect
from .kpi import flagged_lines, summary
from .report import write_all

csv_path = ROOT / "data" / "financials.csv"
if not csv_path.exists():
    write_csv(str(csv_path))
con = connect(csv_path)
months = [r["month"] for r in summary(con)]
month = sys.argv[1] if len(sys.argv) > 1 else months[-1]
write_all(con, month, ROOT / "outputs")
print(f"Report for {month} written to outputs/")
for h in flagged_lines(con, months[-12:])[:5]:
    print(f"- {h['month']} {h['category']}: {h['variance_pct'] * 100:+.1f}% vs budget ({h['status']})")
