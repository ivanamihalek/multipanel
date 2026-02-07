#! /usr/bin/env python3
"""Generate a simple example XLSX workbook with multiple sheets."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    out_path = Path(__file__).resolve().parent / "example.xlsx"

    x = np.linspace(0.0, 10.0, 50)

    sheets = {
        "exp1": pd.DataFrame({"x": x, "y": np.sin(x)}),
        "exp2": pd.DataFrame({"x": x, "y": np.cos(x)}),
        "exp3": pd.DataFrame({"x": x, "y": np.sin(x) * np.cos(x)}),
        # This extra sheet should be ignored silently:
        "extra_sheet": pd.DataFrame({"x": x, "y": x}),
    }

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(
                writer,
                sheet_name=name,
                index=False,
            )


if __name__ == "__main__":
    main()
