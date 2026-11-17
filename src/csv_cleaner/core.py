"""Pure cleaning functions; no file or UI side effects."""
from dataclasses import dataclass, asdict
import re
import pandas as pd


class CleanerError(ValueError):
    """An actionable error safe to display to the user."""


@dataclass(frozen=True)
class CleanOptions:
    columns: tuple[str, ...] | None = None
    trim_spaces: bool = False
    remove_duplicates: bool = False
    remove_empty_rows: bool = False


def missing_mask(frame: pd.DataFrame) -> pd.DataFrame:
    """Empty strings and whitespace count as missing; literal NA/NULL do not."""
    return frame.isna() | frame.map(lambda x: isinstance(x, str) and not x.strip())


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

    def to_dict(self) -> dict:
        return asdict(self)


def clean_table(frame: pd.DataFrame, options: CleanOptions) -> tuple[pd.DataFrame, CleanReport]:
    columns = list(frame.columns if options.columns is None else options.columns)
    if any(c not in frame.columns for c in columns):
        raise CleanerError('Выбран неизвестный столбец. Загрузите файл заново.')
    if len(set(columns)) != len(columns):
        raise CleanerError('Столбцы для обработки не должны повторяться.')
    if not columns and (options.trim_spaces or options.remove_duplicates):
        raise CleanerError('Выберите хотя бы один столбец для очистки или поиска дубликатов.')
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
    after = missing_mask(result)
    report = CleanReport(len(frame), len(result), duplicates, empty_removed,
                         int(before.sum().sum()), int(after.sum().sum()),
                         {str(k): int(v) for k, v in before.sum().items()},
                         {str(k): int(v) for k, v in after.sum().items()}, changed)
    return result.reset_index(drop=True), report
