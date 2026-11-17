"""Streamlit presentation layer. Run: streamlit run app.py."""
import hashlib
import json
import logging

import streamlit as st

from src.csv_cleaner.core import CleanerError, CleanOptions, clean_table, missing_mask
from src.csv_cleaner.display import for_streamlit
from src.csv_cleaner.files import export_table, read_table
from src.csv_cleaner.i18n import localized_report, translate, translate_error

st.set_page_config(page_title='CSV Cleaner Pro', page_icon='🧹', layout='wide')
language = st.selectbox('Language / Язык', ['en', 'ru'], format_func=lambda value: {'en': 'English', 'ru': 'Русский'}[value], key='language')


def t(text: str) -> str:
    return translate(text, language)

st.title('CSV Cleaner Pro')
st.caption(t('Чистые таблицы за несколько шагов · CSV / XLSX · Локальная обработка'))
st.info(t('Исходный файл остаётся у вас. Удаление строк включается только вашим выбором.'))
upload = st.file_uploader(t('Загрузите таблицу до 10 МиБ'), type=['csv', 'xlsx'], key='ui_upload_a_table_up_to_10_mib')
if upload is None:
    st.session_state.pop('result', None)
    st.caption(t('Для знакомства используйте examples/demo_input.csv или demo_input.xlsx.'))
    st.stop()
with st.expander(t('Параметры чтения'), expanded=False):
    left, right = st.columns(2)
    encoding = left.selectbox(t('Кодировка CSV'), ['auto', 'utf-8-sig', 'utf-16', 'cp1251'], format_func=lambda value: t('Авто') if value == 'auto' else value, key='ui_csv_encoding')
    delimiter = right.selectbox(t('Разделитель CSV'), ['auto', ',', ';', '\t', '|'], format_func=lambda x: {'auto': t('Авто'), '\t': t('Табуляция')}.get(x, x), key='ui_csv_delimiter')
    sheet = st.number_input(t('Номер листа XLSX (1 — первый)'), min_value=1, value=1, step=1, key='ui_xlsx_sheet_number_1_first')
    st.caption(t('Первая строка — заголовок. При неверном предпросмотре выберите разделитель вручную. Для XLSX обрабатывается только выбранный лист.'))
data = upload.getvalue()
source_key = (hashlib.sha256(data).hexdigest(), upload.name, encoding, delimiter, sheet)
try:
    frame = read_table(data, upload.name, encoding=encoding, separator=delimiter, sheet=int(sheet) - 1)
except CleanerError as exc:
    st.session_state.pop('result', None)
    st.error(translate_error(str(exc), language))
    st.stop()
except Exception:
    logging.exception('Unexpected input error')
    st.error(t('Непредвиденная ошибка чтения. Технические подробности показаны в терминале сервера.'))
    st.stop()
st.subheader(t('Исходные данные'))
st.caption(f"{len(frame):,}{t(' строк · ')}{len(frame.columns)}{t(' столбцов · ')}{int(missing_mask(frame).sum().sum())}{t(' пустых значений. Показаны первые 20 строк.')}")
st.dataframe(for_streamlit(frame.head(20)), hide_index=True, width='stretch')
with st.container(border=True):
    st.subheader(t('Настройки очистки'))
    columns = st.multiselect(t('Столбцы для очистки, дубликатов и обработки пропусков'), list(frame.columns), default=list(frame.columns), key='ui_columns_for_cleaning_duplicate_comparison_and_missing_values')
    c1, c2, c3 = st.columns(3)
    trim = c1.checkbox(t('Очистить лишние пробелы'), value=False, key='ui_trim_extra_whitespace')
    duplicates = c2.checkbox(t('Удалить дубликаты'), value=False, key='ui_remove_duplicates')
    empty = c3.checkbox(t('Удалить полностью пустые строки'), value=False, key='ui_remove_fully_empty_rows')
    st.caption(t('Пробелы: обрезка по краям и замена повторяющихся пробельных символов одним пробелом, включая переносы строк. Дубликаты: сохраняется первая строка по выбранным столбцам; остальные строки удаляются целиком. Пустые строки проверяются по всем столбцам. Столбцы не удаляются.'))
    strategies = {'keep': t('Оставить пропуски без изменений'), 'drop': t('Удалить строки с пропусками в выбранных столбцах'), 'value': t('Заполнить пропуски указанным значением'), 'median': t('Заполнить пропуски в числовых столбцах медианой')}
    strategy = st.selectbox(t('Обработка пропусков'), list(strategies), format_func=strategies.get, key='ui_missing_values')
    fill_value = st.text_input(t('Значение для заполнения'), disabled=strategy != 'value', key='ui_fill_value')
    st.caption(t('Медиана: все непустые значения столбца должны быть числами или числовым текстом. Текстовые и полностью пустые столбцы остаются без изменений. Порядок: пробелы → пустые строки → дубликаты → обработка пропусков.'))
options = CleanOptions(tuple(columns), trim, duplicates, empty, strategy, fill_value)
result_key = (source_key, options)
if st.session_state.get('result_key') != result_key:
    st.session_state.pop('result', None)
if st.button(t('Запустить обработку'), type='primary', key='ui_run_cleaning'):
    try:
        with st.spinner(t('Обрабатываем таблицу…')):
            st.session_state['result'] = clean_table(frame, options)
            st.session_state['result_key'] = result_key
    except CleanerError as exc:
        st.error(translate_error(str(exc), language))
    except Exception:
        logging.exception('Unexpected cleaning error')
        st.error(t('Ошибка обработки. Технические подробности показаны в терминале сервера.'))
if 'result' in st.session_state:
    cleaned, report = st.session_state['result']
    st.subheader(t('Результат'))
    metrics = st.columns(4)
    metrics[0].metric(t('Строк до → после'), f'{report.rows_before} → {report.rows_after}')
    metrics[1].metric(t('Удалено дубликатов'), report.duplicates_removed)
    metrics[2].metric(t('Удалено пустых строк'), report.empty_rows_removed)
    metrics[3].metric(t('Пустых значений до → после'), f'{report.missing_before} → {report.missing_after}')
    extra = st.columns(3)
    extra[0].metric(t('Заполнено ячеек'), report.cells_filled)
    extra[1].metric(t('Осталось пропусков'), report.missing_after)
    extra[2].metric(t('Удалено строк с пропусками'), report.missing_rows_removed)
    st.caption(f"{t('Изменено ячеек при очистке пробелов: ')}{report.cells_changed}{t('. Пустыми считаются отсутствующие значения, пустые строки и строки из пробелов; NA и NULL сохраняются как текст.')}")
    st.dataframe(for_streamlit(cleaned.head(20)), hide_index=True, width='stretch')
    with st.expander(t('Отчёт по столбцам')):
        st.json(localized_report(report.to_dict(), language))
    output_format = st.radio(t('Формат результата'), ['csv', 'xlsx'], horizontal=True, key='ui_output_format')
    out_sep = st.selectbox(t('Разделитель результата CSV'), [',', ';', '\t', '|'], format_func=lambda value: t('Табуляция') if value == '\t' else value, disabled=output_format != 'csv', key='ui_output_csv_delimiter')
    if output_format == 'csv':
        st.caption(t('CSV хранит текст без изменений. Если значения начинаются с =, +, - или @, импортируйте их в Excel как текст: Excel может интерпретировать их как формулы. XLSX экспортирует такие значения текстом.'))
    try:
        output = export_table(cleaned, output_format, separator=out_sep)
        st.download_button(t('Скачать очищенную таблицу'), output, file_name=f'cleaned.{output_format}', mime='text/csv' if output_format == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key='ui_download_cleaned_table')
        st.download_button(t('Скачать отчёт JSON'), json.dumps(report.to_dict(), ensure_ascii=False, indent=2).encode(), file_name='cleaning_report.json', mime='application/json', key='ui_download_json_report')
    except CleanerError as exc:
        st.error(translate_error(str(exc), language))
    except Exception:
        logging.exception('Unexpected export error')
        st.error(t('Ошибка экспорта. Технические подробности показаны в терминале сервера.'))
