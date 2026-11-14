import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def connect(csv_path=ROOT / "data" / "financials.csv") -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    with open(csv_path, newline="") as f:
        rows = [(r["month"], r["type"], r["category"], float(r["actual"]), float(r["budget"])) for r in csv.DictReader(f)]
    con.executemany("INSERT INTO financials VALUES (?,?,?,?,?)", rows)
    con.commit()
    return con
