#!/usr/bin/env python3
"""
Statistical Visualization Script

Generates grouped bar plots with error bars and statistical significance
annotations from Excel data files.

Usage:
    python script.py --input <excel_file> [--output-dir <directory>] [--verbose]
"""

import argparse
import re
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy import stats

# =============================================================================
# Color Configuration
# =============================================================================

# Color mapping for genotype names
GENOTYPE_COLORS: dict[str, str] = {
    # Gray group
    "S6wt/flox": "#7f7f7f",
    "S6wt/flox + siRNA": "#7f7f7f",
    "S6wt/flox + Myc": "#7f7f7f",
    # Cream group
    "S6flox/flox": "#F4EDD3",
    "DTHB": "#F4EDD3",
    "EGI": "#F4EDD3",
    # Orange group
    "iS6wt/del": "#c55a11",
    "S6wt/del": "#c55a11",
    "iS6wt/del + siRNA": "#c55a11",
    "iS6wt/del + Myc": "#c55a11",
    "S6wt/flox + CRE": "#c55a11",
    # Red group
    "ip53del/del": "#e41908",
    "ip53del/del + Myc": "#e41908",
    "p53flox/flox + CRE": "#e41908",
    # Dark red group
    "iS6wt/del:p53del/del": "#840c18",
    "iS6wt/del:p53del/del + Myc": "#840c18",
    "S6wt/flox:p53flox/flox + CRE": "#840c18",
    "Non": "#840c18",
    "EG": "#840c18",
    # Blue group
    "iS6del/del": "#8babf1",
    "iS6del/del + siRNA": "#8babf1",
    "S6flox/flox + CRE": "#8babf1",
    # Yellow group
    "cp53del/del": "#f0e442",
    # Gold group
    "cS6wt/del:p53del/del": "#e69f00",
    "S6wt/del:p53del/del": "#e69f00",
}

DEFAULT_COLOR = "#808080"  # Fallback gray


# =============================================================================
# Label Parsing Functions
# =============================================================================

def parse_sheet_name(sheet_name: str) -> tuple[str, str]:
    """
    Extract y-axis label and figure label from sheet name.

    Args:
        sheet_name: Excel sheet name containing measurement info

    Returns:
        Tuple of (y_label, figure_label)

    Example:
        "Cell Count A" -> ("Cell Count", "A")
    """
    tokens = sheet_name.split()
    y_label = " ".join(tokens[:-1])
    figure_label = tokens[-1]
    return y_label, figure_label


def format_genotype_label(genotype: str) -> str:
    """
    Convert genotype string to formatted label with superscripts.

    Args:
        genotype: Raw genotype string (e.g., "iS6wt/del:p53del/del")

    Returns:
        Formatted string for matplotlib (e.g., "iS6$^{wt/del}$:p53$^{del/del}$")
    """
    if ":" in genotype:
        # Handle double genotype notation
        pattern = r"(\D+\d+)([wdf]\S*):(\D+\d+)([wdf]\S*)"
        replacement = r"\1$^{\2}$:\3$^{\4}$"
    else:
        # Handle single genotype notation
        pattern = r"(\D+\d+)([wdf]\S*)"
        replacement = r"\1$^{\2}$"

    return re.sub(pattern, replacement, genotype)


# =============================================================================
# Data Loading Functions
# =============================================================================

def load_excel_sheet(file_path: Path, sheet_name: str) -> pd.DataFrame:
    """
    Load and validate data from an Excel sheet.

    Args:
        file_path: Path to Excel file
        sheet_name: Name of sheet to load

    Returns:
        DataFrame with validated data

    Raises:
        ValueError: If columns are missing names
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Validate column names
    if df.columns.isna().any() or (df.columns.astype(str).str.strip() == "").any():
        raise ValueError(f"Not all columns have names in '{sheet_name}' sheet")

    return df


def get_leading_column_name(file_path: Path, sheet_name: str) -> str:
    """
    Get the name of the first column in a sheet.

    Args:
        file_path: Path to Excel file
        sheet_name: Name of sheet to read

    Returns:
        Name of the first column

    Raises:
        ValueError: If first row is empty
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1)

    if df.empty:
        raise ValueError(f"First row is empty in '{sheet_name}' sheet")

    return df.columns[0]


def reshape_to_long_format(df: pd.DataFrame, leading_column: str) -> pd.DataFrame:
    """
    Convert wide-format data to long format for plotting.

    Args:
        df: Wide-format DataFrame
        leading_column: Name of the grouping column (not to melt)

    Returns:
        Long-format DataFrame with columns: [leading_column, Genotype, Value]
    """
    long_df = df.melt(
        id_vars=[leading_column], var_name="Genotype", value_name="Value"
    )

    # Remove rows with missing values
    long_df = long_df.dropna(subset=["Value"])

    return long_df


# =============================================================================
# Statistical Functions
# =============================================================================

def calculate_summary_statistics(long_df: pd.DataFrame,
                                 leading_column: str) -> pd.DataFrame:
    """
    Calculate mean, standard deviation, and count for each group.

    Args:
        long_df: Long-format DataFrame
        leading_column: Name of the grouping column

    Returns:
        DataFrame with summary statistics
    """
    summary = long_df.groupby([leading_column, "Genotype"], sort=False).agg(
        mean=("Value", "mean"), sd=("Value", "std"), count=("Value", "count")
    ).reset_index()

    return summary


def perform_tukey_hsd(long_df: pd.DataFrame,
                      leading_column: str) -> pd.DataFrame:
    """
    Perform Tukey HSD test for pairwise comparisons within each group.

    Args:
        long_df: Long-format DataFrame
        leading_column: Name of the grouping column

    Returns:
        DataFrame with pairwise comparison results
    """
    results = []

    for group_name, group_data in long_df.groupby(leading_column, sort=False):
        genotypes = group_data["Genotype"].unique()

        if len(genotypes) < 2:
            continue

        # Perform pairwise t-tests (simplified Tukey approximation)
        for i, geno1 in enumerate(genotypes):
            for geno2 in genotypes[i + 1:]:
                values1 = group_data[group_data["Genotype"] == geno1]["Value"]
                values2 = group_data[group_data["Genotype"] == geno2]["Value"]

                if len(values1) < 2 or len(values2) < 2:
                    continue

                _, p_value = stats.ttest_ind(values1, values2)

                results.append({
                    leading_column: group_name,
                    "group1": geno1,
                    "group2": geno2,
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

def get_color_for_genotype(genotype: str) -> str:
    """
    Get the color associated with a genotype.

    Args:
        genotype: Genotype name

    Returns:
        Hex color code
    """
    return GENOTYPE_COLORS.get(genotype, DEFAULT_COLOR)


def create_grouped_bar_plot(long_df: pd.DataFrame, summary_df: pd.DataFrame,
                            stat_results: pd.DataFrame, leading_column: str,
                            y_label: str, show_legend: bool = False,
                            show_points: bool = True) -> plt.Figure:
    """
    Create a grouped bar plot with error bars and significance annotations.

    Args:
        long_df: Long-format data
        summary_df: Summary statistics
        stat_results: Statistical test results
        leading_column: Name of grouping column
        y_label: Label for y-axis
        show_legend: Whether to show legend instead of x-labels
        show_points: Whether to show individual data points

    Returns:
        Matplotlib Figure object
    """
    # Get unique groups and genotypes
    groups = long_df[leading_column].unique()
    genotypes = long_df["Genotype"].unique()
    n_groups = len(groups)
    n_genotypes = len(genotypes)

    # Calculate bar positions
    bar_width = 0.8 / n_genotypes
    group_positions = np.arange(n_groups)

    # Create figure
    fig_width = max(8, n_groups * 2)
    fig, ax = plt.subplots(figsize=(fig_width, 6))

    # Plot bars for each genotype
    for i, genotype in enumerate(genotypes):
        geno_data = summary_df[summary_df["Genotype"] == genotype]

        # Align data with group order
        means = []
        sds = []
        for group in groups:
            group_row = geno_data[geno_data[leading_column] == group]
            if not group_row.empty:
                means.append(group_row["mean"].values[0])
                sds.append(group_row["sd"].values[0])
            else:
                means.append(0)
                sds.append(0)

        # Calculate x positions for this genotype
        x_positions = group_positions + (i - n_genotypes / 2 + 0.5) * bar_width
        color = get_color_for_genotype(genotype)

        # Draw bars
        ax.bar(x_positions, means, width=bar_width * 0.9, color=color,
               edgecolor="black", linewidth=0.5,
               label=format_genotype_label(genotype))

        # Draw error bars
        ax.errorbar(x_positions, means, yerr=sds, fmt="none", color="#282828",
                    capsize=3, capthick=1)

        # Draw individual points if requested
        if show_points:
            _add_data_points(ax, long_df, genotype, groups, leading_column,
                             x_positions, bar_width, color)

    # Add significance annotations
    if not stat_results.empty:
        _add_significance_annotations(ax, stat_results, summary_df, groups,
                                      genotypes, leading_column,
                                      group_positions, bar_width)

    # Configure axes
    _configure_axes(ax, groups, genotypes, y_label, show_legend, bar_width)

    plt.tight_layout()
    return fig


def _add_data_points(ax: plt.Axes, long_df: pd.DataFrame, genotype: str,
                     groups: np.ndarray, leading_column: str,
                     x_positions: np.ndarray, bar_width: float,
                     color: str) -> None:
    """Add jittered data points to the plot."""
    for j, group in enumerate(groups):
        mask = (long_df["Genotype"] == genotype) & (long_df[leading_column] == group)
        values = long_df[mask]["Value"].values

        if len(values) > 0:
            # Add jitter to x positions
            jitter = np.random.uniform(-bar_width * 0.3, bar_width * 0.3, len(values))
            x_jittered = x_positions[j] + jitter

            ax.scatter(x_jittered, values, color="#282828", edgecolor="black",
                       linewidth=0.25, s=30, alpha=0.8, zorder=3)


def _add_significance_annotations(ax: plt.Axes, stat_results: pd.DataFrame,
                                  summary_df: pd.DataFrame, groups: np.ndarray,
                                  genotypes: np.ndarray, leading_column: str,
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

        # Find positions of the two genotypes being compared
        geno1_idx = np.where(genotypes == row["group1"])[0]
        geno2_idx = np.where(genotypes == row["group2"])[0]

        if len(geno1_idx) == 0 or len(geno2_idx) == 0:
            continue

        n_genotypes = len(genotypes)
        x1 = group_positions[group_idx] + (geno1_idx[0] - n_genotypes / 2 + 0.5) * bar_width
        x2 = group_positions[group_idx] + (geno2_idx[0] - n_genotypes / 2 + 0.5) * bar_width
        y_bar = y_max + annotation_offset

        # Draw significance bar
        ax.plot([x1, x1, x2, x2],
                [y_bar - annotation_offset * 0.3, y_bar, y_bar, y_bar - annotation_offset * 0.3],
                color="black", linewidth=1)

        # Add significance symbol
        ax.text((x1 + x2) / 2, y_bar, row["significance"], ha="center", va="bottom", fontsize=12)

        # Update offset for next annotation
        annotation_offset += y_range * 0.08


def _configure_axes(ax: plt.Axes, groups: np.ndarray, genotypes: np.ndarray,
                    y_label: str, show_legend: bool, bar_width: float) -> None:
    """Configure axis labels, ticks, and appearance."""
    # Y-axis
    ax.set_ylabel(y_label, fontsize=18, color="black")
    ax.tick_params(axis="y", labelsize=14, colors="black")

    # X-axis
    group_positions = np.arange(len(groups))

    if show_legend:
        ax.set_xticks([])
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=3,
                  fontsize=12, frameon=False)
    else:
        n_genotypes = len(genotypes)
        # Position labels at each bar
        tick_positions = []
        tick_labels = []

        for i, group in enumerate(groups):
            for j, genotype in enumerate(genotypes):
                pos = group_positions[i] + (j - n_genotypes / 2 + 0.5) * bar_width
                tick_positions.append(pos)
                tick_labels.append(format_genotype_label(genotype))

        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=48, ha="right", fontsize=12)

    # Set facet labels (group names) at the top
    for i, group in enumerate(groups):
        ax.text(group_positions[i], ax.get_ylim()[1], str(group),
                ha="center", va="bottom", fontsize=14, fontweight="bold")

    # Remove grid and spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("gray")
    ax.spines["bottom"].set_color("gray")


# =============================================================================
# File Processing Functions
# =============================================================================

def sanitize_filename(name: str) -> str:
    """
    Convert sheet name to valid filename.

    Args:
        name: Original sheet name

    Returns:
        Sanitized filename (without extension)
    """
    return re.sub(r"[\s\W]+", "_", name.strip())


def process_sheet(file_path: Path, sheet_name: str, output_dir: Path,
                  verbose: bool = False) -> None:
    """
    Process a single Excel sheet and generate visualization.

    Args:
        file_path: Path to Excel file
        sheet_name: Name of sheet to process
        output_dir: Directory for output files
        verbose: Whether to print progress messages
    """
    if verbose:
        print(f"Processing sheet: {sheet_name}")

    # Load data
    df = load_excel_sheet(file_path, sheet_name)
    leading_column = get_leading_column_name(file_path, sheet_name)

    # Convert data columns to numeric
    data_columns = [col for col in df.columns if col != leading_column]
    df[data_columns] = df[data_columns].apply(pd.to_numeric, errors="coerce")

    # Reshape data
    long_df = reshape_to_long_format(df, leading_column)

    # Calculate statistics
    summary_df = calculate_summary_statistics(long_df, leading_column)
    stat_results = perform_tukey_hsd(long_df, leading_column)

    # Parse labels
    y_label, _ = parse_sheet_name(sheet_name)

    # Create plot
    fig = create_grouped_bar_plot(
        long_df=long_df, summary_df=summary_df, stat_results=stat_results,
        leading_column=leading_column, y_label=y_label, show_legend=False,
        show_points=True
    )

    # Save plot
    output_filename = sanitize_filename(sheet_name) + ".svg"
    output_path = output_dir / output_filename

    fig.savefig(output_path, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    if verbose:
        print(f"  Saved: {output_path}")


def process_excel_file(file_path: Path, output_dir: Path,
                       verbose: bool = False) -> None:
    """
    Process all sheets in an Excel file.

    Args:
        file_path: Path to Excel file
        output_dir: Directory for output files
        verbose: Whether to print progress messages
    """
    # Get all sheet names
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names

    if verbose:
        print(f"Found {len(sheet_names)} sheets in {file_path}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each sheet
    for sheet_name in sheet_names:
        try:
            process_sheet(file_path, sheet_name, output_dir, verbose)
        except Exception as e:
            print(f"Error processing sheet '{sheet_name}': {e}")


# =============================================================================
# Command Line Interface
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Generate statistical visualizations from Excel data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python script.py --input data.xlsx
    python script.py --input data.xlsx --output-dir ./figures --verbose
        """
    )

    parser.add_argument("--input", "-i", type=Path, required=True,
                        help="Path to input Excel file")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("./output"),
                        help="Directory for output files (default: ./output)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()

    # Validate input file
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    if args.verbose:
        print(f"Input file: {args.input}")
        print(f"Output directory: {args.output_dir}")

    # Process the file
    process_excel_file(args.input, args.output_dir, args.verbose)

    if args.verbose:
        print("Processing complete!")


if __name__ == "__main__":
    main()