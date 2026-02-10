I need a tool to create a labeled multipanel figure using matplotlib's gridspec. 

The tool should read in a yaml file specifying the path to the input spreadsheet in the xlsx format and the layout detail.  The output should be  in the svg format. The layout should be specified in the format resembling the one used by matplotlib's  subplot_mosaic capability. The yaml should also specify which xlsx sheet corresponds to which  panel. Here is an example yaml file:

```yaml
xlsx_path:
  /path/to/spreadsheet.xlsx	

sheet2panel:
  exp1: I
  exp2: J
  exp3: K
  
layout:
   IIJJ
   KKKK
   0000

```

The script should check that the panel names in `sheet2panel` and `layout` match. 
If there are more panel names in `sheet2panel` than in `layout`, the script should error out. 
If there are more panel names in `layout` than in `sheet2panel`, the script should issue a warning and proceed, 
marking the panel with the corresponding character, but leaving it empty as a placeholder.
The panel labeled as `0` should be left unlabeled, and a text "LEGEND" placed therein.

The script should further check that each sheet name used as the key in `sheet2panel` exists in the input xlsx file,
and error out if there are keys in  `sheet2panel` which do not correspond to a sheet in the input file. 
If there are sheet names in the xlsx file, they should be ignored silently.

The styling should be input from a file called `multi.mplstyle` that should be present in the same directory as the script itself.

The layout should be such that each panel consists of a subfigure and a margin whose width on each side of the subfigure should be specified as a fraction of the whole figure width. The panel label should be placed within the margin bounds to the left and above the subfigure. In particular, this means that the panel label should be to the left of the y-axis label in the subfigure.

Make sure that the code is factored into single-use functions, grouped into files in an
intuitive way.

The main script should have main() and shebang line, and  use arg parsing.
All scripts should use type hinting, docstrings and line comments as needed. 

Please format the Python function calls and definitions with all arguments aligned horizontally on a single line, rather than stacking them vertically one per line. Follow PEP 8 guidelines for long argument lists: hang subsequent lines at the opening parenthesis position without vertical alignment, but prefer a single horizontal line if it fits within the 120-character limit.

Create simple input for testing.
