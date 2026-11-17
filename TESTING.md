# Testing

[English README](README.md) · [Русский README](README_RU.md)

## Automated tests

Run from the repository root with Python 3.12+:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -W error -q
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.
Warnings are treated as errors. No browser, account or external service is required.

Coverage includes cleaning order, unchanged source data, selected columns, all four
missing-value modes, encodings, delimiters, malformed files, size limits, literal
formula export, CSV/XLSX round trips and JSON reports. Streamlit AppTest covers
English/Russian labels and errors, state preservation across language changes and
result invalidation after settings change. Preview tests convert data directly
through PyArrow and check for Streamlit's automatic type-repair messages.

## Latest verified result

**2026-11-17: 155 passed**, using `python -m pytest -W error -q`.

| Component | Tested version |
|---|---|
| Python | 3.14.9 |
| pandas | 3.1.1 |
| Streamlit | 1.67.0 |
| openpyxl | 3.1.5 |
| PyArrow | 26.0.1 |
| pytest | 9.1.1 |

These versions describe the tested environment; `requirements.txt` contains bounded
ranges, not a lockfile or a claim that every version combination has been tested.

## Optional browser check and screenshots

Install the browser tooling into the project environment:

```bash
.venv/bin/python -m pip install playwright
PLAYWRIGHT_BROWSERS_PATH=.venv/playwright-browsers .venv/bin/python -m playwright install chromium
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8507
```

In a second terminal, from the repository root:

```bash
PLAYWRIGHT_BROWSERS_PATH=.venv/playwright-browsers .venv/bin/python scripts/capture_screenshots.py
```

These browser commands use Bash syntax. The script uses only `examples/demo_input.csv`,
updates the three real screenshots in `docs/screenshots/`, compares downloaded CSV
bytes, XLSX cell contents and JSON with the supplied examples, and verifies that
switching to Russian retains the upload and result. It also checks JavaScript errors.

Verified on 2026-11-17 with Chromium 159 and Playwright 1.65.2. Expected result:
6 → 3 rows, 1 duplicate and 2 empty rows removed, 9 → 1 missing cells.
[Manual capture instructions (RU)](docs/SCREENSHOTS_RU.md).

## Demonstration fixtures

```bash
.venv/bin/python -m scripts.generate_examples
```

This regenerates the CSV/XLSX and JSON examples using the actual cleaning pipeline.
XLSX archives contain timestamps, so compare cell contents rather than binary hashes.

## Кратко по-русски

Основная проверка: `.venv/bin/python -m pytest -W error -q` из корня проекта.
Последний результат: **155 тестов пройдено**, 17 ноября 2026 года. Проверены оба
языка, четыре режима пропусков, сохранение состояния, экспорт и PyArrow.
Браузерная проверка необязательна; команды выше запускают настоящее приложение
и обновляют скриншоты только на демонстрационных данных.
