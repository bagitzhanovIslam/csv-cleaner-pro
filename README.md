# CSV Cleaner Pro

**Turn messy CSV and Excel tables into clean, downloadable data — locally.**

Clean product lists, price tables and other CSV/XLSX files with rules you choose. Preview the data, remove duplicates and extra spaces, handle missing values, then download the result and a JSON report. A local portfolio demo with fictional sample data.

[Русская документация](README_RU.md) · [Learning guide (RU)](LEARNING_GUIDE_RU.md) · [Portfolio materials](docs/PORTFOLIO_RU.md) · [Verification status](docs/VERIFICATION_RU.md)

## What it does

- Opens CSV and XLSX and previews the first 20 rows.
- Counts missing cells, including empty strings and whitespace.
- Optionally trims whitespace, removes duplicate rows, and removes fully empty rows.
- Handles missing cells in selected columns: keep (default), drop affected rows, fill with a supplied value, or fill numeric columns with the median.
- Lets you choose columns for whitespace cleaning, duplicate comparison and missing-value handling.
- Reports rows before/after, duplicate and empty row removals, filled cells, remaining missing cells, rows removed for missing values, and missing cells per column.
- Downloads a new CSV (UTF-8 with BOM) or XLSX and a JSON report.

All cleaning switches start **off**. Your original file is never overwritten. Files stay in the local Streamlit process; no paid services or external processing APIs are used.

## Run locally

Python **3.12+**. Download and extract the repository, or use your existing local checkout. Open a terminal in the repository root (the folder containing `app.py` and `requirements.txt`). On Linux/macOS with Bash or Zsh:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **http://127.0.0.1:8501**. Stop with `Ctrl+C`. For Fish, use `source .venv/bin/activate.fish`. On Windows PowerShell, replace the activation command with `.venv\Scripts\Activate.ps1`; in cmd.exe use `.venv\Scripts\activate.bat`. A network connection is needed to install dependencies, but processing runs locally afterward.

## Try the demo

1. Upload `examples/demo_input.csv` or `examples/demo_input.xlsx`.
2. Keep all columns selected and enable all three cleaning switches.
3. Click **Запустить обработку**.
4. Expect **6 → 3 rows**, **1 duplicate** and **2 empty rows** removed, **9 → 1 missing cells**, and **5 cells** changed by whitespace cleaning.
5. Download the result and compare it with `examples/demo_output.csv` and `examples/cleaning_report.json`.

The demo uses fictional product records, without personal data. The interface is in Russian; the code uses English names.

## Screenshots: input → settings → result

Real browser screenshots have not been captured yet. The three planned views are:

| View | What the screenshot must show |
|---|---|
| 1. Source data | `demo_input.csv` uploaded; “Исходные данные”, 6 rows and 9 missing cells. |
| 2. Cleaning settings | All columns selected, all three checkboxes enabled, missing values left unchanged. |
| 3. Result | 6 → 3 rows, 1 duplicate and 2 empty rows removed, 9 → 1 missing cells, cleaned table and download controls. |

Follow the [exact capture instructions and filenames](docs/SCREENSHOTS_RU.md). Add the three images here only after capturing the real application; no placeholder images are included.

## Documentation

- [Technical reference](docs/TECHNICAL.md): exact rules, limits, API examples, tests and project layout.
- [Russian technical reference](docs/TECHNICAL_RU.md) and [learning guide](LEARNING_GUIDE_RU.md).
- [Verification record](docs/VERIFICATION_RU.md) and [portfolio materials](docs/PORTFOLIO_RU.md).

Run checks from the repository root, with the virtual environment activated:

```bash
python -m pytest -W error -q
```

MIT License — see [LICENSE](LICENSE).
