"""Rebuild all demonstration outputs with the real processing pipeline."""
import json
from pathlib import Path
from src.csv_cleaner.core import CleanOptions, clean_table
from src.csv_cleaner.files import read_table, export_table

root = Path(__file__).resolve().parents[1] / 'examples'
frame = read_table((root / 'demo_input.csv').read_bytes(), 'demo.csv', separator=',')
cleaned, report = clean_table(frame, CleanOptions(trim_spaces=True, remove_duplicates=True, remove_empty_rows=True))
(root / 'demo_input.xlsx').write_bytes(export_table(frame, 'xlsx'))
for format in ('csv', 'xlsx'):
    (root / f'demo_output.{format}').write_bytes(export_table(cleaned, format))
(root / 'cleaning_report.json').write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + '\n')

# Missing-value demo: numeric CSV text, Cyrillic, duplicate and missing cell.
missing = read_table('Город,Цена\nМосква,10\nМосква,10\nОмск,\nКазань,30\n'.encode(), 'missing.csv')
(root / 'missing_input.csv').write_bytes(export_table(missing, 'csv'))
for strategy in ('keep', 'drop', 'value', 'median'):
    output, stats = clean_table(missing, CleanOptions(
        columns=('Цена',), missing_strategy=strategy, fill_value='Не указано'))
    (root / f'missing_{strategy}.csv').write_bytes(export_table(output, 'csv'))
    (root / f'missing_{strategy}.json').write_text(
        json.dumps(stats.to_dict(), ensure_ascii=False, indent=2) + '\n')
