"""Validation logic for comparing YAML spec with layout and XLSX sheets."""

from __future__ import annotations

import warnings
from typing import Iterable, Set

from mplib.config import PlotSpec


def _panels_in_layout(
    layout_rows: Iterable[str],
) -> Set[str]:
    """Returns the set of panel characters used in the mosaic layout."""
    panels: Set[str] = set()
    for row in layout_rows:
        for ch in row:
            if ch.isspace():
                continue
            panels.add(ch)
    return panels


def validate_spec_against_xlsx(
    spec: PlotSpec,
    xlsx_sheet_names: Set[str],
) -> None:
    """Validates sheet existence and panel/layout consistency.

    Rules:
      - Every key in sheet2panel must exist as an xlsx sheet name (else error).
      - All panel ids referenced in sheet2panel values must appear in layout (else error).
      - If layout contains panels not in sheet2panel (excluding '0'): warn.

    Args:
      spec: Parsed PlotSpec.
      xlsx_sheet_names: Actual sheet names in the XLSX.

    Raises:
      ValueError: If validation fails.
    """
    missing_sheets = [
        sheet_name
        for sheet_name in spec.sheet2panel.keys()
        if sheet_name not in xlsx_sheet_names
    ]
    if missing_sheets:
        raise ValueError(
            "YAML sheet2panel contains keys not found in XLSX sheets: "
            f"{missing_sheets}"
        )

    layout_panels = _panels_in_layout(
        layout_rows=spec.layout_rows,
    )
    mapped_panels = set(spec.sheet2panel.values())

    # If mapping references panel ids not present in layout → error.
    mapping_not_in_layout = sorted(mapped_panels - layout_panels)
    if mapping_not_in_layout:
        raise ValueError(
            "sheet2panel contains panel ids not present in layout: "
            f"{mapping_not_in_layout}"
        )

    # If layout has extra panels beyond mapping: warn (except '0').
    layout_not_in_mapping = sorted((layout_panels - mapped_panels) - {"0"})
    if layout_not_in_mapping:
        warnings.warn(
            "layout contains panel ids not mapped from any sheet; "
            "these panels will be empty placeholders: "
            f"{layout_not_in_mapping}",
            category=UserWarning,
            stacklevel=2,
        )