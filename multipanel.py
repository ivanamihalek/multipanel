#!/usr/bin/env python3
"""Generate multipanel mosaic figures from Excel data with uniform label alignment."""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Tuple, Any

from mplib.yaml_parser import parse_yaml_config, Config
from mplib.xlsx_parser import parse_xlsx_data
from mplib.layout import calculate_max_label_metrics, adjust_panel_layout
from mplib.plotting import plot_panel_content, plot_dummy_fallback

def _style_path_for_script() -> Path:
    """Return path to multi.mplstyle located next to this script."""
    return Path(__file__).resolve().parent / "multi.mplstyle"

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mosaic figure from Excel/YAML configuration.")
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument("-o", "--output", default="output.png", help="Output filename (default: output.png)")
    parser.add_argument("--fontsize", type=int, default=48, help="Font size for panel labels (default: 48)")
    parser.add_argument("--padding", type=float, default=0.2, help="Padding factor (default: 0.2)")
    args = parser.parse_args()

    plt.style.use(str(_style_path_for_script() ))


    # 1. Load Configuration
    config: Config = parse_yaml_config(args.config)
    layout_str = "\n".join(config.layout_rows)

    xlsx_path = config.xlsx_path
    sheet2panel = config.sheet2panel

    # 2. Load Excel Data
    panel_data = parse_xlsx_data(xlsx_path, sheet2panel)

    # 3. Setup Figure
    fig, axd = plt.subplot_mosaic(layout_str, figsize=(16, 12), constrained_layout=False)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.05, wspace=0.3, hspace=0.3)

    # 4. Populate Panels
    for panel_label, ax in axd.items():
        if panel_label in panel_data:
            df, plot_type = panel_data[panel_label]
            plot_panel_content(ax, df, plot_type, panel_label)
        else:
            plot_dummy_fallback(ax, panel_label)

    # 5. Pre-calculate text extents
    fig.canvas.draw()

    # 6. Calculate Master Label Dimensions
    all_labels = list(axd.keys())
    max_w, max_h = calculate_max_label_metrics(fig, all_labels, fontsize=args.fontsize)
    print(f"Applying layout adjustment. Max label width: {max_w:.4f} (figure coords)")

    # 7. Adjust Layout and Place Labels
    for label, ax in sorted(axd.items()):
        adjust_panel_layout(fig, ax, label, fontsize=args.fontsize, padding_factor=args.padding,
                            fixed_label_width=max_w, fixed_label_height=max_h)

    # 8. Save Output
    plt.savefig(args.output, dpi=100)
    print(f"Figure saved to {args.output}")


if __name__ == "__main__":
    main()
