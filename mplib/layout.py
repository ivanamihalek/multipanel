from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PanelBox:
    """Inclusive row/col bounds in the layout grid."""
    r0: int
    r1: int
    c0: int
    c1: int


def layout_shape(layout_rows: list[str]) -> tuple[int, int]:
    nrows = len(layout_rows)
    ncols = len(layout_rows[0])
    if any(len(r) != ncols for r in layout_rows):
        raise ValueError("All layout rows must have the same length.")
    return nrows, ncols


def panel_ids_from_layout(layout_rows: list[str]) -> set[str]:
    return set("".join(layout_rows))


def compute_panel_boxes(layout_rows: list[str]) -> dict[str, PanelBox]:
    """
    Compute bounding rectangles for each panel ID and ensure each panel is a filled rectangle
    (mosaic-like constraint).
    """
    nrows, ncols = layout_shape(layout_rows)
    ids = panel_ids_from_layout(layout_rows)

    positions: dict[str, list[tuple[int, int]]] = {pid: [] for pid in ids}
    for r in range(nrows):
        for c in range(ncols):
            positions[layout_rows[r][c]].append((r, c))

    boxes: dict[str, PanelBox] = {}
    for pid, pos in positions.items():
        rs = [p[0] for p in pos]
        cs = [p[1] for p in pos]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)

        # Ensure panel occupies a full rectangle (no holes, no discontiguous shapes).
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                if layout_rows[rr][cc] != pid:
                    raise ValueError(f"Panel '{pid}' is not a solid rectangle in layout (hole/discontiguity at {rr},{cc}).")

        boxes[pid] = PanelBox(r0=r0, r1=r1, c0=c0, c1=c1)

    return boxes


def validate_panel_ids(layout_rows: list[str], sheet2panel: dict[str, str]) -> tuple[set[str], set[str], set[str]]:
    """
    Returns (layout_ids, mapped_ids, unmapped_layout_ids).

    Rules:
    - If mapped_ids contains IDs not in layout_ids => error (handled by caller).
    - If layout has extra IDs not in mapped_ids (except '0') => warning + placeholders.
    """
    layout_ids = panel_ids_from_layout(layout_rows)
    mapped_ids = set(sheet2panel.values())
    unmapped_layout_ids = {pid for pid in layout_ids if pid not in mapped_ids and pid != "0"}
    return layout_ids, mapped_ids, unmapped_layout_ids


def iter_unique_panels_in_layout(layout_rows: list[str]) -> Iterable[str]:
    """Deterministic order: first appearance scan."""
    seen: set[str] = set()
    for row in layout_rows:
        for ch in row:
            if ch not in seen:
                seen.add(ch)
                yield ch
