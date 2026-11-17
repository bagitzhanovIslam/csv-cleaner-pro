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


@pytest.mark.parametrize('strategy', ['keep', 'drop', 'value', 'median'])
def test_missing_strategies_mixed_russian(strategy):
    frame = pd.DataFrame({
        'Число': pd.Series([1, 3, None, float('nan'), '', ' \t'], dtype=object),
        'Текст': ['Москва', 'Москва', '', None, 'Казань', 'Омск'],
        'Смешанный': ['1', 'текст', None, '', ' ', 4],
    })
    snapshot = frame.copy(deep=True)
    result, report = clean_table(frame, CleanOptions(('Число',), missing_strategy=strategy, fill_value='нет'))
    assert_frame_equal(frame, snapshot)
    assert report.cells_filled == (4 if strategy in {'value', 'median'} else 0)
    assert report.missing_rows_removed == (4 if strategy == 'drop' else 0)
    if strategy in {'value', 'median'}:
        assert result['Число'].tolist() == [1, 3] + (['нет'] * 4 if strategy == 'value' else [2.0] * 4)
        assert_frame_equal(result[['Текст', 'Смешанный']], frame[['Текст', 'Смешанный']])
    assert report.missing_after == int(missing_mask(result).sum().sum())
    assert report.rows_before - report.rows_after == report.missing_rows_removed


def test_median_numeric_text_and_non_numeric_columns():
    frame = pd.DataFrame({'CSV': ['001', '3', ' ', None],
                          'Текст': ['Москва', None, '', 'Омск'],
                          'Смешанный': [1, 'нет', None, ''],
                          'Флаги': [True, False, None, None],
                          'Дата': [pd.Timestamp('2026-01-01'), None, None, None]})
    result, report = clean_table(frame, CleanOptions(missing_strategy='median'))
    assert result['CSV'].tolist() == ['001', '3', 2.0, 2.0]
    assert_frame_equal(result.drop(columns='CSV'), frame.drop(columns='CSV'))
    assert report.cells_filled == 2


@pytest.mark.parametrize('dtype', ['float64', 'Int64', 'Float64', 'string', object])
def test_median_all_missing_columns(dtype):
    frame = pd.DataFrame({'Пусто': pd.Series([None, None], dtype=dtype)})
    result, report = clean_table(frame, CleanOptions(missing_strategy='median'))
    assert_frame_equal(result, frame)
    assert report.cells_filled == 0 and report.missing_after == 2


@pytest.mark.parametrize('dtype', ['Int64', 'Float64', 'string', object])
@pytest.mark.parametrize('strategy', ['value', 'median'])
def test_fill_nullable_types_without_warnings(dtype, strategy):
    frame = pd.DataFrame({'a': pd.Series([1, 2, None], dtype=dtype) if dtype != 'string'
                          else pd.Series(['1', '2', None], dtype=dtype)})
    result, report = clean_table(frame, CleanOptions(missing_strategy=strategy, fill_value='готово'))
    assert result.iloc[:2, 0].tolist() == frame.iloc[:2, 0].tolist()
    assert result.iloc[2, 0] == ('готово' if strategy == 'value' else 1.5)
    assert report.cells_filled == 1


@pytest.mark.parametrize('options', [CleanOptions(missing_strategy='bad'),
    CleanOptions(missing_strategy='value'), CleanOptions(missing_strategy='value', fill_value=' \t'),
    CleanOptions((), missing_strategy='drop')])
def test_invalid_missing_options(options):
    with pytest.raises(CleanerError):
        clean_table(pd.DataFrame({'a': [None]}), options)


def test_removals_before_fill_and_json_report():
    import json
    frame = pd.DataFrame({'Город': ['Москва', 'Москва', '', 'Омск'], 'Цена': ['1', '1', '', '']})
    result, report = clean_table(frame, CleanOptions(remove_duplicates=True, remove_empty_rows=True,
                                                    missing_strategy='value', fill_value='нет'))
    assert len(result) == 2
    assert report.duplicates_removed == report.empty_rows_removed == report.cells_filled == 1
    assert json.loads(json.dumps(report.to_dict()))['cells_filled'] == 1


@pytest.mark.parametrize('values,expected', [([1e308, 1e308, None], 1e308),
    ([-1e308, 1e308, None], 0), ([float('inf'), 1, None], None),
    (['NaN', '1', None], None)])
def test_median_extreme_and_nonfinite_values(values, expected):
    frame = pd.DataFrame({'a': values}, dtype=object)
    result, report = clean_table(frame, CleanOptions(missing_strategy='median'))
    if expected is None:
        assert result.iloc[2, 0] is None and report.cells_filled == 0
    else:
        assert result.iloc[2, 0] == expected and report.cells_filled == 1


@pytest.mark.parametrize('strategy', ['keep', 'drop', 'value', 'median'])
def test_missing_strategies_header_only(strategy):
    source = pd.DataFrame({'Цена': pd.Series([], dtype='Float64')})
    result, report = clean_table(source, CleanOptions(missing_strategy=strategy, fill_value='нет'))
    assert_frame_equal(result, source)
    assert report.cells_filled == report.missing_rows_removed == report.missing_after == 0
