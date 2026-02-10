#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    xlsx_path = "example.xlsx"

    x = np.arange(0, 6)
    df1 = pd.DataFrame({"x": x, "y": x})
    df2 = pd.DataFrame({"x": x, "y": x ** 2})
    df3 = pd.DataFrame({"x": x, "y": np.sqrt(x)})

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="exp1", index=False)
        df2.to_excel(writer, sheet_name="exp2", index=False)
        df3.to_excel(writer, sheet_name="exp3", index=False)
        pd.DataFrame({"note": ["this sheet is ignored"]}).to_excel(writer, sheet_name="ignore_me", index=False)

    print(f"Wrote {xlsx_path}")


if __name__ == "__main__":
    main()
