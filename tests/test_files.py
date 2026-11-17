from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import pandas as pd
import pytest
from openpyxl import Workbook, load_workbook
from src.csv_cleaner.core import CleanerError
from src.csv_cleaner import files
from src.csv_cleaner.files import read_table, export_table


def xlsx_bytes(rows, second_sheet=False):
    book = Workbook()
    for row in rows:
        book.active.append(row)
    if second_sheet:
        book.create_sheet('Other').append(['Other header'])
    out = BytesIO()
    book.save(out)
    book.close()
    return out.getvalue()


@pytest.mark.parametrize('separator', [',', ';', '\t', '|'])
def test_separators_and_russian(separator):
    text = f'Код{separator}Город\n001{separator}Алматы\n'
    frame = read_table(text.encode(), 'demo.CSV')
    assert frame.to_dict('list') == {'Код': ['001'], 'Город': ['Алматы']}


@pytest.mark.parametrize('encoding', ['utf-8-sig', 'utf-16', 'cp1251'])
def test_encodings(encoding):
    text = 'Город;Описание\nАлматы;Тест\n'
    frame = read_table(text.encode(encoding), 'demo.csv', encoding=encoding)
    assert frame.iloc[0, 0] == 'Алматы'


def test_auto_utf16_and_cp1251_requires_choice():
    assert read_table('a\nПривет'.encode('utf-16'), 'x.csv').iloc[0, 0] == 'Привет'
    with pytest.raises(CleanerError, match='cp1251'):
        read_table('a\nПривет'.encode('cp1251'), 'x.csv')


def test_blank_rows_and_literals_preserved():
    frame = read_table(b'a,b\n001,NA\n\n,\nNULL,0\n', 'x.csv')
    assert len(frame) == 4
    assert frame.iloc[1].tolist() == ['', '']
    assert frame.iloc[0].tolist() == ['001', 'NA']


def test_duplicate_blank_and_colliding_headers():
    frame = read_table(b'a,a,a [2],,Column 4\nx,y,z,q,r\n', 'x.csv', separator=',')
    assert frame.columns.tolist() == ['a', 'a [3]', 'a [2]', 'Column 4', 'Column 4 [2]']
    assert frame.iloc[0].tolist() == ['x', 'y', 'z', 'q', 'r']


def test_quoted_multiline():
    frame = read_table(b'a,b\n"hello, world","line1\nline2"\n', 'x.csv', separator=',')
    assert frame.iloc[0].tolist() == ['hello, world', 'line1\nline2']


@pytest.mark.parametrize('data,name', [(b'', 'x.csv'), (b' \n', 'x.csv'),
                                      (b'', 'x.xlsx'), (b'not a zip', 'x.xlsx'),
                                      (b'a,b\n1,2,3', 'x.csv'),
                                      (b'a,b\n"unfinished', 'x.csv'),
                                      (b'abc', 'x.xls'), (b'a\n\x00', 'x.csv')])
def test_bad_files(data, name):
    with pytest.raises(CleanerError):
        read_table(data, name, separator=',')


def test_xlsx_and_sheet_selection():
    data = xlsx_bytes([['Код', 'Город'], ['001', 'Алматы'], [None, None], ['002', 'Астана']], True)
    frame = read_table(data, 'x.xlsx')
    assert len(frame) == 3 and frame.iloc[0].tolist() == ['001', 'Алматы']
    assert frame.iloc[1].isna().all()
    assert read_table(data, 'x.xlsx', sheet=1).columns.tolist() == ['Other header']
    with pytest.raises(CleanerError):
        read_table(data, 'x.xlsx', sheet=2)


def test_empty_xlsx():
    with pytest.raises(CleanerError):
        read_table(xlsx_bytes([]), 'x.xlsx')


@pytest.mark.parametrize('format', ['csv', 'xlsx'])
def test_export_roundtrip(format):
    original = pd.DataFrame({'Код': ['001', '002'], 'text': ['Алматы', 'NA']}, dtype=object)
    output = export_table(original, format)
    pd.testing.assert_frame_equal(read_table(output, f'result.{format}'), original)


def test_xlsx_formula_is_not_executed_or_exported_as_formula():
    data = xlsx_bytes([['=Header'], ['=1+1']])
    frame = read_table(data, 'x.xlsx')
    assert frame.iloc[0, 0] == '=1+1'
    output = export_table(frame, 'xlsx')
    book = load_workbook(BytesIO(output), data_only=False)
    assert book.active['A1'].data_type == book.active['A2'].data_type == 's'
    assert book.active['A2'].value == '=1+1'
    book.close()


def test_size_limits(monkeypatch):
    monkeypatch.setattr(files, 'MAX_FILE_BYTES', 5)
    with pytest.raises(CleanerError, match='10'):
        read_table(b'a\n12345', 'x.csv')


def test_row_and_column_limits(monkeypatch):
    monkeypatch.setattr(files, 'MAX_ROWS', 1)
    with pytest.raises(CleanerError):
        read_table(b'a\nx\ny', 'x.csv')
    monkeypatch.setattr(files, 'MAX_COLUMNS', 1)
    with pytest.raises(CleanerError):
        read_table(b'a,b\nx,y', 'x.csv', separator=',')


def test_zip_expansion_limit(monkeypatch):
    data = xlsx_bytes([['a'], ['b']])
    monkeypatch.setattr(files, 'MAX_EXPANDED_BYTES', 1)
    with pytest.raises(CleanerError, match='50'):
        read_table(data, 'x.xlsx')


def test_macro_rejected():
    out = BytesIO()
    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        z.writestr('xl/vbaProject.bin', b'not executable')
    with pytest.raises(CleanerError, match='макрос'):
        read_table(out.getvalue(), 'x.xlsx')


def test_header_only_and_empty_export():
    frame = read_table(b'a,b\n', 'x.csv', separator=',')
    assert frame.empty
    for format in ['csv', 'xlsx']:
        result = read_table(export_table(frame, format), f'x.{format}')
        assert result.empty and result.columns.tolist() == ['a', 'b']


def test_xlsx_export_refuses_silent_truncation():
    with pytest.raises(CleanerError, match='32 767'):
        export_table(pd.DataFrame({'a': ['x' * 32768]}), 'xlsx')


def test_invalid_export():
    with pytest.raises(CleanerError):
        export_table(pd.DataFrame({'a': ['x']}), 'pdf')


@pytest.mark.parametrize('format', ['csv', 'xlsx'])
@pytest.mark.parametrize('strategy', ['keep', 'drop', 'value', 'median'])
def test_export_after_missing_processing(format, strategy):
    from src.csv_cleaner.core import CleanOptions, clean_table, missing_mask
    original = pd.DataFrame({'Город': ['Москва', 'Москва', 'Омск', ' '],
                             'Цена': ['001', '001', '', None]}, dtype=object)
    cleaned, report = clean_table(original, CleanOptions(remove_duplicates=True,
        remove_empty_rows=True, missing_strategy=strategy, fill_value='нет'))
    restored = read_table(export_table(cleaned, format), f'result.{format}')
    assert len(restored) == report.rows_after
    assert restored.iloc[0].tolist() == ['Москва', '001']
    assert int(missing_mask(restored).sum().sum()) == report.missing_after
    if strategy == 'value':
        assert restored.iloc[1, 1] == 'нет'
    if strategy == 'median':
        assert float(restored.iloc[1, 1]) == 1
