# Настоящие скриншоты

[README](../README_RU.md) · [English README](../README.md)

17 ноября 2026 года сняты три настоящих кадра английского интерфейса в локальном
Chromium через Playwright. Использован только `examples/demo_input.csv`.
Кадры проверены визуально; таблицы содержат вымышленные данные.

- `screenshots/01-source.png`: исходная таблица, 6 строк, 4 столбца, 9 пропусков.
- `screenshots/02-settings.png`: все столбцы, три включённых правила, пропуски сохраняются.
- `screenshots/03-result.png`: 6 → 3 строки, 1 дубликат, 2 пустые строки,
  9 → 1 пропуск, очищенная таблица и кнопки скачивания.

## Повторная автоматическая съёмка

Необязательные инструменты устанавливаются только в `.venv`, без sudo:

```bash
.venv/bin/python -m pip install playwright
PLAYWRIGHT_BROWSERS_PATH=.venv/playwright-browsers .venv/bin/python -m playwright install chromium
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8507
```

В другом терминале из корня проекта:

```bash
PLAYWRIGHT_BROWSERS_PATH=.venv/playwright-browsers .venv/bin/python scripts/capture_screenshots.py
```

Скрипт делает снимки настоящего приложения с окном 1440×1100, проверяет скачивание
CSV/XLSX/JSON и переключение на русский с сохранением файла и результата.
Playwright и браузер не нужны для обычного запуска приложения или pytest.

## Ручная съёмка

Если браузерная автоматизация недоступна, откройте локальное приложение в браузере,
выберите English и загрузите `examples/demo_input.csv`. Снимите исходную таблицу.
Включите Trim extra whitespace, Remove duplicates, Remove fully empty rows,
оставьте Keep missing values unchanged и снимите настройки вместе с Run cleaning.
Запустите обработку, выберите XLSX и снимите результат вместе с метриками и скачиванием.
Используйте имена файлов выше, масштаб 100%, окно около 1440×1100.
Проверьте читаемость и отсутствие личных данных. Не подменяйте снимки макетами.
