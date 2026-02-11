import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


def _infer_plot_type(df: pd.DataFrame) -> str:
    """Infer plot type from DataFrame dimensions."""
    rows, cols = df.shape
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

        panel_data[panel_label] = (df, plot_type)

    return panel_data
