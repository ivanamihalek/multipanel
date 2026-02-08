"""Plotting utilities for building a subplot_mosaic figure from the spec."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.figure
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

from mplib.config import PlotSpec
from mplib.io_utils import load_sheet_dataframe


# multipanel/plotting.py

def _make_inner_plot_axes(
    fig: plt.Figure,
    container_ax: plt.Axes,
    margin_figwidth_frac: float = 0.07,
) -> plt.Axes:
    """Creates an inner axes leaving margins sized as a fraction of figure width.

    The margin length is defined as margin_figwidth_frac * (figure width),
    and applied to:
      - left margin (x direction)
      - top margin (y direction), using the same physical length as the x margin

    Args:
      fig: Matplotlib Figure.
      container_ax: The mosaic axes used as a container.
      margin_figwidth_frac: Margin length as a fraction of total figure width.

    Returns:
      Inset axes for actual plotting.
    """
    if margin_figwidth_frac < 0.0:
        raise ValueError("margin_figwidth_frac must be >= 0")

    # Container position in figure-fraction coordinates.
    pos = container_ax.get_position()  # Bbox: x0,y0,width,height in fig-fraction

    # Convert a margin defined as fraction of *figure width* into figure-fraction
    # offsets in x and y that represent the same physical length. (inches, no other units available)
    fig_width_inches, fig_height_inches = fig.get_size_inches()
    margin_inches = margin_figwidth_frac * fig_width_inches

    # Get the normalized position of the container_ax in figure coordinates
    bbox = container_ax.get_position()

    # Compute physical sizes of the container_ax
    container_phys_width_inches  = bbox.width * fig_width_inches
    container_phys_height_inches = bbox.height * fig_height_inches

    # Normalized fractions for the inset relative to container_ax
    left_frac = margin_inches / container_phys_width_inches
    top_margin_frac = margin_inches / container_phys_height_inches
    width_frac = 1.0 - left_frac
    height_frac = 1.0 - top_margin_frac

    # Create the inner axes with bottom-left origin relative to container_ax
    inner_ax = container_ax.inset_axes( (left_frac, 0.0, width_frac, height_frac))
    return inner_ax

def _label_panel_in_container(container_ax: plt.Axes, panel_id: str, pad_px: float = 2.0, ) -> None:
    """Places panel label at top-left of the *panel container* with pixel padding."""
    container_ax.annotate(panel_id, xy=(0.0, 1.0), xycoords="axes fraction", xytext=(pad_px, -pad_px),
        # a couple of pixels inset from top-left corner
        textcoords="offset points", ha="left", va="top", fontweight="bold", # fontsize="large",
                          bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.20",
            # small padding around label text
            alpha=0.9, ), zorder=10, )


def _populate_legend_panel(container_ax: plt.Axes, ) -> None:
    """Populates the special '0' panel."""
    container_ax.set_axis_off()
    container_ax.text(0.5, 0.5, "LEGEND", transform=container_ax.transAxes,
                      ha="center", va="center", fontsize="x-large", fontweight="bold", )


def _plot_default_xy(ax: plt.Axes, df: pd.DataFrame, title: str | None) -> None:
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
    if title is not None: ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")


def build_figure_from_spec(xlsx_path: Path, spec: PlotSpec, ) -> matplotlib.figure.Figure:
    """Builds the matplotlib Figure based on the YAML spec."""
    # we expect that the main styling options were already applier though mplstyle, for example
    fig = plt.figure()

    # IMPORTANT: pass a multiline string (avoids the 1D-list issue).
    mosaic = "\n".join(spec.layout_rows)
    container_axes: Dict[str, plt.Axes] = fig.subplot_mosaic(mosaic, )

    mapped_panels = set(spec.sheet2panel.values())

    # Create inner plotting axes for panels that will contain data.
    plot_axes: Dict[str, plt.Axes] = {}

    for panel_id, container_ax in container_axes.items():
        # Container axes is only for label/legend; hide its frame/ticks.
        container_ax.set_axis_off()

        if panel_id == "0":
            _populate_legend_panel(container_ax=container_ax, )
            continue

        # Always label non-'0' panels (including placeholders).
        _label_panel_in_container(container_ax=container_ax, panel_id=panel_id, pad_px=2.0, )

        if panel_id not in mapped_panels:
            # Placeholder: leave empty.
            continue

        # Create inset axes to leave the requested top/left margins.
        inner_ax = _make_inner_plot_axes(fig=fig,  container_ax=container_ax,  margin_figwidth_frac=0.05)
        plot_axes[panel_id] = inner_ax

    # Plot each mapped sheet into its assigned inner axes.
    for sheet_name, panel_id in spec.sheet2panel.items():
        df = load_sheet_dataframe(xlsx_path=xlsx_path, sheet_name=sheet_name, )
        ax = plot_axes[panel_id]
        # title = sheet_name
        title = None
        _plot_default_xy(ax=ax, df=df, title=title)

    return fig


def save_figure_svg(fig: matplotlib.figure.Figure, out_path: Path, ) -> None:
    """Saves the figure to SVG."""
    out_path.parent.mkdir(parents=True, exist_ok=True, )
    fig.savefig(out_path, format="svg", )
