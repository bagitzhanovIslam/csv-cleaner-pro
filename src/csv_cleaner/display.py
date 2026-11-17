"""Arrow-safe copies for previews; never use these frames for cleaning/export."""
import pandas as pd
import pyarrow as pa


def for_streamlit(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep Arrow-compatible columns native, stringify only incompatible ones.

    Object columns may legitimately mix CSV text and numeric median fills, or
    XLSX numbers and text fills. Arrow requires a single compatible column type.
    Pandas' nullable string dtype preserves nulls instead of displaying 'nan',
    'None' or '<NA>'. The source values and dtypes are never modified.
    """
    preview = frame.copy(deep=True)
    for position in range(len(preview.columns)):
        column = preview.iloc[:, position]
        try:
            pa.array(column, from_pandas=True)
        except (pa.ArrowInvalid, pa.ArrowTypeError, pa.ArrowNotImplementedError):
            preview.isetitem(position, column.astype('string'))
    return preview
