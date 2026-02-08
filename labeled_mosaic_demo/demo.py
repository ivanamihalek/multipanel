#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Union, Any

def _add_label(ax, label, renderer, offset_pixels):
    # Get the bounding box of the Y-axis label (to find its left edge)
    ylabel_bbox = ax.yaxis.label.get_window_extent(renderer)

    # Get the bounding box of the subplot axes (to find its top edge)
    ax_bbox = ax.get_window_extent(renderer)

    # Calculate target position in display pixels
    # X: Left edge of the y-label minus the offset
    target_x_pixel = ylabel_bbox.x0 - offset_pixels

    # Y: Top edge of the axis (graph) plus the offset
    target_y_pixel = ax_bbox.y1 + offset_pixels

    # Convert these pixel coordinates back to Axes coordinates (0,0 to 1,1) for this specific ax
    # This allows the text to remain anchored to the axis if resized later (to some extent)
    inv_transform = ax.transAxes.inverted()
    axes_coords = inv_transform.transform((target_x_pixel, target_y_pixel))

    # Place the text using the calculated axes coordinates
    # ha='right' ensures the text ends at the calculated point, staying fully clear of the label
    ax.text( axes_coords[0], axes_coords[1], label, transform=ax.transAxes,
             fontsize=32, fontweight='bold', va='bottom', ha='right')


def add_aligned_panel_labels(fig: plt.Figure, axes_dict: Dict[
    str, plt.Axes], n_cols: int, width_fraction: float = 0.05) -> None:
    """
    Places panel labels (A, B) relative to the y-axis label and graph top.
    X Position: To the left of the Y-axis label's bounding box.
    Y Position: Above the top spine of the axes.
    Offsets are calculated as a fraction of the figure width distributed by column count.
    """
    # Trigger a draw to ensure the layout engine (constrained_layout) has finalized positions
    fig.canvas.draw()

    # Get the renderer to calculate text bounding boxes
    renderer = fig.canvas.get_renderer()

    # Calculate the dynamic pixel offset based on figure width
    fig_width_pixels = fig.get_window_extent(renderer).width
    offset_pixels = (width_fraction * fig_width_pixels) / n_cols

    for label, ax in axes_dict.items():
        _add_label(ax, label, renderer, offset_pixels)


def create_mosaic_figure(layout: List[List[str]], data_map: Dict[
    str, np.ndarray], x_label: str = "Time (s)", y_label: str = "Amplitude") -> None:
    """
    Generates the mosaic figure and applies the alignment fix.
    """
    fig, axd = plt.subplot_mosaic(
        layout,
        figsize=(12, 6),
        constrained_layout=True,
        gridspec_kw={'wspace': 0.1, 'hspace': 0.3}
    )

    for key, ax in axd.items():
        if key in data_map:
            ax.plot(data_map[key]['x'], data_map[key]['y'])
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label, fontsize=30)
            ax.grid(True, linestyle='--', alpha=0.6)

    # Determine number of columns for the offset calculation
    n_columns = len(layout[0])

    # Apply the geometrically aligned labels
    add_aligned_panel_labels(fig, axd, n_cols=n_columns, width_fraction=0.025)

    plt.show()


def main() -> None:
    # Sample Input
    x = np.linspace(0, 10, 100)
    data = {'A': {'x': x, 'y': np.sin(x)}, 'B': {'x': x, 'y': np.cos(x) * np.exp(-x / 5)}}

    # Define Layout
    layout_structure = [['A', 'B']]

    print(f"Generating aligned mosaic plot with layout: {layout_structure}")
    create_mosaic_figure(layout_structure, data)


if __name__ == "__main__":
    main()