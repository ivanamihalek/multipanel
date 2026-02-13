#! /usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from itertools import combinations

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

def significance_annotation(fig: plt.Figure, ax: plt.Axes, list_of_heights, p_values):
    """

    Args:
        fig:
        ax:
        list_of_heights:  the height that the significance annotation should sit above
        p_values: dictionary of p values with tuple (i, j) as the key

    Returns:
        None
    """

    n_bars = len(list_of_heights)
    x_positions = np.arange(n_bars)

    # don't touch the numbers hardcoded here - they
    # accomplish what is needed visually
    # Get y-axis tick label font size in points
    y_tick_labels = ax.get_yticklabels()
    if y_tick_labels:
        tick_fontsize = y_tick_labels[0].get_fontsize()
    else:
        tick_fontsize = plt.rcParams.get('ytick.labelsize', plt.rcParams.get('font.size', 10))
        if isinstance(tick_fontsize, str):
            tick_fontsize = 10

    # Asterisk font size is 1/2 of tick label font size (in points)
    asterisk_fontsize = tick_fontsize * 1.2

    # Convert font size in points to data coordinates for spacing calculations
    # We need to estimate the height of text in data coordinates
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    # Get figure dimensions
    fig_height_inches = fig.get_figheight()
    fig_width_inches = fig.get_figwidth()  # Using figure dimensions

    ax_position = ax.get_position()
    ax_height_inches = fig_height_inches * ax_position.height

    # Convert asterisk font size from points to data coordinates
    # Font size in points -> inches (1 point = 1/72 inch) -> data coordinates
    asterisk_height_inches = asterisk_fontsize / 72
    asterisk_height_data = asterisk_height_inches * (y_range / ax_height_inches)

    # Vertical line height: 1/2 of asterisk height
    vline_height = asterisk_height_data / 2

    # Vertical spacing between levels: 1/2 of asterisk height
    level_spacing = asterisk_height_data * 2.5

    # Find the maximum bar height to start annotations above it
    max_bar_height = max(list_of_heights)

    # Sort pairs by their span (distance between bars) to layer them properly
    sorted_pairs = sorted(p_values.keys(), key=lambda pair: abs(pair[1] - pair[0]))

    # Track the maximum height reached for each x position
    max_heights = [max_bar_height] * n_bars

    # Estimate asterisk width in data coordinates
    # A typical asterisk character width is about 0.6 * font_size in points
    asterisk_width_inches = (asterisk_fontsize * 0.6) / 72
    xlim = ax.get_xlim()
    x_range = xlim[1] - xlim[0]
    ax_width_inches = fig_width_inches * ax_position.width
    asterisk_width_data = asterisk_width_inches * (x_range / ax_width_inches)
    # Line width is 2 asterisks
    dash_line_width = asterisk_width_data

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
        ax.plot([x1, x1], [y_line, y_line - vline_height], color='black', linewidth=1)
        ax.plot([x2, x2], [y_line, y_line - vline_height], color='black', linewidth=1)

        # Add significance symbol
        x_mid = (x1 + x2) / 2
        y_text = y_line  - asterisk_height_data * 0.5  # Small offset above the line

        if sig_symbol == "-":
            # Position: 1/3 of asterisk height above the horizontal significance line
            dash_y = y_line +  asterisk_height_data
            # Draw the dash line
            ax.plot([x_mid - dash_line_width/2, x_mid + dash_line_width/2],   [dash_y, dash_y],
                   color='black', linewidth=2, solid_capstyle='butt')
        else:
            ax.text(x_mid, y_text, sig_symbol, ha='center', va='bottom', fontsize=asterisk_fontsize)

        # Update max heights for the span
        # Account for the line, the text, and spacing
        new_max_height = y_line + asterisk_height_data + level_spacing
        for k in range(min(i, j), max(i, j) + 1):
            max_heights[k] = max(max_heights[k], new_max_height)
        if top_y < new_max_height: top_y = new_max_height

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

    significance_annotation(fig, ax, list_of_avgs, p_values)
    # Draw the plot to get accurate font sizes
    fig.canvas.draw()

    plt.tight_layout()
    return fig, ax

def generate_test_values(number_of_avgs):

    np.random.seed(42)
    list_of_avgs = np.random.uniform(5, 15, number_of_avgs).tolist()
    # Generate test p-values for some pairs (not all combinations)
    p_values = {}
    # Adjacent comparisons
    for i, j in combinations(range(number_of_avgs), 2):
        p_values[(i, j)] = np.random.choice([0.00005, 0.0005, 0.005, 0.03, 0.1])

    return list_of_avgs, p_values

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
