#!/usr/bin/env python3
"""Plotting utilities for populating mosaic panels with data."""
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Callable, Dict
from .bar_w_stats import bar_plot_w_stats  # Add import at top of file

def _plot_line(fig: Figure, ax: Axes, df: pd.DataFrame, panel_label: str) -> None:
    """Render line plot."""
    x, y = (df.iloc[:, 0], df.iloc[:, 1]) if df.shape[1] >= 2 else (np.arange(len(df)), df.iloc[:, 0])
    ax.plot(x, y)
    ax.set_ylabel("Amplitude")
    ax.set_xlabel(f"X-Axis Data ({panel_label})")
    ax.grid(False, alpha=0.3)


def _plot_scatter(fig: Figure, ax: Axes, df: pd.DataFrame, panel_label: str) -> None:
    """Render scatter plot."""
    x, y = (df.iloc[:, 0], df.iloc[:, 1]) if df.shape[1] >= 2 else (np.arange(len(df)), df.iloc[:, 0])
    ax.scatter(x, y, alpha=0.6, c='darkblue')
    ax.set_ylabel("Observations")
    ax.set_xlabel(f"X-Axis Data ({panel_label})")
    ax.grid(False, alpha=0.3)


def _plot_histogram(fig: Figure, ax: Axes, df: pd.DataFrame, panel_label: str) -> None:
    """Render histogram."""
    data = df.iloc[:, 0].dropna()
    ax.hist(data, bins=20, alpha=0.7, color='purple')
    ax.set_ylabel("Frequency")
    ax.set_xlabel(f"X-Axis Data ({panel_label})")
    ax.grid(False, alpha=0.3)


def _plot_heatmap(fig: Figure, ax: Axes, df: pd.DataFrame, panel_label: str) -> None:
    """Render heatmap."""
    # TODO - y-label overlpa the gutter, assorted AIs (Feb 2026) cannot find the fix
    ax.imshow(df.values, cmap='viridis', aspect='auto')
    ax.set_ylabel("Y-Index")

def _plot_bar(fig: Figure, ax: Axes, df: pd.DataFrame,  panel_label: str):
    bar_plot_w_stats(fig, ax, df, panel_label)

# Factory mapping
plot_factory: Dict[str, Callable[[Figure, Axes, pd.DataFrame, str], None]] = {
    'line': _plot_line,
    'scatter': _plot_scatter,
    'histogram': _plot_histogram,
    'heatmap': _plot_heatmap,
    'bar': _plot_bar,  # Add new entry
}


def plot_panel_content(fig,  ax: Axes, df: pd.DataFrame, plot_type: str, panel_label: str) -> None:
    """Render plot content into a specific axis based on data type."""

    plot_func = plot_factory.get(plot_type)
    if plot_func is None:
        raise ValueError(f"Unknown plot type: {plot_type}")

    plot_func(ax, df, panel_label)


def plot_legend(ax: Axes) -> None:
    """Generate placeholder content when no Excel data is mapped to a panel."""
    ax.set_axis_off()
    ax.text(0.5, 0.5, "legend\nhere", transform=ax.transAxes,
                      ha="center", va="center")

def plot_dummy_fallback(ax: Axes) -> None:
    """Generate placeholder content when no Excel data is mapped to a panel."""
    ax.set_axis_off()
    ax.text(0.5, 0.5, "data\nnot found", transform=ax.transAxes,
                      ha="center", va="center")
