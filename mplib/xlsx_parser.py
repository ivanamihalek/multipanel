import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


def _infer_plot_type(df: pd.DataFrame) -> str:
    """Infer plot type from DataFrame dimensions."""
    rows, cols = df.shape

    # Check for bar plot
    if cols >= 2:
        first_col = df.iloc[:, 0]

        # the column names should be all strings
        col_names_all_strings = all(isinstance(val, str) for val in df.columns)
        data_start_idx = 1 if col_names_all_strings else 0

        # Get data column (skip header if present)
        data_col = first_col.iloc[data_start_idx:]

        # Check if first column has strings
        if data_col.dtype == object or all(isinstance(val, str) for val in data_col):
            distinct_count = data_col.nunique()

            # Check remaining columns are numeric
            remaining_cols = df.iloc[data_start_idx:, 1:]
            all_numeric = all(pd.api.types.is_numeric_dtype(remaining_cols[col])
                              for col in remaining_cols.columns)

            if distinct_count <= 10 and all_numeric:
                return 'bar'

    if cols == 2 and rows < 80:
        return 'scatter'

    elif cols == 2 and rows >= 80:
        return 'line'

    elif cols == 1 or (cols > 1 and rows > 1 and df.shape[0] < 10):
        # Treat single column or very short multi-column as histogram source
        return 'histogram'

    elif cols > 2 and rows > 2:
        return 'heatmap'

    else:
        raise Exception(f"Unknown plot type: {cols} {rows}")

def _coerce_header(sheet_name: str, df: pd.DataFrame) -> None:
    non_string_cols = [col for col in df.columns if not isinstance(col, str)]
    if non_string_cols:
        raise ValueError(f"Invalid header detected in '{sheet_name}' sheet Numeric values found in columns: {non_string_cols}")


def parse_xlsx_data(path: str|Path, sheet2panel: Dict[str, str]) -> Dict[str, Tuple[pd.DataFrame, str]]:
    """Parse Excel sheets and map to panel labels with inferred plot types."""
    try:
        xls = pd.ExcelFile(path)
    except Exception as e:
        print(f"Error loading Excel file: {e}", file=sys.stderr)
        sys.exit(1)

    panel_data: Dict[str, Tuple[pd.DataFrame, str]] = {}

    for sheet_name, panel_label in sheet2panel.items():
        if sheet_name not in xls.sheet_names:
            print(f"Warning: Sheet '{sheet_name}' not found in Excel file.", file=sys.stderr)
            continue

        df = pd.read_excel(xls, sheet_name=sheet_name)
        try:
            plot_type = _infer_plot_type(df)
        except Exception as e:
            print(f"Error parsing Excel file: {path}, sheet {sheet_name}", file=sys.stderr)
            print(f"{e}", file=sys.stderr)
            sys.exit(1)

        if plot_type not in ['heatmap']:  # any other tables without header?
            _coerce_header(sheet_name, df)

        panel_data[panel_label] = (df, plot_type)

    return panel_data
