"""Data models for YAML plot specifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PlotSpec:
    """Parsed YAML plot specification.

    Attributes:
      sheet2panel: Mapping from Excel sheet name to a single-character panel id.
      layout_rows: Row strings for subplot_mosaic, e.g. ["IIJJ", "KKKK", "0000"].
    """

    sheet2panel: Mapping[str, str]
    layout_rows: Sequence[str]
