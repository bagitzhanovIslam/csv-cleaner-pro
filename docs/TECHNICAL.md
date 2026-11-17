# Technical reference

[Back to README](../README.md)

## Rules that matter

| Topic | Behavior |
|---|---|
| Header | First row is the header. Blank and repeated names receive unique labels; original spelling and spaces are otherwise retained. |
| CSV encoding | Auto reads UTF-8/BOM or BOM-marked UTF-16. Choose cp1251 explicitly for legacy Russian files. Decoding never silently replaces characters. |
| CSV delimiter | Auto attempts comma, semicolon, tab or pipe. Manual override is available. Check the preview before cleaning; ambiguous detection can produce a single column. |
| Values | CSV is read as text to preserve `001`, `NA`, `NULL`, and dates. XLSX retains native numbers/dates where available. Existing values are preserved; filling requires an explicit choice. |
| Missing cells | Null, empty string, and whitespace-only text count as missing. Missing values are reported across **all** columns. |
| Whitespace | In selected text columns, trim edges and collapse whitespace runs (including line breaks) to one space. |
| Duplicates | Before missing-value handling, after whitespace cleaning and optional empty-row removal, compare selected columns and keep the first row. Selecting fewer columns can remove rows with different values elsewhere. |
| Empty rows | Remove only when every cell across the entire table is missing. Independent of the column selection. |
| XLSX scope | Only the selected worksheet, starting at row 1, is processed. Styles, charts, other sheets and workbook metadata are not copied. Formula text is read without execution and exported as text. |
| Empty data | Zero-byte/blank files are errors; a header-only table is valid. XLSX trailing unused rows are not reliable data records. |

## Limits and file safety

Upload: **10 MiB**. XLSX uncompressed entries: **50 MiB**. Table: **100,000 rows**, **200 columns**, **1,000,000 cells**. Limits apply in both the interface and reader. This is an in-memory tool for small jobs, not a streaming or hostile-file isolation service. Do not expose it publicly without additional resource and access controls.

Only `.csv` and `.xlsx` are accepted. XLS/XLSM and macro-bearing workbooks are rejected. No uploaded code or macros are executed; openpyxl reads data and defusedxml hardens XML parsing. Corrupted files and invalid CSV row widths produce visible errors. Unexpected errors are logged with a traceback in the local terminal instead of being silently ignored.

XLSX exports force text cells, including strings starting with `=`, to remain text. CSV preserves original values: spreadsheet applications may interpret formula-like text when opened. Import such CSV columns explicitly as text or choose XLSX. No automatic prefix is added that would silently change your data.

## Tests and project layout

```bash
python -m pytest -q
python -m scripts.generate_examples
```

```text
app.py                       Streamlit interface and session state
src/csv_cleaner/core.py       Pure cleaning functions and report
src/csv_cleaner/files.py      Bounded readers and in-memory exporters
tests/                       Processing, file, UI and repository checks
examples/                    Fictional before/after CSV, XLSX and JSON
scripts/generate_examples.py  Rebuild examples with the actual pipeline
docs/                        Portfolio, screenshots and verification notes
```

Tests cover encodings, delimiters, Russian text, duplicates, empty rows, disabled rules, selected columns, malformed files, size limits, formula text, and export/reimport. Streamlit AppTest covers the initial screen, processing, result invalidation and errors. See [verification notes](VERIFICATION_RU.md) for what actually ran in the creation environment; test presence is not a claim that all tests passed.

Dependencies use bounded version ranges in `requirements.txt`; this is not a fully pinned lockfile. Tested environment details and any installation blockers are recorded separately. No database is needed.

## Portfolio and license

Skills: Python, pandas, openpyxl, Streamlit, pytest, CSV/Excel automation, validation, type hints, error handling, Git. Honest portfolio copy and a job proposal template are in [docs/PORTFOLIO_RU.md](PORTFOLIO_RU.md). Screenshot instructions are in [docs/SCREENSHOTS_RU.md](SCREENSHOTS_RU.md).

MIT License — see [LICENSE](../LICENSE).

## Fish shell on Arch Linux

No activation is required; these commands work in Fish and Bash:

Run from the repository root:

```fish
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

For optional Fish activation use `source .venv/bin/activate.fish`.
Run checks with `.venv/bin/python -m pytest -W error -q`.

## Missing-value examples

Select columns, then choose a missing-value mode. A supplied value is literal text
(e.g. `Unknown`); blank or whitespace-only replacements are rejected. Other cells
and unselected columns are preserved unless another enabled rule changes them.
Median accepts columns whose nonmissing values are all finite numbers or numeric
text (including CSV). It skips mixed text, booleans, dates and columns without
observations. Entirely empty numeric columns stay missing because no median exists.
Literal `NA` and `NULL` remain text. The order is whitespace → empty rows →
duplicates → missing-value handling. Filling can create new duplicates; they are
not removed afterward. Removal counts describe separate stages; filled-cell counts
refer to retained rows. JSON includes `cells_filled` and `missing_rows_removed`.

```python
from src.csv_cleaner.core import CleanOptions, clean_table
from src.csv_cleaner.files import read_table

frame = read_table(b"id,price\n001,10\n002,\n", "prices.csv")
cleaned, report = clean_table(frame, CleanOptions(
    columns=("price",), missing_strategy="median"))
assert cleaned.loc[1, "price"] == 10
assert report.cells_filled == 1
```

Generate additional missing-value demos with `.venv/bin/python -m scripts.generate_examples`.
Local environments, caches, credentials and private data directories are ignored.
Only fictional demo files belong in `examples/`. Review staged files before publishing.

## Interface languages

English is the default; Русский is available at the top. The presentation-only
`src/csv_cleaner/i18n.py` catalog translates labels, hints, errors and report headings.
Stable widget keys retain uploads, settings and results across language changes.
Streamlit 1.67+ is required for the verified widget identity behavior. Domain cleaning
functions and user-owned data remain unchanged. JSON downloads retain the original
English field schema for machine consumption; on-screen report headings are localized.
Native framework/browser controls may use their own system language.

The optional `scripts/capture_screenshots.py` uses Playwright to capture the actual
app and check downloads; see [capture instructions](SCREENSHOTS_RU.md).
