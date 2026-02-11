#!/usr/bin/env python3
"""Plotting utilities for populating mosaic panels with data."""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes


def plot_panel_content(ax: Axes, df: pd.DataFrame, plot_type: str, panel_label: str) -> None:
    """Render plot content into a specific axis based on data type."""
    ax.set_title(f"Panel {panel_label}: {plot_type.capitalize()} Plot")

    if plot_type == 'line':
        if df.shape[1] >= 2:
            x, y = df.iloc[:, 0], df.iloc[:, 1]
        else:
            x, y = np.arange(len(df)), df.iloc[:, 0]
        ax.plot(x, y)
        ax.set_ylabel("Amplitude")

    elif plot_type == 'scatter':
        if df.shape[1] >= 2:
            x, y = df.iloc[:, 0], df.iloc[:, 1]
        else:
            x, y = np.arange(len(df)), df.iloc[:, 0]
        ax.scatter(x, y, alpha=0.6, c='darkblue')
        ax.set_ylabel("Observations")

    elif plot_type == 'histogram':
        data = df.iloc[:, 0].dropna()
        ax.hist(data, bins=20, alpha=0.7, color='purple')
        ax.set_ylabel("Frequency")

    elif plot_type == 'heatmap':
        im = ax.imshow(df.values, cmap='viridis', aspect='auto')
        ax.set_ylabel("Y-Index")

    ax.set_xlabel(f"X-Axis Data ({panel_label})")
    ax.grid(True, alpha=0.3)


def plot_dummy_fallback(ax: Axes, panel_label: str) -> None:
    """Generate placeholder content when no Excel data is mapped to a panel."""
    x = np.linspace(0, 10, 50)
    ax.plot(x, np.sin(x), 'k--', alpha=0.3)
    ax.set_title(f"Panel {panel_label}: (No Data)")
    ax.set_xlabel("X-Axis")
    ax.set_ylabel("Y-Axis")
    ax.grid(True, alpha=0.3)
