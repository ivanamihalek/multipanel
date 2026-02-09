from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Union, Any, Optional

import pandas as pd


def place_single_label(ax: plt.Axes, label: str, renderer: Any, offset_pixels: float) -> None:
    """
    Calculates coordinates and places a single panel label.
    Adapts logic based on whether the panel has content (y-label visible) or is empty (axis off).
    """
    # Get the bounding box of the subplot axes (the graph area)
    # Even if axis is 'off', this returns the allocated area in the mosaic
    ax_bbox = ax.get_window_extent(renderer)

    # Determine the reference X coordinate (the anchor point)
    # If axis is ON and has a label, anchor to the left of the Y-label.
    # If axis is OFF (empty placeholder), anchor to the left of the allocated axis area (x0).
    if ax.axison and ax.yaxis.label.get_text():
        ylabel_bbox = ax.yaxis.label.get_window_extent(renderer)
        reference_x_pixel = ylabel_bbox.x0
    else:
        reference_x_pixel = ax_bbox.x0

    # Calculate target position in display pixels
    # X: Reference point minus the offset
    target_x_pixel = reference_x_pixel - offset_pixels

    # Y: Top edge of the axis (graph) plus the offset
    target_y_pixel = ax_bbox.y1 + offset_pixels

    # Convert display pixels back to Axes coordinates
    # This ensures the text is attached to this specific subplot
    inv_transform = ax.transAxes.inverted()
    axes_coords = inv_transform.transform((target_x_pixel, target_y_pixel))

    # Place the text
    ax.text(
        axes_coords[0],
        axes_coords[1], label, transform=ax.transAxes, fontsize=16, fontweight='bold', va='bottom', ha='right')


def add_aligned_panel_labels(fig: plt.Figure, axes_dict: Dict[
    str, plt.Axes], n_cols: int, width_fraction: float) -> None:
    """
    Iterates through all axes and applies the label placement logic.
    """
    # Force a draw so renderer has final bounding boxes for calculations
    fig.canvas.draw()

    renderer = fig.canvas.get_renderer()

    # Calculate offset in pixels based on figure width fraction
    fig_width_pixels = fig.get_window_extent(renderer).width
    offset_pixels = (width_fraction * fig_width_pixels) / n_cols

    for label, ax in axes_dict.items():
        place_single_label(ax, label, renderer, offset_pixels)


def create_mosaic_figure(layout: List[List[str]], data_map: Dict[str, pd.DataFrame],
                         x_label: str = "Time (s)", y_label: str = "Amplitude") -> None:
    """
    Generates the mosaic figure. Handles empty panels by checking data_map keys.
    """
    fig, axd = plt.subplot_mosaic(layout, figsize=(10, 5), constrained_layout=True)

    for key, ax in axd.items():
        if key in data_map:
            # Panel has data: Plot it
            ax.plot(data_map[key]['x'], data_map[key]['y'])
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', alpha=0.6)
        else:
            # Panel has no data: Make it a completely empty placeholder
            # 'axis("off")' hides spines, ticks, and labels, but keeps the space reserved
            ax.axis('off')

    n_columns = len(layout[0])

    # Apply labels with offset calculated as fraction of width
    add_aligned_panel_labels(fig, axd, n_cols=n_columns, width_fraction=0.04)

    plt.show()
