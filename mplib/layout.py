
"""Layout engine for calculating label metrics and adjusting panel geometry."""

import sys
from typing import Dict, List, Tuple

from matplotlib.axes import Axes
from matplotlib.figure import Figure


def calculate_max_label_metrics(fig: Figure, labels: List[str], fontsize: int) -> Tuple[float, float]:
    """Calculate the width/height of the widest/tallest label in Figure coordinates."""
    renderer = fig.canvas.get_renderer()
    max_width = 0.0
    max_height = 0.0

    for label in labels:
        temp_text = fig.text(0, 0, label, fontsize=fontsize, fontweight='bold')
        bbox = temp_text.get_window_extent(renderer=renderer)
        bbox_fig = bbox.transformed(fig.transFigure.inverted())
        max_width = max(max_width, bbox_fig.width)
        max_height = max(max_height, bbox_fig.height)
        temp_text.remove()

    return max_width, max_height


def add_panel_label(fig: Figure, ax: Axes, label: str, fontsize: int, padding_factor: float,
                    fixed_label_width: float, fixed_label_height: float) -> None:
    """Adjust axis position to create a gutter for the panel label."""
    renderer = fig.canvas.get_renderer()
    base_pos = ax.get_position()
    base_x0, base_y0 = base_pos.x0, base_pos.y0
    base_x1, base_y1 = base_pos.x1, base_pos.y1

    fig_width, fig_height = fig.get_size_inches()
    padding_inches = (fontsize / 72) * padding_factor
    x_padding_fig = padding_inches / fig_width
    y_padding_fig = padding_inches / fig_height

    ylabel = ax.yaxis.label
    ylabel_bbox = ylabel.get_window_extent(renderer=renderer)
    ylabel_bbox_fig = ylabel_bbox.transformed(fig.transFigure.inverted())
    ylabel_width = ylabel_bbox_fig.width if ylabel.get_text() else 0.0

    max_tick_width = 0.0
    for tl in ax.get_yticklabels():
        if tl.get_text():
            tl_bbox = tl.get_window_extent(renderer=renderer)
            tl_bbox_fig = tl_bbox.transformed(fig.transFigure.inverted())
            max_tick_width = max(max_tick_width, tl_bbox_fig.width)

    title = ax.title
    title_bbox = title.get_window_extent(renderer=renderer)
    title_bbox_fig = title_bbox.transformed(fig.transFigure.inverted())
    title_height = title_bbox_fig.height if title.get_text() else 0.0

    gap = x_padding_fig / 2.0
    required_left_inset = (x_padding_fig + fixed_label_width + gap + ylabel_width + gap + max_tick_width + gap)
    required_top_inset = (y_padding_fig + fixed_label_height + y_padding_fig + title_height)

    new_left = base_x0 + required_left_inset
    new_top = base_y1 - required_top_inset
    new_width = base_x1 - new_left
    new_height = new_top - base_y0

    if new_width <= 0 or new_height <= 0:
        print(f"Warning: Panel {label} is too small for the requested font/layout.", file=sys.stderr)
        return

    ax.set_position((new_left, base_y0, new_width, new_height))

    final_x = base_x0 + x_padding_fig
    final_y = base_y1 - y_padding_fig - fixed_label_height

    fig.text(final_x, final_y, label, fontsize=fontsize, fontweight='bold', ha='left', va='bottom',
             transform=fig.transFigure)
