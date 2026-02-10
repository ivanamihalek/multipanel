from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

from .config import Config
from .layout import compute_panel_boxes, layout_shape, validate_panel_ids


def _margin_y_in_figcoords(margin_x_frac: float, fig_w_in: float, fig_h_in: float) -> float:
    """Convert a margin specified as fraction of figure width into normalized figure y-units."""
    return margin_x_frac * (fig_w_in / fig_h_in)


def _read_sheet_df(xlsx_path: Path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(xlsx_path, sheet_name=sheet_name)


def _plot_dataframe(ax: plt.Axes, df: pd.DataFrame, sheet_name: str) -> None:
    """
    Simple plotting rule for testing:
    - If columns x and y exist, plot y vs x.
    - Else, plot first two numeric columns if available.
    - Else, plot the first column vs index.
    """
    ax.grid(True, alpha=0.3)

    if "x" in df.columns and "y" in df.columns:
        ax.plot(df["x"], df["y"], marker="o", linewidth=1.5)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        return

    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(num_cols) >= 2:
        xcol, ycol = num_cols[0], num_cols[1]
        ax.plot(df[xcol], df[ycol], marker="o", linewidth=1.5)
        ax.set_xlabel(str(xcol))
        ax.set_ylabel(str(ycol))
        return

    if len(df.columns) >= 1:
        col = df.columns[0]
        ax.plot(df.index, df[col], marker="o", linewidth=1.5)
        ax.set_xlabel("index")
        ax.set_ylabel(str(col))
        return

    ax.text(0.5, 0.5, f"No data in sheet '{sheet_name}'", ha="center", va="center", transform=ax.transAxes)


def _add_panel_label(fig: matplotlib.figure.Figure, panel_id: str, x: float, y: float) -> None:
    """Place the panel label outside the panel rectangle in figure coordinates."""
    fig.text(x, y, panel_id, ha="left", va="top", transform=fig.transFigure, clip_on=False)

def _add_placeholder(ax: plt.Axes, panel_id: str) -> None:
    ax.set_axis_off()
    ax.text(0.5, 0.5, f"({panel_id})", ha="center", va="center", transform=ax.transAxes)


def _add_legend_panel(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.text(0.5, 0.5, "LEGEND", ha="center", va="center", transform=ax.transAxes)


def build_figure(cfg: Config) -> matplotlib.figure.Figure:
    """
    Construct the figure with a mosaic-like GridSpec layout, per-panel fixed margins (figure-width-based),
    and label placement in the margin area (left & above the plotting axes).
    """
    layout_ids, mapped_ids, unmapped_layout_ids = validate_panel_ids(cfg.layout_rows, cfg.sheet2panel)

    extra_mapped = mapped_ids - layout_ids
    if extra_mapped:
        raise ValueError(f"sheet2panel maps to panel IDs not present in layout: {sorted(extra_mapped)}")

    if unmapped_layout_ids:
        warnings.warn(f"Panels present in layout but not in sheet2panel will be placeholders: "
                      f"{sorted(unmapped_layout_ids)}", stacklevel=2)

    boxes = compute_panel_boxes(cfg.layout_rows)
    nrows, ncols = layout_shape(cfg.layout_rows)

    fig = plt.figure(figsize=cfg.figsize)
    gs = fig.add_gridspec(nrows=nrows, ncols=ncols, wspace=0.0, hspace=0.0)

    fig_w, fig_h = cfg.figsize
    ml = float(cfg.margins.left)
    mr = float(cfg.margins.right)
    mt = _margin_y_in_figcoords(float(cfg.margins.top), fig_w, fig_h)
    mb = _margin_y_in_figcoords(float(cfg.margins.bottom), fig_w, fig_h)

    panel2sheet = {panel: sheet for sheet, panel in cfg.sheet2panel.items()}

    for panel_id, box in boxes.items():
        sub = gs[box.r0:box.r1 + 1, box.c0:box.c1 + 1]
        bbox = sub.get_position(fig)  # figure-relative coordinates

        main_x0 = bbox.x0 + ml
        main_x1 = bbox.x1 - mr
        main_y0 = bbox.y0 + mb
        main_y1 = bbox.y1 - mt

        if main_x1 <= main_x0 or main_y1 <= main_y0:
            raise ValueError(f"Margins too large for panel '{panel_id}' area; reduce margins or increase figsize/layout size.")

        main_ax = fig.add_axes((main_x0, main_y0, main_x1 - main_x0, main_y1 - main_y0))

        if panel_id == "0":
            _add_legend_panel(main_ax)
            continue

        label_x = bbox.x0 - ml
        label_y = bbox.y1 + mt
        _add_panel_label(fig, panel_id, label_x, label_y)

        if panel_id in panel2sheet:
            sheet = panel2sheet[panel_id]
            df = _read_sheet_df(cfg.xlsx_path, sheet)
            _plot_dataframe(main_ax, df, sheet)
        else:
            _add_placeholder(main_ax, panel_id)

    return fig
