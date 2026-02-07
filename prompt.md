Outline a project that uses matplotlib subplot_mosaic capability to create a multipanel figure in svg format from ans xlsx
file and yaml specification file. Ths xlsx should contain multiple sheets, with the data in each used to create
one panel in the figure.

The YAML file should specify which sheet should map to which panel, for example
```yaml
sheet2panel:
  exp1: I
  exp2: J
  exp3: K
```
Each panel should be labeled with the character specified in `sheet2panel`.

The YAML file should also specify the layout like expected by subplot_mosaic(), for example:
```yaml
layout:
   IIJJ
   KKKK
   0000
```
The script should chek that the panel names in `sheet2panel` and `layout` match. 
If there are more panel names in `sheet2panel` than in `layout`, the script should error out. 
If there are more panel names in `layout` than in `sheet2panel`, the script should issue a warning and proceed, 
marking the panel with the corresponding character, but leaving it empty as a placeholder.
The panel labeled as `0` should be left unlabeled, and a text "LEGEND" placed therein.

The script should further check that each sheet name used as the ley in `sheet2panel` exists in the input xlsx file,
and error out if there are keys in  `sheet2panel` which do not correspond to a sheet in the input file. 
If there are sheet names in the xlsx file, they should be ignored silently.

The styling should be input from a file called `multi.mplstyle` that should be present in the same directory
as the script itself.

Make sure that the code is factored into single-use functions, grouped into files in an
intuitive way.

The main script should have main() and shebang line, and  use arg parsing.
All scripts should use type hinting, docstrings and line comments as needed. 
Use Google coding style with  horizontal argument formatting in function definitions and calls.

Create simple input for testing.
