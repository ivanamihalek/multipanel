#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from mplib.config import load_config
from mplib.plotting import build_figure


def _style_path_for_script() -> Path:
    """Return path to multi.mplstyle located next to this script."""
    return Path(__file__).resolve().parent / "multi.mplstyle"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a labeled multi-panel SVG figure from xlsx + YAML layout.")
    parser.add_argument("-y", "--config-yaml", type=Path, help="Path to YAML configuration file.")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Optional output SVG path (overrides YAML).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config_yaml)

    if args.output is not None:
        cfg.output_svg = args.output

    style_path = _style_path_for_script()
    if not style_path.exists():
        raise FileNotFoundError(f"Required style file not found: {style_path}")

    plt.style.use(str(style_path))

    fig = build_figure(cfg)
    cfg.output_svg.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.output_svg, format="svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
