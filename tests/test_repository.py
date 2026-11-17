"""Dependency-free checks; these do not substitute for processing tests."""
import ast
import csv
import json
from pathlib import Path
import tomllib
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def test_python_sources_parse():
    for path in [ROOT / 'app.py', * (ROOT / 'src').rglob('*.py'), *(ROOT / 'tests').rglob('*.py')]:
        ast.parse(path.read_text(), filename=str(path))


def test_local_server_limits_and_telemetry():
    config = tomllib.loads((ROOT / '.streamlit/config.toml').read_text())
    assert config['server']['maxUploadSize'] == 10
    assert config['server']['address'] == '127.0.0.1'
    assert config['browser']['gatherUsageStats'] is False


def test_demo_report_and_files():
    with (ROOT / 'examples/demo_input.csv').open(newline='') as source:
        original = list(csv.DictReader(source))
    with (ROOT / 'examples/demo_output.csv').open(encoding='utf-8-sig', newline='') as source:
        cleaned = list(csv.DictReader(source))
    report = json.loads((ROOT / 'examples/cleaning_report.json').read_text())
    assert report['rows_before'] == len(original) == 6
    assert report['rows_after'] == len(cleaned) == 3
    assert report['rows_before'] - report['rows_after'] == report['duplicates_removed'] + report['empty_rows_removed']
    for name in ['demo_input.xlsx', 'demo_output.xlsx']:
        with ZipFile(ROOT / 'examples' / name) as archive:
            assert archive.testzip() is None
            assert 'xl/worksheets/sheet1.xml' in archive.namelist()
