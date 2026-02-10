from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass(frozen=True)
class Margins:
    """Margins specified as fractions of figure width."""
    left: float = 0.04
    right: float = 0.02
    top: float = 0.04
    bottom: float = 0.02


@dataclass
class Config:
    xlsx_path: Path
    sheet2panel: dict[str, str]          # sheet name -> panel ID (single character)
    layout_rows: list[str]               # e.g. ["IIJJ", "KKKK", "0000"]
    margins: Margins = Margins()
    figsize: tuple[float, float] = (7.0, 5.0)
    output_svg: Path = Path("figure.svg")


def _coerce_xlsx_path(raw: Any) -> Path:
    """
    Support both:
      xlsx_path: /path/to/file.xlsx
    and the (common accidental) form:
      xlsx_path:
        /path/to/file.xlsx
    """
    if isinstance(raw, str):
        return Path(raw).expanduser()
    if isinstance(raw, dict) and len(raw) == 1:
        only_key = next(iter(raw.keys()))
        if isinstance(only_key, str):
            return Path(only_key).expanduser()
    raise ValueError("xlsx_path must be a string path (recommended: xlsx_path: /path/to/file.xlsx).")


def _coerce_layout_rows(raw: Any) -> list[str]:
    """Allow layout to be provided as a YAML block string or a list of strings."""
    if isinstance(raw, list) and all(isinstance(x, str) for x in raw):
        rows = [r.rstrip("\n") for r in raw if r.strip() != ""]
        if not rows:
            raise ValueError("layout cannot be empty.")
        return rows

    if isinstance(raw, str):
        rows = [r for r in raw.splitlines() if r.strip() != ""]
        if not rows:
            raise ValueError("layout cannot be empty.")
        return rows

    raise ValueError("layout must be a list of strings or a multiline string (use layout: | ...).")


def _validate_sheet2panel(sheet2panel: dict[str, str]) -> None:
    if not isinstance(sheet2panel, dict) or not sheet2panel:
        raise ValueError("sheet2panel must be a non-empty mapping of sheet name -> panel character.")
    for sheet, panel in sheet2panel.items():
        if not isinstance(sheet, str) or sheet.strip() == "":
            raise ValueError("sheet2panel keys must be non-empty strings (sheet names).")
        if not isinstance(panel, str) or len(panel) != 1:
            raise ValueError(f"sheet2panel value for sheet '{sheet}' must be a single character panel ID; got {panel!r}.")
        if panel == "0":
            raise ValueError("Panel ID '0' is reserved for the LEGEND panel; do not map sheets to panel '0'.")


def _validate_xlsx_sheets_exist(xlsx_path: Path, sheet2panel: dict[str, str]) -> None:
    if not xlsx_path.exists():
        raise FileNotFoundError(f"xlsx_path does not exist: {xlsx_path}")

    try:
        xl = pd.ExcelFile(xlsx_path)
    except Exception as e:
        raise RuntimeError(f"Failed to open xlsx file: {xlsx_path}") from e

    missing = [s for s in sheet2panel.keys() if s not in xl.sheet_names]
    if missing:
        raise ValueError(f"These keys in sheet2panel are not sheets in the xlsx file: {missing}")


def load_config(yaml_path: Path) -> Config:
    """Load YAML configuration and perform input checks that don't require figure construction."""
    if not yaml_path.exists():
        raise FileNotFoundError(f"Config YAML not found: {yaml_path}")

    data = yaml.safe_load(yaml_path.read_text())
    if not isinstance(data, dict):
        raise ValueError("YAML top-level must be a mapping/dict.")

    xlsx_path = _coerce_xlsx_path(data.get("xlsx_path"))
    sheet2panel = data.get("sheet2panel", {})
    _validate_sheet2panel(sheet2panel)

    layout_rows = _coerce_layout_rows(data.get("layout"))

    margins_raw = data.get("margins", {})
    margins = Margins(**margins_raw) if isinstance(margins_raw, dict) else Margins()

    figsize_raw = data.get("figsize", (7.0, 5.0))
    if not (isinstance(figsize_raw, (list, tuple)) and len(figsize_raw) == 2):
        raise ValueError("figsize must be a 2-element list/tuple like [7, 5].")
    figsize = (float(figsize_raw[0]), float(figsize_raw[1]))

    output_svg_raw = data.get("output_svg", "figure.svg")
    output_svg = Path(output_svg_raw).expanduser()

    _validate_xlsx_sheets_exist(xlsx_path, sheet2panel)

    return Config(xlsx_path=xlsx_path, sheet2panel=dict(sheet2panel),
                  layout_rows=layout_rows, margins=margins, figsize=figsize, output_svg=output_svg)
