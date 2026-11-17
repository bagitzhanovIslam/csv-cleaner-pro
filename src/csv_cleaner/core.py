"""Pure cleaning functions; no file or UI side effects."""
from dataclasses import dataclass, asdict
import re
import math
from numbers import Real
import pandas as pd


class CleanerError(ValueError):
    """An actionable error safe to display to the user."""


@dataclass(frozen=True)
class CleanOptions:
    columns: tuple[str, ...] | None = None
    trim_spaces: bool = False
    remove_duplicates: bool = False
    remove_empty_rows: bool = False
    missing_strategy: str = "keep"
    fill_value: str = ""


def missing_mask(frame: pd.DataFrame) -> pd.DataFrame:
    """Empty strings and whitespace count as missing; literal NA/NULL do not."""
    # Empty string columns can retain their string dtype after map (pandas 3).
    whitespace = frame.map(lambda x: isinstance(x, str) and not x.strip()).astype(bool)
    return frame.isna() | whitespace


@dataclass(frozen=True)
class CleanReport:
    rows_before: int
    rows_after: int
    duplicates_removed: int
    empty_rows_removed: int
    missing_before: int
    missing_after: int
    missing_by_column_before: dict[str, int]
    missing_by_column_after: dict[str, int]
    cells_changed: int
    cells_filled: int
    missing_rows_removed: int

    def to_dict(self) -> dict:
        return asdict(self)


def clean_table(frame: pd.DataFrame, options: CleanOptions) -> tuple[pd.DataFrame, CleanReport]:
    columns = list(frame.columns if options.columns is None else options.columns)
    if any(c not in frame.columns for c in columns):
        raise CleanerError('Выбран неизвестный столбец. Загрузите файл заново.')
    if len(set(columns)) != len(columns):
        raise CleanerError('Столбцы для обработки не должны повторяться.')
    if options.missing_strategy not in {"keep", "drop", "value", "median"}:
        raise CleanerError("Неизвестный способ обработки пропусков.")
    if options.missing_strategy == "value" and not options.fill_value.strip():
        raise CleanerError("Укажите непустое значение для заполнения пропусков.")
    if not columns and (options.trim_spaces or options.remove_duplicates or options.missing_strategy != "keep"):
        raise CleanerError('Выберите хотя бы один столбец для обработки.')
    result = frame.copy(deep=True)
    before = missing_mask(frame)
    changed = 0
    if options.trim_spaces:
        for col in columns:
            def normalize(value: object) -> object:
                nonlocal changed
                if isinstance(value, str):
                    cleaned = re.sub(r'\s+', ' ', value).strip()
                    changed += cleaned != value
                    return cleaned
                return value
            result[col] = result[col].map(normalize)
    empty_removed = 0
    if options.remove_empty_rows:
        empty = missing_mask(result).all(axis=1)
        empty_removed = int(empty.sum())
        result = result.loc[~empty].copy()
    duplicates = 0
    if options.remove_duplicates:
        old_count = len(result)
        result = result.drop_duplicates(subset=columns, keep='first').copy()
        duplicates = old_count - len(result)
    # Remove rows before filling, so fills never hide empty rows or duplicates.
    missing_removed = 0
    filled = 0
    if options.missing_strategy == 'drop':
        drop = missing_mask(result)[columns].any(axis=1)
        missing_removed = int(drop.sum())
        result = result.loc[~drop].copy()
    elif options.missing_strategy in {'value', 'median'}:
        mask = missing_mask(result)
        for col in columns:
            gaps = mask[col]
            if not gaps.any():
                continue
            replacement = options.fill_value
            if options.missing_strategy == 'median':
                present = result.loc[~gaps, col]
                # Numeric text is supported for CSV; boolean/date/text columns are not.
                if present.empty or not present.map(
                    lambda v: isinstance(v, (str, Real)) and not isinstance(v, bool)
                ).all():
                    continue
                numbers = pd.to_numeric(present, errors='coerce')
                if numbers.isna().any() or not numbers.map(math.isfinite).all():
                    continue
                ordered = sorted(float(v) for v in numbers)
                middle = len(ordered) // 2
                replacement = (ordered[middle] if len(ordered) % 2 else
                               ordered[middle - 1] / 2 + ordered[middle] / 2)
                if not math.isfinite(replacement):
                    continue
            # Object assignment supports string/nullable numeric dtypes without
            # incompatible-dtype warnings or coercion of existing values.
            values = result[col].astype(object)
            values.loc[gaps] = replacement
            result[col] = values
            filled += int(gaps.sum())
    after = missing_mask(result)
    report = CleanReport(len(frame), len(result), duplicates, empty_removed,
                         int(before.sum().sum()), int(after.sum().sum()),
                         {str(k): int(v) for k, v in before.sum().items()},
                         {str(k): int(v) for k, v in after.sum().items()}, changed, filled, missing_removed)
    return result.reset_index(drop=True), report
