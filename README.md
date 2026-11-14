# BI Financial Performance Platform

Monthly financial reporting: KPIs, month-on-month and year-on-year change, and budget vs actual with amber (5%) and red (10%) flags.

## What it does

- Loads financials into SQL (`sql/schema.sql`)
- Monthly KPI report (markdown), budget workbook (xlsx) and HTML dashboard
- Flags lines that drift past budget

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python generate_data.py
python -m bi_platform
```

Results are written to `outputs/`.

## Tests

```bash
ruff check . && pytest
```

## Notes

The data is synthetic. In the July 2025 demo, labour is 8.4% over budget (amber) and maintenance and marketing are red. No `.pbix` is included, see `powerbi/README.md`.

MIT licensed. Built by Kesiya Ann Sony.
