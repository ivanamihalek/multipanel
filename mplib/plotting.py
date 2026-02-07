"""Plotting utilities for building a subplot_mosaic figure from the spec."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Tuple

import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

from mplib.config import PlotSpec
from mplib.io_utils import load_sheet_dataframe


def _label_panel(ax: plt.Axes, panel_id: str, ) -> None:
    """Adds a panel label in the upper-left corner of the axes."""
    ax.text(
        0.0,
        1.1,  # slightly above axes
        panel_id,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize="large",
        fontweight="bold",
        clip_on=False,  # allow drawing outside axes
    )

def _plot_default_xy(ax: plt.Axes, df: pd.DataFrame, title: str, ) -> None:
    """Default plotting routine for a sheet.

    Expects columns: x, y

    Args:
      ax: Target axes.
      df: Sheet DataFrame.
      title: Panel title (e.g., sheet name).
    """
    if "x" not in df.columns or "y" not in df.columns:
        raise ValueError("Sheet is missing required columns for default plot: x, y. "
                         f"Found columns: {list(df.columns)}")

    ax.plot(df["x"], df["y"], linewidth=2.0, )
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)


def _populate_legend_panel(ax: plt.Axes, ) -> None:
    """Populates the special '0' panel."""
    ax.set_axis_off()
    ax.text(0.5, 0.5, "LEGEND", transform=ax.transAxes, ha="center", va="center", fontsize="x-large", fontweight="bold", )


def build_figure_from_spec(xlsx_path: Path, spec: PlotSpec, ) -> matplotlib.figure.Figure:
    """Builds the matplotlib Figure based on the YAML spec.

    Args:
      xlsx_path: Path to the XLSX workbook.
      spec: Plot specification.

    Returns:
      The created Figure.
    """
    fig = plt.figure(figsize=(10, 6), constrained_layout=True, )
    mosaic = "\n".join(spec.layout_rows)
    axes_dict: Dict[str, plt.Axes] = fig.subplot_mosaic(mosaic)

    # Placeholders: any panel in axes_dict not driven by a sheet mapping
    # should still be labeled (except '0'), but left empty.
    mapped_panels = set(spec.sheet2panel.values())

    for panel_id, ax in axes_dict.items():
        if panel_id == "0":
            _populate_legend_panel(ax=ax, )
            continue

        # Label panel regardless of whether it is mapped, per requirements.
        _label_panel(ax=ax, panel_id=panel_id, )

        if panel_id not in mapped_panels:
            # Placeholder: leave empty (no data plotted).
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("")
            continue

    # Plot each mapped sheet into its assigned panel.
    for sheet_name, panel_id in spec.sheet2panel.items():
        ax = axes_dict[panel_id]
        df = load_sheet_dataframe(xlsx_path=xlsx_path, sheet_name=sheet_name, )
        _plot_default_xy(ax=ax, df=df, title=sheet_name, )

    return fig


def save_figure_svg(fig: matplotlib.figure.Figure, out_path: Path, ) -> None:
    """Saves the figure to SVG."""
    out_path.parent.mkdir(parents=True, exist_ok=True, )
    fig.savefig(out_path, format="svg", )
