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


def test_missing_mask_mixed_types():
    frame = pd.DataFrame({
        'mixed': pd.Series([None, float('nan'), pd.NA, '', ' \t\n',
                            'NA', 'NULL', 0, False, 1.5], dtype=object),
        'number': pd.Series([pd.NA] + list(range(9)), dtype='Int64'),
        'text': pd.Series([' ', None] + ['keep'] * 8, dtype='string'),
    })
    snapshot = frame.copy(deep=True)
    expected = pd.DataFrame({
        'mixed': [True] * 5 + [False] * 5,
        'number': [True] + [False] * 9,
        'text': [True, True] + [False] * 8,
    })
    assert_frame_equal(missing_mask(frame), expected)
    assert_frame_equal(frame, snapshot)


@pytest.mark.parametrize('dtype', [object, 'str', 'string', 'Int64', 'boolean'])
def test_missing_mask_empty_columns_are_boolean(dtype):
    frame = pd.DataFrame({'empty': pd.Series([], dtype=dtype)})
    assert_frame_equal(missing_mask(frame), pd.DataFrame({'empty': pd.Series([], dtype=bool)}))


def test_clean_mixed_types_preserves_missing_values_and_counts():
    source = pd.DataFrame({'a': pd.Series([None, float('nan'), ' \t ', 0, False, ' A  B '], dtype=object)})
    snapshot = source.copy(deep=True)
    result, report = clean_table(source, CleanOptions(trim_spaces=True, remove_empty_rows=True))
    assert_frame_equal(result, pd.DataFrame({'a': pd.Series([0, False, 'A B'], dtype=object)}))
    assert_frame_equal(source, snapshot)
    assert report.empty_rows_removed == 3
    assert report.missing_before == 3
    assert report.missing_after == 0
    assert report.cells_changed == 2


@pytest.mark.parametrize('columns', [('unknown',), ('a', 'a'), ()])
def test_invalid_selection(columns):
    with pytest.raises(CleanerError):
        clean_table(pd.DataFrame({'a': ['x']}), CleanOptions(columns, trim_spaces=True))


def test_empty_result():
    result, report = clean_table(pd.DataFrame({'a': ['', ' ']}), CleanOptions(remove_empty_rows=True))
    assert result.empty and list(result.columns) == ['a']
    assert report.rows_before - report.rows_after == report.empty_rows_removed + report.duplicates_removed
