"""Small presentation-only catalog; user values and export schema stay unchanged."""
import re

EN = {
    'Чистые таблицы за несколько шагов · CSV / XLSX · Локальная обработка':
        'Clean tables in a few steps · CSV / XLSX · Local processing',
    'Исходный файл остаётся у вас. Удаление строк включается только вашим выбором.':
        'Your original file stays intact. Rows are removed only when you choose to do so.',
    'Загрузите таблицу до 10 МиБ':
        'Upload a table up to 10 MiB',
    'Исходные данные':
        'Source data',
    'Запустить обработку':
        'Run cleaning',
    'Для знакомства используйте examples/demo_input.csv или demo_input.xlsx.':
        'Try examples/demo_input.csv or demo_input.xlsx to get started.',
    'Параметры чтения':
        'Read settings',
    'Кодировка CSV':
        'CSV encoding',
    'Разделитель CSV':
        'CSV delimiter',
    'Номер листа XLSX (1 — первый)':
        'XLSX sheet number (1 = first)',
    'Первая строка — заголовок. При неверном предпросмотре выберите разделитель вручную. Для XLSX обрабатывается только выбранный лист.':
        'The first row contains headers. If the preview looks wrong, select the delimiter manually. Only the selected XLSX sheet is processed.',
    ' строк · ':
        ' rows · ',
    ' столбцов · ':
        ' columns · ',
    ' пустых значений. Показаны первые 20 строк.':
        ' missing cells. Showing the first 20 rows.',
    'Настройки очистки':
        'Cleaning settings',
    'Столбцы для очистки, дубликатов и обработки пропусков':
        'Columns for cleaning, duplicate comparison and missing values',
    'Очистить лишние пробелы':
        'Trim extra whitespace',
    'Удалить дубликаты':
        'Remove duplicates',
    'Удалить полностью пустые строки':
        'Remove fully empty rows',
    'Пробелы: обрезка по краям и замена повторяющихся пробельных символов одним пробелом, включая переносы строк. Дубликаты: сохраняется первая строка по выбранным столбцам; остальные строки удаляются целиком. Пустые строки проверяются по всем столбцам. Столбцы не удаляются.':
        'Whitespace: trim edges and collapse repeated whitespace, including line breaks. Duplicates: keep the first row based on selected columns and remove subsequent rows entirely. Empty rows are checked across all columns. Columns are never removed.',
    'Оставить пропуски без изменений':
        'Keep missing values unchanged',
    'Удалить строки с пропусками в выбранных столбцах':
        'Drop rows with missing values in selected columns',
    'Заполнить пропуски указанным значением':
        'Fill missing values with a supplied value',
    'Заполнить пропуски в числовых столбцах медианой':
        'Fill missing numeric values with the median',
    'Обработка пропусков':
        'Missing values',
    'Значение для заполнения':
        'Fill value',
    'Медиана: все непустые значения столбца должны быть числами или числовым текстом. Текстовые и полностью пустые столбцы остаются без изменений. Порядок: пробелы → пустые строки → дубликаты → обработка пропусков.':
        'Median: all nonempty values in a column must be numbers or numeric text. Text and fully empty columns stay unchanged. Order: whitespace → empty rows → duplicates → missing values.',
    'Результат':
        'Result',
    'Строк до → после':
        'Rows before → after',
    'Удалено дубликатов':
        'Duplicates removed',
    'Удалено пустых строк':
        'Empty rows removed',
    'Пустых значений до → после':
        'Missing cells before → after',
    'Заполнено ячеек':
        'Cells filled',
    'Осталось пропусков':
        'Missing cells remaining',
    'Удалено строк с пропусками':
        'Rows removed for missing values',
    'Формат результата':
        'Output format',
    'Разделитель результата CSV':
        'Output CSV delimiter',
    'Непредвиденная ошибка чтения. Технические подробности показаны в терминале сервера.':
        'Unexpected read error. Technical details are available in the server terminal.',
    'Изменено ячеек при очистке пробелов: ':
        'Cells changed by whitespace cleaning: ',
    '. Пустыми считаются отсутствующие значения, пустые строки и строки из пробелов; NA и NULL сохраняются как текст.':
        '. Missing values include absent values, empty strings and whitespace-only strings; NA and NULL remain text.',
    'Отчёт по столбцам':
        'Column report',
    'CSV хранит текст без изменений. Если значения начинаются с =, +, - или @, импортируйте их в Excel как текст: Excel может интерпретировать их как формулы. XLSX экспортирует такие значения текстом.':
        'CSV preserves text. If values begin with =, +, - or @, import them into Excel as text: Excel may interpret them as formulas. XLSX exports these values as text.',
    'Скачать очищенную таблицу':
        'Download cleaned table',
    'Скачать отчёт JSON':
        'Download JSON report',
    'Обрабатываем таблицу…':
        'Cleaning table…',
    'Ошибка обработки. Технические подробности показаны в терминале сервера.':
        'Processing error. Technical details are available in the server terminal.',
    'Ошибка экспорта. Технические подробности показаны в терминале сервера.':
        'Export error. Technical details are available in the server terminal.',
    'Авто':
        'Auto',
    'Табуляция':
        'Tab',
}

def translate(text, language):
    return EN[text] if language == 'en' else text

ERRORS = [('Выбран неизвестный столбец. Загрузите файл заново.',
  'Unknown column selected. Upload the file again.'),
 ('Столбцы для обработки не должны повторяться.', 'Processing columns must be unique.'),
 ('Неизвестный способ обработки пропусков.', 'Unknown missing-value strategy.'),
 ('Укажите непустое значение для заполнения пропусков.',
  'Enter a nonempty value to fill missing cells.'),
 ('Выберите хотя бы один столбец для обработки.', 'Select at least one column to process.'),
 ('В файле нет заголовка таблицы.', 'The file has no table header.'),
 ('Разрешено не более {0} столбцов.', 'At most {0} columns are allowed.'),
 ('Таблица слишком большая: максимум 100 000 строк и 1 000 000 ячеек.',
  'Table too large: at most 100,000 rows and 1,000,000 cells.'),
 ('Файл превышает лимит 10 МиБ.', 'The file exceeds the 10 MiB limit.'),
 ('Файл пуст. Добавьте заголовок и данные.', 'The file is empty. Add a header and data.'),
 ('Поддерживаются только CSV и XLSX, без XLS/XLSM.',
  'Only CSV and XLSX are supported; XLS/XLSM are not supported.'),
 ('Выберите CSV или XLSX.', 'Choose CSV or XLSX.'),
 ('Неподдерживаемая кодировка.', 'Unsupported encoding.'),
 ('Не удалось прочитать UTF-8/UTF-16. Для старого русского CSV выберите cp1251.',
  'Cannot read UTF-8/UTF-16. Select cp1251 for older Russian CSV files.'),
 ('CSV пуст или содержит только пробелы.', 'CSV is empty or contains only whitespace.'),
 ('CSV содержит нулевые байты. Проверьте формат и кодировку.',
  'CSV contains null bytes. Check its format and encoding.'),
 ('Выберите разделитель: запятая, точка с запятой, табуляция или |.',
  'Choose a comma, semicolon, tab or | delimiter.'),
 ('Не удалось открыть XLSX ({0}). Файл повреждён, зашифрован или имеет другой формат.',
  'Cannot open XLSX ({0}). The file is damaged, encrypted or has a different format.'),
 ('Недопустимый разделитель экспорта.', 'Invalid export delimiter.'),
 ('В таблице есть управляющие символы, запрещённые в XLSX. Используйте CSV.',
  'The table contains control characters forbidden in XLSX. Use CSV.'),
 ('Файл не читается как {0}. Выберите другую кодировку.',
  'Cannot read the file as {0}. Choose another encoding.'),
 ('В таблице больше 200 столбцов.', 'The table has more than 200 columns.'),
 ('Некорректный CSV: {0}. Проверьте кавычки и разделитель.',
  'Invalid CSV: {0}. Check quotes and delimiter.'),
 ('Распакованный XLSX превышает лимит 50 МиБ.', 'The expanded XLSX exceeds the 50 MiB limit.'),
 ('XLSX с макросами не поддерживается.', 'XLSX files with macros are not supported.'),
 ('Лист с таким номером отсутствует.', 'No sheet exists at this number.'),
 ('В листе больше 200 столбцов.', 'The sheet has more than 200 columns.'),
 ('Лист пуст или первая строка не содержит заголовка.',
  'The sheet is empty or its first row has no headers.'),
 ('CSV: строка около {0} содержит {1} полей вместо {2}. Проверьте разделитель.',
  'CSV: line near {0} has {1} fields instead of {2}. Check the delimiter.'),
 ('XLSX допускает не более 32 767 символов в ячейке. Используйте CSV.',
  'XLSX supports at most 32,767 characters per cell. Use CSV.')]


def translate_error(message, language):
    if language == 'ru':
        return message
    for source, target in ERRORS:
        pattern = re.escape(source)
        pattern = re.sub(r'\\\{\d+\\\}', '(.*?)', pattern)
        match = re.fullmatch(pattern, message, flags=re.DOTALL)
        if match:
            return target.format(*match.groups())
    return 'Unable to process this table. Check the input file and settings.'


REPORT_RU = {'rows_before': 'Строк до обработки',
 'rows_after': 'Строк после обработки',
 'duplicates_removed': 'Удалено дубликатов',
 'empty_rows_removed': 'Удалено пустых строк',
 'missing_before': 'Пропусков до обработки',
 'missing_after': 'Пропусков после обработки',
 'missing_by_column_before': 'Пропуски по столбцам до обработки',
 'missing_by_column_after': 'Пропуски по столбцам после обработки',
 'cells_changed': 'Изменено ячеек при очистке пробелов',
 'cells_filled': 'Заполнено ячеек',
 'missing_rows_removed': 'Удалено строк с пропусками'}


def localized_report(report, language):
    # Translate only report labels, never nested user column names or values.
    return {(REPORT_RU[key] if language == 'ru' else key.replace('_', ' ').capitalize()): value
            for key, value in report.items()}
