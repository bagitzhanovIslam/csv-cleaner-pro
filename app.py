"""Streamlit presentation layer. Run: streamlit run app.py."""
import hashlib
import json
import logging
import streamlit as st
from src.csv_cleaner.core import CleanerError, CleanOptions, clean_table, missing_mask
from src.csv_cleaner.files import read_table, export_table
from src.csv_cleaner.display import for_streamlit

st.set_page_config(page_title='CSV Cleaner Pro', page_icon='🧹', layout='wide')
st.title('CSV Cleaner Pro')
st.caption('Чистые таблицы за несколько шагов · CSV / XLSX · Локальная обработка')
st.info('Исходный файл остаётся у вас. Удаление строк включается только вашим выбором.')
upload = st.file_uploader('Загрузите таблицу до 10 МиБ', type=['csv', 'xlsx'])
if upload is None:
    st.session_state.pop('result', None)
    st.caption('Для знакомства используйте examples/demo_input.csv или demo_input.xlsx.')
    st.stop()
with st.expander('Параметры чтения', expanded=False):
    left, right = st.columns(2)
    encoding = left.selectbox('Кодировка CSV', ['auto', 'utf-8-sig', 'utf-16', 'cp1251'])
    delimiter = right.selectbox('Разделитель CSV', ['auto', ',', ';', '\t', '|'],
                                format_func=lambda x: {'auto': 'Авто', '\t': 'Табуляция'}.get(x, x))
    sheet = st.number_input('Номер листа XLSX (1 — первый)', min_value=1, value=1, step=1)
    st.caption('Первая строка — заголовок. При неверном предпросмотре выберите разделитель вручную. Для XLSX обрабатывается только выбранный лист.')
data = upload.getvalue()
source_key = (hashlib.sha256(data).hexdigest(), upload.name, encoding, delimiter, sheet)
try:
    frame = read_table(data, upload.name, encoding=encoding, separator=delimiter, sheet=int(sheet)-1)
except CleanerError as exc:
    st.session_state.pop('result', None)
    st.error(str(exc))
    st.stop()
except Exception:
    logging.exception('Unexpected input error')
    st.error('Непредвиденная ошибка чтения. Технические подробности показаны в терминале сервера.')
    st.stop()
st.subheader('Исходные данные')
st.caption(f'{len(frame):,} строк · {len(frame.columns)} столбцов · {int(missing_mask(frame).sum().sum())} пустых значений. Показаны первые 20 строк.')
st.dataframe(for_streamlit(frame.head(20)), hide_index=True, width='stretch')
with st.container(border=True):
    st.subheader('Настройки очистки')
    columns = st.multiselect('Столбцы для очистки, дубликатов и обработки пропусков',
                             list(frame.columns), default=list(frame.columns))
    c1, c2, c3 = st.columns(3)
    trim = c1.checkbox('Очистить лишние пробелы', value=False)
    duplicates = c2.checkbox('Удалить дубликаты', value=False)
    empty = c3.checkbox('Удалить полностью пустые строки', value=False)
    st.caption('Пробелы: обрезка по краям и замена повторяющихся пробельных символов одним пробелом, включая переносы строк. Дубликаты: сохраняется первая строка по выбранным столбцам; остальные строки удаляются целиком. Пустые строки проверяются по всем столбцам. Столбцы не удаляются.')
    strategies = {
        'keep': 'Оставить пропуски без изменений',
        'drop': 'Удалить строки с пропусками в выбранных столбцах',
        'value': 'Заполнить пропуски указанным значением',
        'median': 'Заполнить пропуски в числовых столбцах медианой',
    }
    strategy = st.selectbox('Обработка пропусков', list(strategies), format_func=strategies.get)
    fill_value = st.text_input('Значение для заполнения', disabled=strategy != 'value')
    st.caption('Медиана: все непустые значения столбца должны быть числами или числовым текстом. Текстовые и полностью пустые столбцы остаются без изменений. Порядок: пробелы → пустые строки → дубликаты → обработка пропусков.')
options = CleanOptions(tuple(columns), trim, duplicates, empty, strategy, fill_value)
result_key = (source_key, options)
if st.session_state.get('result_key') != result_key:
    st.session_state.pop('result', None)
if st.button('Запустить обработку', type='primary'):
    try:
        with st.spinner('Обрабатываем таблицу…'):
            st.session_state['result'] = clean_table(frame, options)
            st.session_state['result_key'] = result_key
    except CleanerError as exc:
        st.error(str(exc))
    except Exception:
        logging.exception('Unexpected cleaning error')
        st.error('Ошибка обработки. Технические подробности показаны в терминале сервера.')
if 'result' in st.session_state:
    cleaned, report = st.session_state['result']
    st.subheader('Результат')
    metrics = st.columns(4)
    metrics[0].metric('Строк до → после', f'{report.rows_before} → {report.rows_after}')
    metrics[1].metric('Удалено дубликатов', report.duplicates_removed)
    metrics[2].metric('Удалено пустых строк', report.empty_rows_removed)
    metrics[3].metric('Пустых значений до → после', f'{report.missing_before} → {report.missing_after}')
    extra = st.columns(3)
    extra[0].metric('Заполнено ячеек', report.cells_filled)
    extra[1].metric('Осталось пропусков', report.missing_after)
    extra[2].metric('Удалено строк с пропусками', report.missing_rows_removed)
    st.caption(f'Изменено ячеек при очистке пробелов: {report.cells_changed}. Пустыми считаются отсутствующие значения, пустые строки и строки из пробелов; NA и NULL сохраняются как текст.')
    st.dataframe(for_streamlit(cleaned.head(20)), hide_index=True, width='stretch')
    with st.expander('Отчёт по столбцам'):
        st.json(report.to_dict())
    format = st.radio('Формат результата', ['csv', 'xlsx'], horizontal=True)
    out_sep = st.selectbox('Разделитель результата CSV', [',', ';', '\t', '|'], disabled=format != 'csv')
    if format == 'csv':
        st.caption('CSV хранит текст без изменений. Если значения начинаются с =, +, - или @, импортируйте их в Excel как текст: Excel может интерпретировать их как формулы. XLSX экспортирует такие значения текстом.')
    try:
        output = export_table(cleaned, format, separator=out_sep)
        st.download_button('Скачать очищенную таблицу', output, file_name=f'cleaned.{format}',
                           mime='text/csv' if format == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        st.download_button('Скачать отчёт JSON', json.dumps(report.to_dict(), ensure_ascii=False, indent=2).encode(),
                           file_name='cleaning_report.json', mime='application/json')
    except CleanerError as exc:
        st.error(str(exc))
    except Exception:
        logging.exception('Unexpected export error')
        st.error('Ошибка экспорта. Технические подробности показаны в терминале сервера.')
