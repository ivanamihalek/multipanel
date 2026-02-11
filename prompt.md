Below is a demo script, a Python command-line interface (CLI) application that generates complex multi-panel
Matplotlib figures based on a mosaic layout string parsed from a YAML configuration file.

* It automatically populates the subplots with diverse dummy content—including line plots, scatter plots, histograms,
and heatmaps—complete with titles and axis labels to test layout stability. 
* The core feature is a custom layout algorithm that pre-calculates the rendered bounding boxes of all text elements to
find the widest panel label, ensuring uniform vertical alignment across all panels. 
* The script then dynamically shrinks and shifts the active plotting area of each subplot to create a dedicated "gutter"
in the top-left corner, allowing for large, bold panel labels to be placed without overlapping Y-axis labels, ticks, or
titles. 
* Finally, it maximizes the use of the figure canvas by aggressively reducing outer margins via
subplots_adjust before saving the high-resolution output to an image file.

```python
#!/usr/bin/env python3
import argparse
import sys
import yaml
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Any
from matplotlib.figure import Figure
from matplotlib.axes import Axes


def generate_dummy_content(axd: Dict[str, Axes]) -> None:
    """
    Populates the axes with dummy content based on their label keys.
    Cycles through different plot types to make them look distinct.
    """
    x = np.linspace(0, 10, 100)

    # Sort keys to ensure deterministic assignment of plot types
    for i, (label, ax) in enumerate(sorted(axd.items())):
        # Cycle through 4 types of plots based on index
        plot_type = i % 4

        if plot_type == 0:
            # Line plot
            ax.plot(x, np.sin(x + i), label='Sine')
            ax.set_title(f"Panel {label}: Line Plot")
            ax.set_ylabel("Amplitude")

        elif plot_type == 1:
            # Scatter plot
            noise = np.random.normal(0, 0.2, 20)
            ax.scatter(x[:20], np.cos(x[:20]) + noise, c='r')
            ax.set_title(f"Panel {label}: Scatter")
            ax.set_ylabel("Observations")

        elif plot_type == 2:
            # Histogram
            data = np.random.normal(0, 1 + i * 0.5, 500)
            ax.hist(data, bins=20, alpha=0.7, color='purple')
            ax.set_title(f"Panel {label}: Histogram")
            ax.set_ylabel("Frequency")

        elif plot_type == 3:
            # Image/Heatmap
            data = np.random.rand(10, 10)
            ax.imshow(data, cmap='viridis', aspect='auto')
            ax.set_title(f"Panel {label}: Heatmap")
            ax.set_ylabel("Y-Pixel")

        # Add X-axis labels to everything (as requested)
        ax.set_xlabel(f"X-Axis Data ({label})")
        ax.grid(True, alpha=0.3)


def calculate_max_label_metrics(
        fig: Figure,
        labels: List[str],
        fontsize: int
) -> Tuple[float, float]:
    """
    Calculates the width/height of the widest/tallest label in Figure coordinates.
    """
    renderer = fig.canvas.get_renderer()
    max_width = 0.0
    max_height = 0.0

    for label in labels:
        # Create temporary text to measure
        temp_text = fig.text(0, 0, label, fontsize=fontsize, fontweight='bold')

        # Get dimensions
        bbox = temp_text.get_window_extent(renderer=renderer)
        bbox_fig = bbox.transformed(fig.transFigure.inverted())

        max_width = max(max_width, bbox_fig.width)
        max_height = max(max_height, bbox_fig.height)

        temp_text.remove()

    return max_width, max_height


def adjust_panel_layout(
        fig: Figure,
        ax: Axes,
        label: str,
        fontsize: int,
        padding_factor: float,
        fixed_label_width: float,
        fixed_label_height: float
) -> None:
    """
    Adjusts a specific axis within a mosaic to fit a panel label using
    pre-calculated fixed dimensions.
    """
    renderer = fig.canvas.get_renderer()

    # 1. Get original position (the "slot" assigned by mosaic)
    base_pos = ax.get_position()
    base_x0, base_y0 = base_pos.x0, base_pos.y0
    base_x1, base_y1 = base_pos.x1, base_pos.y1

    # 2. Calculate padding in Figure coordinates
    fig_width, fig_height = fig.get_size_inches()
    padding_inches = (fontsize / 72) * padding_factor
    x_padding_fig = padding_inches / fig_width
    y_padding_fig = padding_inches / fig_height

    # 3. Measure Y-Axis Label width (specific to this plot)
    ylabel = ax.yaxis.label
    ylabel_bbox = ylabel.get_window_extent(renderer=renderer)
    ylabel_bbox_fig = ylabel_bbox.transformed(fig.transFigure.inverted())
    ylabel_width = ylabel_bbox_fig.width if ylabel.get_text() else 0

    # 4. Measure Max Tick width (specific to this plot)
    max_tick_width = 0.0
    for tl in ax.get_yticklabels():
        if tl.get_text():
            tl_bbox = tl.get_window_extent(renderer=renderer)
            tl_bbox_fig = tl_bbox.transformed(fig.transFigure.inverted())
            max_tick_width = max(max_tick_width, tl_bbox_fig.width)

    # 5. Measure Title height (specific to this plot)
    title = ax.title
    title_bbox = title.get_window_extent(renderer=renderer)
    title_bbox_fig = title_bbox.transformed(fig.transFigure.inverted())
    title_height = title_bbox_fig.height if title.get_text() else 0

    # 6. Calculate Margins
    gap = x_padding_fig / 2.0

    # Left Inset: Padding + LabelWidth + Gap + YLabel + Gap + Ticks + Gap
    required_left_inset = (
            x_padding_fig +
            fixed_label_width +
            gap +
            ylabel_width +
            gap +
            max_tick_width +
            gap
    )

    # Top Inset: Padding + LabelHeight + Padding + TitleHeight
    required_top_inset = (
            y_padding_fig +
            fixed_label_height +
            y_padding_fig +
            title_height
    )

    # 7. Apply new geometry
    new_left = base_x0 + required_left_inset
    new_top = base_y1 - required_top_inset
    new_width = base_x1 - new_left
    new_height = new_top - base_y0

    if new_width <= 0 or new_height <= 0:
        print(f"Warning: Panel {label} is too small for the requested font/layout.", file=sys.stderr)
        return

    ax.set_position([new_left, base_y0, new_width, new_height])

    # 8. Place permanent label at top-left of the ORIGINAL slot
    final_x = base_x0 + x_padding_fig
    final_y = base_y1 - y_padding_fig - fixed_label_height

    fig.text(
        final_x, final_y, label,
        fontsize=fontsize,
        fontweight='bold',
        ha='left',
        va='bottom',
        transform=fig.transFigure
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a multipanel figure with aligned labels from YAML.")
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument("-o", "--output", default="output.png", help="Output filename (default: output.png)")
    parser.add_argument("--fontsize", type=int, default=48, help="Font size for panel labels (default: 48)")
    parser.add_argument("--padding", type=float, default=0.2, help="Padding factor (default: 0.2)")

    args = parser.parse_args()

    # 1. Load Configuration
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML: {e}", file=sys.stderr)
        sys.exit(1)

    layout_str = config.get('layout')
    if not layout_str:
        print("Error: YAML must contain a 'layout' key.", file=sys.stderr)
        sys.exit(1)

    # 2. Setup Figure
    # constrained_layout=False is required for manual positioning
    fig, axd = plt.subplot_mosaic(layout_str, figsize=(16, 12), constrained_layout=False)

    # *** CRITICAL STEP: Adjust Outer Margins ***
    # This pushes the panels to the edge of the image before we calculate label positions.
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.05, wspace=0.3, hspace=0.3)

    # 3. Generate Content
    generate_dummy_content(axd)

    # 4. Draw to calculate initial renderer boxes
    fig.canvas.draw()

    # 5. Calculate Master Dimensions (widest label)
    all_labels = list(axd.keys())
    max_w, max_h = calculate_max_label_metrics(fig, all_labels, fontsize=args.fontsize)

    print(f"Applying layout adjustment. Max label width: {max_w:.4f} (figure coords)")

    # 6. Apply adjustments
    for label, ax in sorted(axd.items()):
        adjust_panel_layout(
            fig,
            ax,
            label,
            fontsize=args.fontsize,
            padding_factor=args.padding,
            fixed_label_width=max_w,
            fixed_label_height=max_h
        )

    # 7. Final Draw and Save
    plt.savefig(args.output, dpi=100)
    print(f"Figure saved to {args.output}")


if __name__ == "__main__":
    main()
```

Generalize this script into an application that reads the input from an xlsx file. To do that

1. extract the dummy content creation script called `make_example_xlsx.py` which creates sheets with some intuitive names,
   indicative of the sheet content, and populates each sheet with data needed to create the figure
2. extends the yaml parser to read in the path to the xlsx sheet, abd the mapping between the sheet and the panel names

Here is an example of the new YAML file

```yaml
xlsx_path:
  /path/to/spreadsheet.xlsx

sheet2panel:
  exp1: I
  exp2: J
  exp3: K

layout:
  AABB
  CCBB
  DDDE
```

3. creates xlsx parser which takes in the path to xlsx file, and returns a dictionary with the sheet / panel name as
   the key, and pandas dataframe and the figure type (scatter, heatmap) as the content 
4. modify the main() to use the new xlsx and yaml parsing capability. The arg parsing should be modified accordingly



Make sure that the code is factored into single-use functions, grouped into files intuitively.

The main script should have main() and shebang line, and use arg parsing.
All scripts should use type hinting, docstrings and line comments as needed.

Please format the Python function calls and definitions with all arguments aligned horizontally on a single line, rather
than stacking them vertically one per line. Follow PEP 8 guidelines for long argument lists: hang subsequent lines at
the opening parenthesis position without vertical alignment, but prefer a single horizontal line if it fits within the
120-character limit.

Use Top-Down/Helper Functions First convention in ordering functions within a file.