#!/usr/bin/env python3
"""CLI entry point for generating a multi-panel SVG from XLSX + YAML spec."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mplib.io_utils import load_plot_spec, list_xlsx_sheet_names
from mplib.plotting import create_mosaic_figure
from mplib.validate import validate_spec_against_xlsx


def parse_args() -> argparse.Namespace:
    """Parses CLI arguments."""
    parser = argparse.ArgumentParser(description=("Create a multi-panel SVG using matplotlib subplot_mosaic "
                                                  "from an XLSX workbook and a YAML specification."), )
    parser.add_argument("-x", "--xlsx", required=True, type=Path, help="Path to input XLSX workbook.", )
    parser.add_argument("-y", "--yaml", required=True, type=Path, help="Path to YAML specification file.", )
    parser.add_argument("-o", "--out", required=True, type=Path, help="Path to output SVG file.", )
    return parser.parse_args()


def apply_style() -> None:
    """Applies matplotlib style from multi.mplstyle next to this script."""
    style_path = Path(__file__).resolve().parent / "multi.mplstyle"
    if style_path.exists():
        plt.style.use(str(style_path))
    else:
        raise FileNotFoundError(f"Expected matplotlib style file next to script: {style_path}")


def get_data() -> Dict[str, pd.DataFrame]:
    x = np.linspace(0, 10, 100)

    # Define data; 'B' is omitted to demonstrate the empty placeholder.
    data = {
        'A': {'x': x, 'y': np.sin(x)},
        'B': {'x': x, 'y': np.cos(x)},
        'C':  {'x': x, 'y': np.cos(x)},
        'D': {'x': x, 'y': np.sin(x)},
    }
    dict_of_dataframes = {key: pd.DataFrame(value) for key, value in data.items()}
    #
    # spec = load_plot_spec(path=args.yaml)
    #
    # xlsx_sheets = list_xlsx_sheet_names(xlsx_path=args.xlsx, )
    # validate_spec_against_xlsx(spec=spec, xlsx_sheet_names=xlsx_sheets)
    return dict_of_dataframes

def main() -> None:

    args = parse_args()
    apply_style()

    # Define layout: Row 1 has A and B.
    layout_structure = [['A', 'A'], ['B', 'B'], ['C', 'D']]
    data = get_data()

    fig = create_mosaic_figure(layout_structure, data)
    # save_figure_svg(fig=fig, out_path=args.out, )


if __name__ == "__main__":
    main()
