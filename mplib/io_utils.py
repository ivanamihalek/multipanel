"""I/O helpers for reading YAML specs and XLSX sheet data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Mapping, Sequence, Set, Union

import pandas as pd
import yaml

from mplib.config import PlotSpec


def _normalize_layout(layout_value: Union[str, Sequence[str]], ) -> List[str]:
    """Normalizes YAML layout to a list of row strings.

    Accepts either:
      - a block string with newlines, or
      - a list of strings.

    Returns:
      List of non-empty row strings.
    """
    if isinstance(layout_value, str):
        rows = [row.strip() for row in layout_value.splitlines()]
        rows = [row for row in rows if row.strip() != ""]
        return rows

    rows = [str(row).strip() for row in layout_value]
    rows = [row for row in rows if row.strip() != ""]
    return rows


def load_plot_spec(path: Path, ) -> PlotSpec:
    """Loads PlotSpec from YAML.
    Args:
      path: YAML file path.
    Returns:
      PlotSpec instance.
    Raises:
      ValueError: If required fields are missing or malformed.
    """

    if not path.exists():
        raise Exception(f"Path {path} does not exist")

    data: Mapping[str, Any]
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise Exception(f"No data found in {path}.")

    if "sheet2panel" not in data:
        raise ValueError("YAML missing required key: sheet2panel")
    if "layout" not in data:
        raise ValueError("YAML missing required key: layout")

    sheet2panel_raw = data["sheet2panel"]
    if not isinstance(sheet2panel_raw, dict):
        raise ValueError("sheet2panel must be a mapping.")

    # Force string keys/values.
    sheet2panel: Mapping[str, str] = {str(k): str(v) for k, v in sheet2panel_raw.items()}

    layout_rows = _normalize_layout(layout_value=data["layout"])

    return PlotSpec(sheet2panel=sheet2panel, layout_rows=layout_rows, )


def list_xlsx_sheet_names(xlsx_path: Path, ) -> Set[str]:
    """Lists sheet names in the input XLSX."""
    xl = pd.ExcelFile(xlsx_path)
    return set(xl.sheet_names)


def load_sheet_dataframe(xlsx_path: Path, sheet_name: str) -> pd.DataFrame:
    """Loads a sheet as a DataFrame.

    Expected minimal columns for the simple default plot:
      - x
      - y

    Args:
      xlsx_path: XLSX path.
      sheet_name: Sheet name to read.

    Returns:
      DataFrame for that sheet.
    """
    return pd.read_excel(xlsx_path, sheet_name=sheet_name)
