#! /usr/bin/env python3
from dataclasses import dataclass
from typing import Tuple

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from pathlib import Path
from itertools import combinations
from matplotlib.font_manager import FontProperties

def generate_test_values(number_of_avgs):
    np.random.seed(42)
    list_of_avgs = np.random.uniform(5, 15, number_of_avgs).tolist()
    # Generate test p-values for some pairs (not all combinations)
    p_values = {}
    # Adjacent comparisons
    for i, j in combinations(range(number_of_avgs), 2):
        p_values[(i, j)] = np.random.choice([0.00005, 0.0005, 0.005, 0.03, 0.1])

    return list_of_avgs, p_values

def get_significance_symbol(p_value: float) -> str:
    if p_value <= 0.0001:
        return "****"
    elif p_value <= 0.001:
        return "***"
    elif p_value <= 0.01:
        return "**"
    elif p_value <= 0.05:
        return "*"
    else:
        return "-"

@dataclass(frozen=True)
class AsteriskBarDimensions:
    asterisk_fontsize: float
    asterisk_height_in_data_units: float
    tip_length_in_data_units: float
    dash_width_in_data_units: float
    top_y_in_data_units: float



def get_axis_to_font_ratio(fig: plt.Figure, ax: plt.Axes) -> Tuple[float, float, float, float]:
    """
    Compute the ratio of axis dimensions (width, height) in pixels
    to the dimensions of the y-axis tick label font (in pixels).

    Returns:
        dict with ratios and intermediate measurements
    """

    # ----------------------------------------------------------
    # STEP 1: Get the axis bounding box in display (pixel) units
    # ----------------------------------------------------------
    # We must call draw() first so that all layout info is resolved
    fig.canvas.draw()

    bbox = ax.get_window_extent()          # in display pixels
    ax_width_px  = bbox.width
    ax_height_px = bbox.height

    # ----------------------------------------------------------
    # STEP 2: Get the y-axis tick label font size in *points*
    # ----------------------------------------------------------
    # Font size in points (pt) is a measurement of the total vertical height of the font's bounding box
    # —originally the metal body, now the "em square"
    ytick_labels = ax.get_yticklabels()
    if ytick_labels:
        font_size_pt = ytick_labels[0].get_fontsize()   # in points
    else:
        font_size_pt = mpl.rcParams['ytick.labelsize']
        if isinstance(font_size_pt, str):                # e.g. 'medium'
            font_size_pt = mpl.font_manager.font_scalings.get(
                font_size_pt, 1.0) * mpl.rcParams['font.size']

    # ----------------------------------------------------------
    # STEP 3: Convert font size from points → pixels
    # ----------------------------------------------------------
    dpi = fig.dpi
    font_height_px = font_size_pt * dpi / 72.0   # 1 point = 1/72 inch

    return font_size_pt, font_height_px, ax_width_px  / font_height_px,  ax_height_px / font_height_px


def asterisk_bar_geometry(fig: plt.Figure, ax: plt.Axes,  sig_pairs) -> AsteriskBarDimensions:
    # Get figure dimensions
    # Points are absolute, print-based units (1/72th of an inch)
    # number of pixels per point depends on the device resolution
    # The native figure size unit in Matplotlib is inches, deriving from print industry standards.
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/figure_size_units.html
    # The font sizes, however, are specified in points (pt), a standard unit in typography

    # don't touch the numbers hardcoded here - they
    # accomplish what is needed visually
    # Get y-axis tick label font size in points

    # 'fu' means font units (font height)
    font_size_pt, font_height_px, ax_width_fu, ax_height_fu = get_axis_to_font_ratio(fig, ax)

    # for each sig pair we want to show the asterisk bar
    # let's say for now it will be 2 font units high
    n_sig_pairs = len(sig_pairs)

    # y in data units
    y_limits_current = ax.get_ylim() # \The current y-axis limits in data coordinates.
    y_range_current = y_limits_current[1] - y_limits_current[0]
    y_range_new = y_range_current*(ax_height_fu/(ax_height_fu - n_sig_pairs*2*font_height_px))
    top_y_in_data_units = y_limits_current[0] + y_range_new

    font_height_in_data_units = (y_range_new - y_range_current)/(n_sig_pairs*2)
    # prong, or teine or tip at the end of asterisk bar
    tip_length_in_data_units = font_height_in_data_units / 3

    # the glyph itself is 1/3 of the fontsize
    asterisk_height_in_data_units = font_height_in_data_units * 1.2 / 3
    x_limits_current = ax.get_xlim()
    dash_width_in_data_units = (x_limits_current[1] - x_limits_current[0]) / 20


    geom = AsteriskBarDimensions(asterisk_fontsize= font_size_pt,
                                 asterisk_height_in_data_units=asterisk_height_in_data_units,
                                 tip_length_in_data_units=tip_length_in_data_units,
                                 dash_width_in_data_units=dash_width_in_data_units,
                                 top_y_in_data_units=top_y_in_data_units)

    return geom


def draw_asterisk_bars(fig: plt.Figure, ax: plt.Axes, list_of_heights, p_values):
    """

    Args:
        fig:
        ax:
        list_of_heights:  the height that the significance annotation should sit above
        p_values: dictionary of p values with tuple (i, j) as the key

    Returns:
        None
    """

    # Sort pairs by their span (distance between bars) to layer them properly
    sorted_pairs = sorted(p_values.keys(), key=lambda pair: abs(pair[1] - pair[0]))

    g: AsteriskBarDimensions = asterisk_bar_geometry(fig, ax, p_values)

    n_bars = len(list_of_heights)
    x_positions = np.arange(n_bars)

    max_height = max(list_of_heights)
    lowest_asterisk_line_y = max_height + g.tip_length_in_data_units

    for pair_idx, (i, j) in enumerate(sorted_pairs):

        p_value = p_values[(i, j)]
        sig_symbol = get_significance_symbol(p_value)

        # Determine the height for this annotation
        # It should be above the tallest element in the span

        y_line = lowest_asterisk_line_y + pair_idx * 2 * g.asterisk_height_in_data_units

        x1, x2 = x_positions[i], x_positions[j]

        # Draw horizontal line
        ax.plot([x1, x2], [y_line, y_line], color='black', linewidth=1)

        # Draw vertical lines at ends (1/2 the height of asterisk)
        for x in [x1, x2]:
            ax.plot([x, x], [y_line, y_line - g.tip_length_in_data_units], color='black', linewidth=1)

        # Add significance symbol
        x_mid = (x1 + x2) / 2
        y_text = y_line  - g.asterisk_height_in_data_units * 0.5  # Small offset above the line

        if sig_symbol == "-":
            # Position: 1/3 of asterisk height above the horizontal significance line
            dash_y = y_line +  g.asterisk_height_in_data_units * 0.5
            # Draw the dash line
            ax.plot([x_mid - g.dash_width_in_data_units/2, x_mid + g.dash_width_in_data_units/2],  [dash_y, dash_y],
                   color='black', linewidth=2, solid_capstyle='butt')
        else:
            ax.text(x_mid, y_text, sig_symbol, ha='center', va='bottom', fontsize=g.asterisk_fontsize)


    # Adjust y-axis limit to accommodate annotations
    current_ylim = ax.get_ylim()
    ax.set_ylim(current_ylim[0], g.top_y_in_data_units)


def barplot_w_sig_annotation(fig: plt.Figure, ax: plt.Axes, list_of_avgs, p_values):
    """
    Create a barplot with significance annotations.

    Args:
        list_of_avgs: List of average values to plot as bars
        p_values: Dictionary with keys as tuples (i, j) representing pairs of bars,
                  and values as p-values for those pairs
    """

    n_bars = len(list_of_avgs)
    x_positions = np.arange(n_bars)

    # Create the bar plot
    bars = ax.bar(x_positions, list_of_avgs, color='steelblue', alpha=0.7, edgecolor='black')

    # Set labels
    ax.set_ylabel('Average Value')
    ax.set_xlabel('attributes')
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f'attribute {i + 1}' for i in range(n_bars)])

    draw_asterisk_bars(fig, ax, list_of_avgs, p_values)

    plt.tight_layout()
    return fig, ax

def main():
    plt.style.use("multi.mplstyle")

    number_of_avgs = 5

    list_of_avgs, p_values = generate_test_values(number_of_avgs)

    fig, ax = plt.subplots(figsize=(12, 8))

    barplot_w_sig_annotation(fig, ax, list_of_avgs, p_values)
    plt.savefig('significance_barplot.png', dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    main()
