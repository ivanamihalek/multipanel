import matplotlib.pyplot as plt
import matplotlib.transforms as transforms


def add_panel_label_with_adjustment(ax, label, fontsize=14,  padding_factor=1.2):
    """
    Add a panel label to the upper left corner of a figure,
    adjusting the plot area to accommodate the label while keeping
    tick marks, tick labels, and axis labels at their original sizes.

    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        The axes to add the label to
    label : str
        The panel label text (e.g., 'A', 'B', 'C')
    fontsize : float
        Font size for the panel label
    padding_factor : float
        Multiplier for padding around the label
    """
    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer()

    # Get figure dimensions
    fig_width_inches = fig.get_figwidth()
    fig_height_inches = fig.get_figheight()

    # Calculate padding in figure coordinates
    padding_inches = (fontsize / 72) * padding_factor
    x_padding_fig = padding_inches / fig_width_inches
    y_padding_fig = padding_inches / fig_height_inches

    # Create the panel label temporarily to measure it
    temp_label = fig.text(
        0, 0, label,
        fontsize=fontsize,
        fontweight='bold',
        ha='left',
        va='bottom'
    )
    fig.canvas.draw()

    # Get label dimensions in figure coordinates
    label_bbox = temp_label.get_window_extent(renderer=renderer)
    label_bbox_fig = label_bbox.transformed(fig.transFigure.inverted())
    label_width = label_bbox_fig.width
    label_height = label_bbox_fig.height
    temp_label.remove()

    # Measure y-axis label width using the specified ylabel_fontsize
    ylabel = ax.yaxis.label
    ylabel_text = ylabel.get_text()

    # Get the y-axis label width
    fig.canvas.draw()
    ylabel = ax.yaxis.label
    ylabel_bbox = ylabel.get_window_extent(renderer=renderer)
    ylabel_bbox_fig = ylabel_bbox.transformed(fig.transFigure.inverted())
    ylabel_width = ylabel_bbox_fig.width if ylabel.get_text() else 0


    # Get tick label widths
    tick_labels = ax.get_yticklabels()
    max_tick_width = 0
    for tl in tick_labels:
        tl_bbox = tl.get_window_extent(renderer=renderer)
        tl_bbox_fig = tl_bbox.transformed(fig.transFigure.inverted())
        max_tick_width = max(max_tick_width, tl_bbox_fig.width)

    # Get current axes position
    ax_pos = ax.get_position()

    # Calculate the x position where the panel label ends
    # Panel label starts at x_padding_fig and has width label_width
    panel_label_right_edge = x_padding_fig + label_width

    # The y-axis label should start after the panel label plus a gap
    ylabel_left_edge = panel_label_right_edge + x_padding_fig

    # Calculate required left margin for the plot area
    # ylabel_left_edge + ylabel_width + gap + tick_labels + gap
    required_left = (
            ylabel_left_edge +
            ylabel_width +
            x_padding_fig / 2 +
            max_tick_width +
            x_padding_fig / 2
    )

    # Calculate required top margin for panel label
    title = ax.title
    title_bbox = title.get_window_extent(renderer=renderer)
    title_bbox_fig = title_bbox.transformed(fig.transFigure.inverted())
    title_height = title_bbox_fig.height if title.get_text() else 0

    required_top = (
            y_padding_fig +
            label_height +
            y_padding_fig
    )

    # Calculate new axes position
    new_left = max(ax_pos.x0, required_left)
    new_bottom = ax_pos.y0
    new_top = 1.0 - max(1.0 - ax_pos.y1, required_top)

    # Ensure we have room for title
    if title_height > 0:
        new_top = min(new_top, 1.0 - required_top - title_height - y_padding_fig / 2)

    new_width = ax_pos.x1 - new_left
    new_height = new_top - new_bottom

    # Ensure positive dimensions
    new_width = max(0.1, new_width)
    new_height = max(0.1, new_height)

    # Update axes position
    ax.set_position([new_left, new_bottom, new_width, new_height])

    # Redraw to update positions
    fig.canvas.draw()

    # Position panel label
    x_pos = x_padding_fig
    y_pos = 1.0 - y_padding_fig - label_height

    # Add the final panel label
    panel_label = fig.text(
        x_pos, y_pos, label,
        fontsize=fontsize,
        fontweight='bold',
        ha='left',
        va='bottom',
        transform=fig.transFigure
    )

    # Verify positioning (for debugging)
    fig.canvas.draw()
    final_label_bbox = panel_label.get_window_extent(renderer=renderer)
    final_label_bbox_fig = final_label_bbox.transformed(fig.transFigure.inverted())

    ylabel_bbox_actual = ax.yaxis.label.get_window_extent(renderer=renderer)
    ylabel_bbox_actual_fig = ylabel_bbox_actual.transformed(fig.transFigure.inverted())

    print(f"Panel label right edge: {final_label_bbox_fig.x1:.4f}")
    print(f"Y-axis label left edge: {ylabel_bbox_actual_fig.x0:.4f}")
    print(f"Gap: {ylabel_bbox_actual_fig.x0 - final_label_bbox_fig.x1:.4f}")

    return panel_label


# Example usage
fig, ax = plt.subplots(figsize=(8, 6))

ax.plot([0, 1, 2, 3], [0, 1, 0.5, 0.8], 'bs-', markersize=8)
ax.set_xlabel('X Axis', fontsize=28)
ax.set_ylabel('Y Axis Label', fontsize=28)
ax.set_title('Plot with Panel Label')

fig.canvas.draw()

add_panel_label_with_adjustment(
    ax,
    label='A',
    fontsize=76,
    padding_factor=0.02
)

plt.savefig('panel_label_fixed.png', dpi=100, bbox_inches='tight')
plt.show()