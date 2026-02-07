xlsx to multipanel


# Tips

## Problem
When saving figures to SVG format using Matplotlib (especially versions 3.0+), the default behavior is to render 
text as paths (svg.fonttype='path'). This converts text strings into vector outlines/shapes 
(<path> elements) rather than editable <text> elements. Inkscape recognizes these as grouped paths or objects, 
not live text, so you can't select and edit the string, font, or size directly.

This default changed around Matplotlib 3.3 to improve portability 
(e.g., ensuring fonts look identical everywhere without requiring specific fonts installed), 
but it sacrifices editability in vector editors like Inkscape.

## Fix
1. Immediate: Set Matplotlib's svg.fonttype to 'none' before calling savefig(). 
This renders text as standard SVG <text> elements with CSS font-family properties, which Inkscape fully supports as editable text.
2. Permanent: Add svg.fonttype: none to your ~/.config/matplotlib/matplotlibrc file (create if needed).
3. On the project level: add to mplstyle file:
```text
# editable_svg.mplstyle
svg.fonttype : none

# Optional: Add other defaults for nicer SVGs/Inkscape compatibility
font.family : DejaVu Sans
svg.image_embedding_threshold : 5KB  # Embed small images as SVG (faster load)
savefig.bbox : tight
savefig.pad_inches : 0.1
```