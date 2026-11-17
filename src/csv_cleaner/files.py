"""Strict bounded CSV/XLSX input and in-memory export."""
import csv
from io import BytesIO, StringIO
from itertools import chain
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import IllegalCharacterError, InvalidFileException

from .core import CleanerError

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_EXPANDED_BYTES = 50 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 200
MAX_CELLS = 1_000_000
ENCODINGS = ('utf-8-sig', 'utf-16', 'cp1251')
SEPARATORS = (',', ';', '\t', '|')


def _headers(raw: list[object]) -> list[str]:
    """Preserve original labels; disambiguate blanks/duplicates without collisions."""
    labels = [str(x) if x is not None and str(x) != '' else f'Column {i + 1}'
              for i, x in enumerate(raw)]
    reserved = set(labels)
    used: set[str] = set()
    result = []
    for base in labels:
        name, suffix = base, 2
        if name in used:
            while True:
                name = f'{base} [{suffix}]'
                suffix += 1
                if name not in used and name not in reserved:
                    break
        used.add(name)
        result.append(name)
    return result


def _frame(rows: list[list], header: list) -> pd.DataFrame:
    if not header:
        raise CleanerError('В файле нет заголовка таблицы.')
    if len(header) > MAX_COLUMNS:
        raise CleanerError(f'Разрешено не более {MAX_COLUMNS} столбцов.')
    return pd.DataFrame(rows, columns=_headers(header), dtype=object)


def _check_bounds(row_count: int, width: int) -> None:
    if row_count > MAX_ROWS or row_count * width > MAX_CELLS:
        raise CleanerError('Таблица слишком большая: максимум 100 000 строк и 1 000 000 ячеек.')


def _decode(data: bytes, encoding: str) -> str:
    if encoding != 'auto':
        if encoding not in ENCODINGS:
            raise CleanerError('Неподдерживаемая кодировка.')
        try:
            return data.decode(encoding)
        except UnicodeError as exc:
            raise CleanerError(f'Файл не читается как {encoding}. Выберите другую кодировку.') from exc
    chosen = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    try:
        return data.decode(chosen)
    except UnicodeError as exc:
        raise CleanerError('Не удалось прочитать UTF-8/UTF-16. Для старого русского CSV выберите cp1251.') from exc


def read_table(data: bytes, filename: str, *, encoding: str = 'auto',
               separator: str = 'auto', sheet: int = 0) -> pd.DataFrame:
    if len(data) > MAX_FILE_BYTES:
        raise CleanerError('Файл превышает лимит 10 МиБ.')
    if not data:
        raise CleanerError('Файл пуст. Добавьте заголовок и данные.')
    suffix = Path(filename).suffix.lower()
    if suffix == '.csv':
        text = _decode(data, encoding)
        if not text.strip():
            raise CleanerError('CSV пуст или содержит только пробелы.')
        if '\x00' in text:
            raise CleanerError('CSV содержит нулевые байты. Проверьте формат и кодировку.')
        if separator == 'auto':
            try:
                separator = csv.Sniffer().sniff(text[:65536], delimiters=',;\t|').delimiter
            except csv.Error:
                separator = ','
        if separator not in SEPARATORS:
            raise CleanerError('Выберите разделитель: запятая, точка с запятой, табуляция или |.')
        try:
            reader = csv.reader(StringIO(text, newline=''), delimiter=separator, strict=True)
            header = next(reader)
            if len(header) > MAX_COLUMNS:
                raise CleanerError('В таблице больше 200 столбцов.')
            rows = []
            for row in reader:
                if not row:
                    row = [''] * len(header)
                if len(row) != len(header):
                    raise CleanerError(f'CSV: строка около {reader.line_num} содержит {len(row)} полей вместо {len(header)}. Проверьте разделитель.')
                rows.append(row)
                _check_bounds(len(rows), len(header))
            return _frame(rows, header)
        except (csv.Error, StopIteration) as exc:
            raise CleanerError(f'Некорректный CSV: {exc}. Проверьте кавычки и разделитель.') from exc
    if suffix != '.xlsx':
        raise CleanerError('Поддерживаются только CSV и XLSX, без XLS/XLSM.')
    try:
        with ZipFile(BytesIO(data)) as archive:
            if sum(i.file_size for i in archive.infolist()) > MAX_EXPANDED_BYTES:
                raise CleanerError('Распакованный XLSX превышает лимит 50 МиБ.')
            if any('vbaproject' in i.filename.lower() for i in archive.infolist()):
                raise CleanerError('XLSX с макросами не поддерживается.')
        workbook = load_workbook(BytesIO(data), read_only=True, data_only=False, keep_links=False)
        try:
            if not 0 <= sheet < len(workbook.worksheets):
                raise CleanerError('Лист с таким номером отсутствует.')
            worksheet = workbook.worksheets[sheet]
            if worksheet.max_column and worksheet.max_column > MAX_COLUMNS:
                raise CleanerError('В листе больше 200 столбцов.')
            iterator = worksheet.iter_rows(values_only=True)
            header = list(next(iterator, ()))
            if not header or all(v is None for v in header):
                raise CleanerError('Лист пуст или первая строка не содержит заголовка.')
            rows = []
            for values in iterator:
                rows.append(list(values))
                _check_bounds(len(rows), len(header))
            return _frame(rows, header)
        finally:
            workbook.close()
    except CleanerError:
        raise
    except (BadZipFile, InvalidFileException, KeyError, ValueError, OSError, EOFError, SyntaxError, RuntimeError) as exc:
        raise CleanerError(f'Не удалось открыть XLSX ({type(exc).__name__}). Файл повреждён, зашифрован или имеет другой формат.') from exc


def export_table(frame: pd.DataFrame, format: str, *, separator: str = ',') -> bytes:
    if format == 'csv':
        if separator not in SEPARATORS:
            raise CleanerError('Недопустимый разделитель экспорта.')
        return frame.to_csv(index=False, sep=separator, lineterminator='\n').encode('utf-8-sig')
    if format != 'xlsx':
        raise CleanerError('Выберите CSV или XLSX.')
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Cleaned data'
    try:
        rows = chain([list(frame.columns)], frame.itertuples(index=False, name=None))
        for row_number, row in enumerate(rows, start=1):
            for value in row:
                if isinstance(value, str) and len(value) > 32767:
                    raise CleanerError('XLSX допускает не более 32 767 символов в ячейке. Используйте CSV.')
            worksheet.append([None if pd.isna(v) else v for v in row])
            for column_number, value in enumerate(row, start=1):
                if isinstance(value, str):
                    # Formula-looking content is always literal text.
                    worksheet.cell(row_number, column_number).data_type = 's'
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()
    except IllegalCharacterError as exc:
        raise CleanerError('В таблице есть управляющие символы, запрещённые в XLSX. Используйте CSV.') from exc
    finally:
        workbook.close()
