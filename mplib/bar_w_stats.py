import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from scipy import stats

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


# =============================================================================
# Plotting Functions
# =============================================================================

def _add_data_points(ax: plt.Axes, df: pd.DataFrame, attribute: str,
                     groups: np.ndarray, leading_column: str,
                     x_positions: np.ndarray, bar_width: float,
                     color: str) -> None:
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

                ax.scatter(x_jittered, values, color="#282828", edgecolor="black",
                           linewidth=0.25, s=30, alpha=0.8, zorder=3)


def _add_significance_annotations(ax: plt.Axes, stat_results: pd.DataFrame,
                                  summary_df: pd.DataFrame, groups: np.ndarray,
                                  attributes: np.ndarray, leading_column: str,
                                  group_positions: np.ndarray,
                                  bar_width: float) -> None:
    """Add significance bars and annotations to the plot."""
    # Calculate y range for positioning
    y_max = (summary_df["mean"] + summary_df["sd"]).max()
    y_range = y_max - summary_df["mean"].min()
    annotation_offset = y_range * 0.05

    for _, row in stat_results.iterrows():
        if row["significance"] == "-":  # Skip non-significant
            continue

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
        y_bar = y_max + annotation_offset

        # Draw significance bar
        ax.plot([x1, x1, x2, x2],
                [y_bar - annotation_offset * 0.3, y_bar, y_bar, y_bar - annotation_offset * 0.3],
                color="black", linewidth=0.5)

        # Add significance symbol
        ax.text((x1 + x2) / 2, y_bar, row["significance"], ha="center", va="bottom", fontsize=12)

        # Update offset for next annotation
        annotation_offset += y_range * 0.08

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
                    y_label: str, bar_width: float) -> None:
    """Configure axis labels, ticks, and appearance."""
    # Y-axis
    ax.set_ylabel(y_label)

    # X-axis
    group_positions = np.arange(len(groups))

    # Set group names at the top
    for i, group in enumerate(groups):
        ax.text(group_positions[i], ax.get_ylim()[1], str(group),
                ha="center", va="bottom", fontsize=14, fontweight="bold")

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
    if not stat_results.empty:
        _add_significance_annotations(ax, stat_results, summary_df, groups,
                                      attributes, leading_column,
                                      group_positions, bar_width)

    # Configure axes
    _configure_axes(ax, groups, attributes, y_label, bar_width)


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
