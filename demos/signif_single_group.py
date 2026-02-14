#! /usr/bin/env python3
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from itertools import combinations

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

def asterisk_bar_geometry(fig: plt.Figure, ax: plt.Axes, list_of_heights) -> AsteriskBarDimensions:
    # Get figure dimensions
    # Points are absolute, print-based units (1/72th of an inch)
    # number of pixels per point depends on the device resolution
    # The native figure size unit in Matplotlib is inches, deriving from print industry standards.
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/figure_size_units.html
    # The font sizes, however, are specified in points (pt), a standard unit in typography

    # don't touch the numbers hardcoded here - they
    # accomplish what is needed visually
    # Get y-axis tick label font size in points
    y_tick_labels = ax.get_yticklabels()
    if y_tick_labels:
        tick_fontsize = y_tick_labels[0].get_fontsize()
    else:
        tick_fontsize = plt.rcParams.get('ytick.labelsize', plt.rcParams.get('font.size', 10))
        #
        if isinstance(tick_fontsize, str): # TODO what do string descriptions of the font size correspond to?
            tick_fontsize = 10


    # Create invisible text so matplotlib can measure it
    t = ax.text(0, 0, "A", fontsize=tick_fontsize, alpha=0)
    # Need to draw, to figure out what are our units in terms of what is plotted on the y axis (data coordinates)
    fig.canvas.draw()
    # Get text bounding box in display (pixel) coordinates
    bbox = t.get_window_extent()
    # we do not need the sacrificial text any more
    t.remove()

    # Height in pixels
    font_height_pixels = bbox.height
    font_width_pixels = bbox.width
    # Convert pixel height and width to data units
    inv = ax.transData.inverted()
    p1 = inv.transform((0, 0))
    p2 = inv.transform((font_width_pixels, font_height_pixels))
    font_height_in_data_units = float(p2[1] - p1[1])
    font_width_in_data_units = float(p2[0] - p1[0])

    # prong, or teine or tip at the end of asterisk bar
    tip_length_in_data_units = font_height_in_data_units / 3
    # Asterisk font size is 1.2 of tick label font size (in points)
    asterisk_fontsize = tick_fontsize * 1.2
    # the glyph itself is 1/3 of the fontsize
    asterisk_height_in_data_units = font_height_in_data_units * 1.2 / 3
    dash_width_in_data_units = 2 * font_width_in_data_units


    geom = AsteriskBarDimensions(asterisk_fontsize=asterisk_fontsize,
                                 asterisk_height_in_data_units=asterisk_height_in_data_units,
                                 tip_length_in_data_units=tip_length_in_data_units,
                                 dash_width_in_data_units=dash_width_in_data_units)

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

    g: AsteriskBarDimensions = asterisk_bar_geometry(fig, ax, list_of_heights, p_values)

    n_bars = len(list_of_heights)
    x_positions = np.arange(n_bars)

    top_y = 0
    for pair_idx, (i, j) in enumerate(sorted_pairs):

        p_value = p_values[(i, j)]
        sig_symbol = get_significance_symbol(p_value)

        # Determine the height for this annotation
        # It should be above the tallest element in the span
        span_max_height = max(max_heights[min(i, j):max(i, j) + 1])
        y_line = span_max_height + level_spacing

        x1, x2 = x_positions[i], x_positions[j]

        # Draw horizontal line
        ax.plot([x1, x2], [y_line, y_line], color='black', linewidth=1)

        # Draw vertical lines at ends (1/2 the height of asterisk)
        for x in [x1, x2]:
            ax.plot([x, x], [y_line, y_line - g.tip_length], color='black', linewidth=1)

        # Add significance symbol
        x_mid = (x1 + x2) / 2
        y_text = y_line  - g.asterisk_height_inches * 0.5  # Small offset above the line

        if sig_symbol == "-":
            # Position: 1/3 of asterisk height above the horizontal significance line
            dash_y = y_line +  g.asterisk_height_inches * 0.5
            # Draw the dash line
            ax.plot([x_mid - g.dash_physical_width/2, x_mid + g.dash_physical_width/2],   [dash_y, dash_y],
                   color='black', linewidth=2, solid_capstyle='butt')
        else:
            ax.text(x_mid, y_text, sig_symbol, ha='center', va='bottom', fontsize=g.asterisk_fontsize)


    # Adjust y-axis limit to accommodate annotations
    current_ylim = ax.get_ylim()
    ax.set_ylim(current_ylim[0],top_y)


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
