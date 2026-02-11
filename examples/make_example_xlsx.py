#!/usr/bin/env python3
"""Generate example Excel file with data for mosaic figure panels."""

import argparse
import numpy as np
import pandas as pd
from typing import Dict, Tuple


def create_line_data(n: int = 100, offset: float = 0.0) -> pd.DataFrame:
    """Create DataFrame with sinusoidal line data."""
    x = np.linspace(0, 10, n)
    y = np.sin(x + offset) + np.random.normal(0, 0.1, n)
    return pd.DataFrame({'x': x, 'y': y})


def create_scatter_data(n: int = 50) -> pd.DataFrame:
    """Create DataFrame with correlated scatter data."""
    x = np.random.normal(5, 2, n)
    y = 2 * x + np.random.normal(0, 1, n)
    return pd.DataFrame({'x': x, 'y': y})


def create_histogram_data(n: int = 500) -> pd.DataFrame:
    """Create DataFrame with normally distributed values."""
    data = np.random.normal(0, 1, n)
    return pd.DataFrame({'values': data})


def create_heatmap_data(size: int = 10) -> pd.DataFrame:
    """Create DataFrame with random 2D grid data."""
    data = np.random.rand(size, size)
    return pd.DataFrame(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate example Excel file for mosaic figures.")
    parser.add_argument("output", default="example_data.xlsx", nargs="?", help="Output Excel filename")
    args = parser.parse_args()

    # Map sheet names to (intended_plot_type, dataframe)
    sheets: Dict[str, Tuple[str, pd.DataFrame]] = {
        'timeseries_a': ('line', create_line_data(120, offset=0.0)),
        'scatter_b': ('scatter', create_scatter_data(40)),
        'distribution_c': ('histogram', create_histogram_data(600)),
        'intensity_d': ('heatmap', create_heatmap_data(12)),
        'timeseries_e': ('line', create_line_data(80, offset=2.0)),
        'scatter_f': ('scatter', create_scatter_data(90)),
    }

    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        for sheet_name, (_, df) in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Example Excel file created: {args.output}")
    print("Available sheets:", list(sheets.keys()))


if __name__ == "__main__":
    main()
