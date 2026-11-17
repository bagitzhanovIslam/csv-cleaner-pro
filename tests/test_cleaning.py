import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from src.csv_cleaner.core import CleanOptions, CleanerError, clean_table, missing_mask


def test_disabled_options_preserve_source():
    source = pd.DataFrame({'a': [' x ', ' x ', ''], 'b': ['1', '1', '']})
    snapshot = source.copy(deep=True)
    result, report = clean_table(source, CleanOptions())
    assert_frame_equal(source, snapshot)
    assert_frame_equal(result, source)
    assert report.rows_before == report.rows_after == 3
    assert report.duplicates_removed == report.cells_changed == 0


def test_cleaning_order_and_report():
    source = pd.DataFrame({'name': ['  Demo  A ', 'Demo A', ' ', 'Demo B'],
                           'city': [' Алматы ', 'Алматы', None, '']})
    result, report = clean_table(source, CleanOptions(trim_spaces=True, remove_duplicates=True, remove_empty_rows=True))
    assert result.to_dict('list') == {'name': ['Demo A', 'Demo B'], 'city': ['Алматы', '']}
    assert report.rows_before == 4 and report.rows_after == 2
    assert report.duplicates_removed == report.empty_rows_removed == 1
    assert report.missing_before == 3 and report.missing_after == 1
    assert report.cells_changed == 3
    assert report.missing_by_column_before == {'name': 1, 'city': 2}


def test_columns_subset_keeps_other_cells_but_drops_entire_duplicate_row():
    source = pd.DataFrame({'id': ['01', '01'], 'text': ['  A  ', ' B ']})
    result, report = clean_table(source, CleanOptions(('id',), True, True))
    assert result.to_dict('list') == {'id': ['01'], 'text': ['  A  ']}
    assert report.duplicates_removed == 1


def test_empty_rows_use_all_columns():
    frame = pd.DataFrame({'a': ['', ''], 'b': ['keep', ' ']})
    result, report = clean_table(frame, CleanOptions(('a',), remove_empty_rows=True))
    assert len(result) == 1 and report.empty_rows_removed == 1


def test_missing_literals_and_whitespace():
    frame = pd.DataFrame({'a': ['', ' ', None, 'NA', 'NULL', 0, False]})
    assert missing_mask(frame)['a'].tolist() == [True, True, True, False, False, False, False]


@pytest.mark.parametrize('columns', [('unknown',), ('a', 'a'), ()])
def test_invalid_selection(columns):
    with pytest.raises(CleanerError):
        clean_table(pd.DataFrame({'a': ['x']}), CleanOptions(columns, trim_spaces=True))


def test_empty_result():
    result, report = clean_table(pd.DataFrame({'a': ['', ' ']}), CleanOptions(remove_empty_rows=True))
    assert result.empty and list(result.columns) == ['a']
    assert report.rows_before - report.rows_after == report.empty_rows_removed + report.duplicates_removed
