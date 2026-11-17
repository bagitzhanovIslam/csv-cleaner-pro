"""Exercise Arrow directly: AppTest alone can conceal Streamlit's fallback."""
from datetime import date
from io import BytesIO

import pandas as pd
import pyarrow as pa
import pytest
from pandas.testing import assert_frame_equal
from openpyxl import load_workbook

from src.csv_cleaner.core import CleanOptions, clean_table
from src.csv_cleaner.display import for_streamlit
from src.csv_cleaner.files import export_table


@pytest.mark.parametrize('values', [
    [1, 'текст', None, float('nan'), pd.NA],
    ['001', 2.5, None, float('nan'), pd.NA],
    [1.25, 'нет', None, float('nan'), pd.NA],
])
def test_mixed_columns_keep_text_and_real_nulls(values):
    source = pd.DataFrame({'возраст': values}, dtype=object)
    original = source.copy(deep=True)
    with pytest.raises((pa.ArrowInvalid, pa.ArrowTypeError)):
        pa.Table.from_pandas(source)
    preview = for_streamlit(source)
    table = pa.Table.from_pandas(preview)
    assert table['возраст'].to_pylist() == [str(values[0]), str(values[1]), None, None, None]
    assert_frame_equal(source, original)
    assert preview is not source


def test_native_numbers_dates_strings_and_nulls():
    source = pd.DataFrame({
        'integer': pd.Series([1, pd.NA], dtype='Int64'),
        'float': [1.25, float('nan')],
        'numeric_object': pd.Series([2.5, None], dtype=object),
        'text': pd.Series(['001', pd.NA], dtype='string'),
        'date': [date(2026, 1, 1), None],
        'timestamp': pd.to_datetime(['2026-01-01', None]),
        'nulls': pd.Series([None, pd.NA], dtype=object),
    })
    preview = for_streamlit(source)
    assert_frame_equal(preview, source)
    table = pa.Table.from_pandas(preview)
    assert pa.types.is_floating(table['numeric_object'].type)
    assert pa.types.is_integer(table['integer'].type)
    assert pa.types.is_date(table['date'].type)
    assert pa.types.is_timestamp(table['timestamp'].type)
    assert table['text'].to_pylist() == ['001', None]
    assert table['nulls'].null_count == 2


@pytest.mark.parametrize('strategy', ['keep', 'drop', 'value', 'median'])
@pytest.mark.parametrize('kind', ['csv_text', 'xlsx_number'])
def test_all_missing_strategies_preserve_cleaning_and_exports(strategy, kind):
    values = ['001', '003', None, float('nan'), pd.NA] if kind == 'csv_text' else [1, 3.5, None, float('nan'), pd.NA]
    source = pd.DataFrame({'возраст': values}, dtype=object)
    original = source.copy(deep=True)
    cleaned, report = clean_table(source, CleanOptions(missing_strategy=strategy, fill_value='нет'))
    before = cleaned.copy(deep=True)
    csv_before = export_table(cleaned, 'csv')
    preview = for_streamlit(cleaned)
    table = pa.Table.from_pandas(preview)
    assert table.num_rows == report.rows_after
    assert table['возраст'].null_count == (3 if strategy == 'keep' else 0)
    if strategy == 'median' and kind == 'csv_text':
        assert table['возраст'].to_pylist() == ['001', '003', '2.0', '2.0', '2.0']
        assert isinstance(cleaned.iloc[2, 0], float)
    if strategy == 'value' and kind == 'xlsx_number':
        assert table['возраст'].to_pylist() == ['1', '3.5', 'нет', 'нет', 'нет']
    assert_frame_equal(source, original)
    assert_frame_equal(cleaned, before)
    assert export_table(cleaned, 'csv') == csv_before
    book = load_workbook(BytesIO(export_table(cleaned, 'xlsx')))
    cell = book.active['A2']
    assert cell.value == values[0]
    assert cell.data_type == ('s' if kind == 'csv_text' else 'n')
    book.close()


@pytest.mark.parametrize('frame', [pd.DataFrame(), pd.DataFrame({'возраст': pd.Series([], dtype=object)})])
def test_empty_preview(frame):
    assert_frame_equal(for_streamlit(frame), frame)
    assert pa.Table.from_pandas(for_streamlit(frame)).num_rows == 0
