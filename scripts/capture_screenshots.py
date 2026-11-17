"""Capture the real local app using only examples; optional Playwright dependency.

Run Streamlit on port 8507 first. Install Playwright and Chromium locally,
then run with PLAYWRIGHT_BROWSERS_PATH=.venv/playwright-browsers if needed.
"""
import json
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs' / 'screenshots'


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, channel="chromium")
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8507', wait_until='networkidle')
        page.get_by_text('Upload a table up to 10 MiB', exact=True).wait_for()
        page.locator('input[type=file]').set_input_files(ROOT / 'examples/demo_input.csv')
        page.get_by_role('heading', name='Source data', exact=True).wait_for()
        page.get_by_text('6 rows · 4 columns · 9 missing cells. Showing the first 20 rows.', exact=True).wait_for()
        page.locator('[data-testid="stDataFrame"] canvas').first.wait_for()
        page.wait_for_timeout(1000)  # Let the native canvas finish painting.
        page.screenshot(path=DEST / '01-source.png')
        for label in ['Trim extra whitespace', 'Remove duplicates', 'Remove fully empty rows']:
            page.get_by_text(label, exact=True).click()
            page.wait_for_timeout(300)
        page.get_by_role('heading', name='Cleaning settings', exact=True).scroll_into_view_if_needed()
        page.get_by_role('button', name='Run cleaning', exact=True).scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        page.screenshot(path=DEST / '02-settings.png')
        page.get_by_role('button', name='Run cleaning', exact=True).click()
        page.get_by_role('heading', name='Result', exact=True).wait_for()
        page.get_by_text('6 → 3', exact=True).wait_for()
        page.get_by_text('xlsx', exact=True).click()
        page.get_by_role('button', name='Download cleaned table', exact=True).wait_for()
        page.get_by_role('heading', name='Result', exact=True).evaluate(
            '(el) => el.scrollIntoView({block: "start"})')
        page.wait_for_timeout(600)
        page.screenshot(path=DEST / '03-result.png')
        with page.expect_download() as download:
            page.get_by_role('button', name='Download cleaned table', exact=True).click()
        xlsx = Path(download.value.path()).read_bytes()
        assert xlsx.startswith(b'PK')
        actual_book = load_workbook(BytesIO(xlsx), read_only=True)
        expected_book = load_workbook(ROOT / 'examples/demo_output.xlsx', read_only=True)
        try:
            assert list(actual_book.active.values) == list(expected_book.active.values)
        finally:
            actual_book.close()
            expected_book.close()
        with page.expect_download() as download:
            page.get_by_role('button', name='Download JSON report', exact=True).click()
        report = json.loads(Path(download.value.path()).read_bytes())
        assert report == json.loads((ROOT / 'examples/cleaning_report.json').read_text())
        page.get_by_text('csv', exact=True).click()
        page.get_by_text('CSV preserves text.', exact=False).wait_for()
        with page.expect_download() as download:
            page.get_by_role('button', name='Download cleaned table', exact=True).click()
        actual = Path(download.value.path()).read_bytes()
        expected = (ROOT / 'examples/demo_output.csv').read_bytes()
        assert actual == expected, (actual[:100], expected[:100])
        selector = page.get_by_test_id('stSelectbox').filter(has_text='Language / Язык').get_by_role('combobox')
        selector.focus()
        selector.press('ArrowDown')
        selector.press('Enter')
        page.get_by_role('heading', name='Результат', exact=True).wait_for()
        page.get_by_text('6 → 3', exact=True).scroll_into_view_if_needed()
        assert page.get_by_text('6 → 3', exact=True).is_visible()
        assert not errors, errors
        print('Saved three screenshots and verified CSV, XLSX, JSON and the Russian interface.')
        browser.close()


if __name__ == '__main__':
    main()
