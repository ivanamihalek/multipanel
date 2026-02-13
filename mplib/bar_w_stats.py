import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib import  rcParams
from scipy import stats
from matplotlib.colors import to_hex
from colorGenerator import Color

# =============================================================================
# Color Configuration
# =============================================================================

# Color mapping for attribute names
attribute_COLORS: dict[str, str] = {
   "A": "red",
    "B": "green",
    "C": "blue",
    "D": "magenta"
}

DEFAULT_COLOR = "#808080"  # Fallback gray


# =============================================================================
# Stats
# =============================================================================
def calculate_summary_statistics(df: pd.DataFrame,
                                 leading_column: str) -> pd.DataFrame:
    """
    Calculate mean, standard deviation, and count for each group.

    Args:
        df: Wide-format DataFrame
        leading_column: Name of the grouping column

    Returns:
        DataFrame with summary statistics (columns: [leading_column, attribute, mean, sd, count])
    """
    records = []

    # Identify data columns (all columns except the leading column)
    data_columns = [col for col in df.columns if col != leading_column]

    for group_name, group_data in df.groupby(leading_column, sort=False):
        for col in data_columns:
            values = group_data[col].dropna()
            if not values.empty:
                records.append({
                    leading_column: group_name,
                    "attribute": col,
                    "mean": values.mean(),
                    "sd": values.std(),
                    "count": values.count()
                })
            else:
                 records.append({
                    leading_column: group_name,
                    "attribute": col,
                    "mean": np.nan,
                    "sd": np.nan,
                    "count": 0
                })

    if not records:
        return pd.DataFrame(columns=[leading_column, "attribute", "mean", "sd", "count"])

    return pd.DataFrame(records)


def perform_tukey_hsd(df: pd.DataFrame,
                      leading_column: str) -> pd.DataFrame:
    """
    Perform Tukey HSD test (or t-test approximation) for pairwise comparisons within each group.

    Args:
        df: Wide-format DataFrame
        leading_column: Name of the grouping column

    Returns:
        DataFrame with pairwise comparison results
    """
    results = []

    # Identify data columns (attributes)
    attributes = [col for col in df.columns if col != leading_column]

    if len(attributes) < 2:
        return pd.DataFrame()

    for group_name, group_data in df.groupby(leading_column, sort=False):

        # Perform pairwise t-tests (simplified Tukey approximation)
        for i, attr1 in enumerate(attributes):
            for attr2 in attributes[i + 1:]:
                values1 = group_data[attr1].dropna()
                values2 = group_data[attr2].dropna()

                if len(values1) < 2 or len(values2) < 2:
                    continue

                _, p_value = stats.ttest_ind(values1, values2)

                results.append({
                    leading_column: group_name,
                    "group1": attr1,
                    "group2": attr2,
                    "p_value": p_value
                })

    if not results:
        return pd.DataFrame()

    result_df = pd.DataFrame(results)

    # Apply Bonferroni correction
    n_tests = len(result_df)
    result_df["p_adj"] = np.minimum(result_df["p_value"] * n_tests, 1.0)

    # Add significance symbols
    result_df["significance"] = result_df["p_adj"].apply(get_significance_symbol)

    return result_df


def get_significance_symbol(p_value: float) -> str:
    """
    Convert p-value to significance symbol.

    Args:
        p_value: Adjusted p-value

    Returns:
        Significance symbol (****/**/*/- for ns)
    """
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


def get_complementary_color(color_name: str) -> str:
    """
    Get the complementary color for a given color (name or hex) using colorGenerator.
    """
    # Convert named colors (e.g. 'red') to hex
    hex_color = to_hex(color_name)

    if hex_color.startswith('#'):
        hex_color = hex_color[1:]

    # Convert hex to RGB (0-255)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Create Color object
    c = Color(rgb=(r, g, b))

    # Get complementary color object
    comp = c.complementary()

    # Get RGB values (returns tuple of 0-255 ints via __repr__)
    comp_rgb = comp.__repr__()

    # Convert RGB to hex string
    return '#{:02x}{:02x}{:02x}'.format(*comp_rgb)


# =============================================================================
# Plotting Functions
# =============================================================================

def _add_data_points(ax: plt.Axes, df: pd.DataFrame, attribute: str,
                     groups: np.ndarray, leading_column: str,
                     x_positions: np.ndarray, bar_width: float,
                     bar_color: str) -> None:
    """Add jittered data points to the plot."""
    for j, group in enumerate(groups):
        # Filter rows for the current group
        group_data = df[df[leading_column] == group]

        # Extract values for the current attribute (column)
        if attribute in group_data.columns:
            values = group_data[attribute].dropna().values

            if len(values) > 0:
                # Add jitter to x positions
                jitter = np.random.uniform(-bar_width * 0.3, bar_width * 0.3, len(values))
                x_jittered = x_positions[j] + jitter

                point_color = get_complementary_color(bar_color)
                ax.scatter(x_jittered, values, color=point_color, edgecolor="black",
                           linewidth=0.25, s=30, alpha=0.8, zorder=3)


def _add_significance_annotations(ax: plt.Axes, stat_results: pd.DataFrame,
                                  summary_df: pd.DataFrame, groups: np.ndarray,
                                  attributes: np.ndarray, leading_column: str,
                                  group_positions: np.ndarray,
                                  bar_width: float) -> float:
    """Add significance bars and annotations to the plot."""
    # Calculate y range for positioning
    y_max = (summary_df["mean"] + summary_df["sd"]).max()
    y_min = summary_df["mean"].min()
    y_range = y_max - y_min if (y_max - y_min) > 0 else 1.0

    # Get axis tick label font size
    tick_label_size = rcParams["ytick.labelsize"]

    asterisk_fontsize = tick_label_size * 0.5

    # Estimate asterisk height in data coordinates (rough heuristic)
    fig_height_in = ax.get_figure().get_size_inches()[1]

    # Data range per inch
    data_per_inch = y_range / fig_height_in

    # Height in data coords (approx)
    asterisk_height_data = (asterisk_fontsize / 72.0) * data_per_inch * 2

    current_y_offset = y_max + asterisk_height_data

    max_y_used = current_y_offset

    for _, row in stat_results.iterrows():
        # User wants dashes for "no significance", so we don't skip "-"

        group = row[leading_column]
        group_idx = np.where(groups == group)[0]

        if len(group_idx) == 0:
            continue

        group_idx = group_idx[0]

        # Find positions of the two attributes being compared
        attr1_idx = np.where(attributes == row["group1"])[0]
        attr2_idx = np.where(attributes == row["group2"])[0]

        if len(attr1_idx) == 0 or len(attr2_idx) == 0:
            continue

        n_attributes = len(attributes)
        x1 = group_positions[group_idx] + (attr1_idx[0] - n_attributes / 2 + 0.5) * bar_width
        x2 = group_positions[group_idx] + (attr2_idx[0] - n_attributes / 2 + 0.5) * bar_width

        # Vertical space from previous elements
        y_bar = current_y_offset

        # Vertical lines height = 1/2 asterisk height
        v_line_h = asterisk_height_data * 0.5

        # Draw significance bar
        ax.plot([x1, x1, x2, x2], [y_bar - v_line_h, y_bar, y_bar, y_bar - v_line_h], color="black", linewidth=0.5)

        symbol = row["significance"]
        if symbol == "-":
            # Dash for no significance
            dash_width = bar_width * 0.1
            dash_height = asterisk_height_data * 0.33
            center_x = (x1 + x2) / 2

            # Draw dash as a rectangle/thick line
            rect = plt.Rectangle((center_x - dash_width/2, y_bar + v_line_h),
                                 dash_width, dash_height,
                                 facecolor="black", edgecolor="none")
            ax.add_patch(rect)

            # Update max used
            max_y_used = max(max_y_used, y_bar + v_line_h + dash_height)

        else:
            # Add significance symbol
            text_y = y_bar + v_line_h
            ax.text((x1 + x2) / 2, text_y, symbol, ha="center", va="bottom", fontsize=asterisk_fontsize)

            # Update max used
            max_y_used = max(max_y_used, text_y + asterisk_height_data)

        # Update offset for next annotation: vertical space = 1/2 asterisk height
        current_y_offset += (asterisk_height_data * 1.5)

    return max_y_used


def get_color_for_attribute(attribute: str) -> str:
    """
    Get the color associated with a attribute.

    Args:
        attribute: attribute name

    Returns:
        Hex color code
    """
    return attribute_COLORS.get(attribute, DEFAULT_COLOR)


def _configure_axes(ax: plt.Axes, groups: np.ndarray, attributes: np.ndarray,
                    y_label: str, bar_width: float, top_y_annotation: float = None) -> None:
    """Configure axis labels, ticks, and appearance."""
    # Y-axis
    ax.set_ylabel(y_label)

    # X-axis
    group_positions = np.arange(len(groups))

    # Set group names at the top
    # Use top_y_annotation if provided, else use current ylim top

    current_top = ax.get_ylim()[1]
    label_y = top_y_annotation if top_y_annotation is not None else current_top

    # Add some padding
    # Estimate padding same way as other elements or just a fixed factor
    # y_range approximation
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min
    padding = y_range * 0.05
    label_y += padding

    for i, group in enumerate(groups):
        ax.text(group_positions[i], label_y, str(group),
                ha="center", va="bottom", fontsize=14, fontweight="bold")

    # Update ylim to include labels
    # Rough estimate of label height
    ax.set_ylim(top=label_y + padding * 2)

    # Remove grid and spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("gray")
    ax.spines["bottom"].set_color("gray")

    ax.tick_params(axis='x',  which='both', bottom=False, top=False, labelbottom=False)


def create_grouped_bar_plot(ax: Axes, df: pd.DataFrame, summary_df: pd.DataFrame,
                            stat_results: pd.DataFrame,
                            y_label: str,  show_points: bool = True) -> None:
    """
    Create a grouped bar plot with error bars and significance annotations.

    Args:
        ax: (subplot) axes
        df: Wide-format data used for plotting points
        summary_df: Summary statistics
        stat_results: Statistical test results
        y_label: Label for y-axis
        show_points: Whether to show individual data points

    Returns:
        Matplotlib Figure object
    """
    # Get unique groups and attributes
    leading_column = df.columns[0]

    # Attributes are all columns except the leading one
    attributes = np.array([col for col in df.columns if col != leading_column])
    groups = df[leading_column].unique()

    n_groups = len(groups)
    n_attributes = len(attributes)

    # Calculate bar positions
    bar_width = 0.8 / n_attributes
    group_positions = np.arange(n_groups)

    # Plot bars for each attribute
    for i, attribute in enumerate(attributes):
        # Filter summary for this attribute
        attr_data = summary_df[summary_df["attribute"] == attribute]

        # Align data with group order
        means = []
        sds = []
        for group in groups:
            group_row = attr_data[attr_data[leading_column] == group]
            if not group_row.empty:
                means.append(group_row["mean"].values[0])
                sds.append(group_row["sd"].values[0])
            else:
                means.append(0)
                sds.append(0)

        # Calculate x positions for this attribute
        x_positions = group_positions + (i - n_attributes / 2 + 0.5) * bar_width
        color = get_color_for_attribute(attribute)

        # Draw bars
        ax.bar(x_positions, means, width=bar_width * 0.9, color=color,
               edgecolor="black", linewidth=0.5,
               label=attribute)

        # Draw error bars
        ax.errorbar(x_positions, means, yerr=sds, fmt="none", color="#282828",
                    capsize=1, capthick=0.5)

        # Draw individual points if requested
        if show_points:
            _add_data_points(ax, df, attribute, groups, leading_column,
                             x_positions, bar_width, color)

    # Add significance annotations
    top_y = (summary_df["mean"] + summary_df["sd"]).max()
    if not stat_results.empty:
        top_y = _add_significance_annotations(ax, stat_results, summary_df, groups,
                                      attributes, leading_column,
                                      group_positions, bar_width)

    # Configure axes
    _configure_axes(ax, groups, attributes, y_label, bar_width, top_y_annotation=top_y)


def bar_plot_w_stats(ax: Axes, df: pd.DataFrame, panel_label: str) -> None:

    leading_column_name = df.columns[0]

    # Convert data columns to numeric (in wide format)
    data_columns = [col for col in df.columns if col != leading_column_name]
    df[data_columns] = df[data_columns].apply(pd.to_numeric, errors="coerce")

    # Calculate statistics using wide format
    summary_df = calculate_summary_statistics(df, leading_column_name)
    stat_results = perform_tukey_hsd(df, leading_column_name)

    create_grouped_bar_plot(ax, df=df, summary_df=summary_df, stat_results=stat_results,
                            y_label='y_label',  show_points=True)
