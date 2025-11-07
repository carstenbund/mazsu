# Configurable Field Inventory

This document lists configuration keys that influence the generator pipeline and notes whether they are currently exposed through the web configuration panel. Use it as a checklist when extending the UI.

## Runtime request parameters

| Field path | Purpose | Exposed in web UI? | Notes |
| --- | --- | --- | --- |
| `grid_size` | Controls the spacing of the logical grid passed to `SymbolicField`. | Yes | Input elements for grid size, width, and height are posted with each request. 【F:app.py†L64-L96】【F:static/script.js†L41-L69】
| `width` | Output width in pixels. | Yes | Same controls as above. 【F:app.py†L64-L96】【F:static/script.js†L41-L69】
| `height` | Output height in pixels. | Yes | Same controls as above. 【F:app.py†L64-L96】【F:static/script.js†L41-L69】

## `default_config.yaml`

### `grid` appearance

| Field path | Purpose | Exposed in web UI? | Notes |
| --- | --- | --- | --- |
| `grid.dot_radius` | Intended radius for background dots. | No | UI never reads or writes this key; dots are drawn with a hard-coded radius instead. 【F:default_config.yaml†L1-L8】【F:generator.py†L140-L148】【F:static/script.js†L7-L62】
| `grid.dot_opacity` | Intended opacity for background dots. | No | Not surfaced in the UI and not forwarded to the renderer yet. 【F:default_config.yaml†L1-L8】【F:static/script.js†L7-L62】
| `grid.lines.stroke_width` | Styling for random grid lines. | No | Line drawing currently uses fixed style values. 【F:default_config.yaml†L5-L8】【F:generator.py†L165-L200】【F:static/script.js†L7-L62】
| `grid.lines.stroke_color` | Stroke colour for grid lines. | No | Same as above. 【F:default_config.yaml†L5-L8】【F:generator.py†L165-L200】
| `grid.lines.opacity` | Opacity for grid lines. | No | Same as above. 【F:default_config.yaml†L5-L8】【F:generator.py†L165-L200】

### Heatmap controls

| Field path | Purpose | Exposed in web UI? | Notes |
| --- | --- | --- | --- |
| `heatmaps.grid.file` | Base map for grid density. | Yes | The form allows editing the file path and replaces it if uploads are provided. 【F:default_config.yaml†L11-L17】【F:app.py†L69-L81】【F:static/script.js†L7-L56】
| `heatmaps.grid.use_perlin` | Enables procedural noise for the grid layer. | Yes | Checkbox toggles this flag. 【F:default_config.yaml†L13-L17】【F:static/script.js†L7-L56】
| `heatmaps.grid.mode` | Combination mode between file and Perlin map. | Yes | Select control provides the three modes. 【F:default_config.yaml†L13-L17】【F:static/script.js†L7-L56】
| `heatmaps.grid.perlin_scale` | Scale parameter for Perlin noise. | Yes | Numeric input mapped to this key. 【F:default_config.yaml†L13-L17】【F:static/script.js†L7-L56】
| `heatmaps.grid.perlin_octaves` | Octave count for Perlin noise. | Yes | Numeric input mapped to this key. 【F:default_config.yaml†L13-L17】【F:static/script.js†L7-L56】
| `heatmaps.figure.file` | Base map for figure density. | Yes | Mirrored controls exist for the figure layer. 【F:default_config.yaml†L19-L25】【F:static/script.js†L14-L56】
| `heatmaps.figure.use_perlin` | Enables procedural noise for figures. | Yes | As above. 【F:default_config.yaml†L19-L25】【F:static/script.js†L14-L56】
| `heatmaps.figure.mode` | Combination mode for figure heatmap. | Yes | As above. 【F:default_config.yaml†L19-L25】【F:static/script.js†L14-L56】
| `heatmaps.figure.perlin_scale` | Perlin noise scale for figures. | Yes | As above. 【F:default_config.yaml†L19-L25】【F:static/script.js†L14-L56】
| `heatmaps.figure.perlin_octaves` | Octave count for figure noise. | Yes | As above. 【F:default_config.yaml†L19-L25】【F:static/script.js†L14-L56】
| `heatmaps.figure.palettes` | Palette options for figure fills. | Yes | Text input maps to the palette array. 【F:default_config.yaml†L26-L32】【F:static/script.js†L14-L56】
| `heatmaps.shapes.<name>.file` | Shape-specific mask used to bias placement (e.g., standing or walking). | No | `SymbolicField` loads each shape map, but the UI provides no controls for them. 【F:default_config.yaml†L35-L45】【F:generator.py†L99-L118】【F:static/script.js†L7-L62】
| `heatmaps.shapes.<name>.use_perlin` | Enables procedural noise for a specific shape map. | No | Same as above. 【F:default_config.yaml†L35-L45】【F:generator.py†L99-L118】
| `heatmaps.shapes.<name>.mode` | Combination mode for a shape map. | No | Same as above. 【F:default_config.yaml†L35-L45】【F:generator.py†L99-L118】
| `heatmaps.shapes.<name>.perlin_scale` | Optional Perlin scale per shape. | No | Only provided for some shapes in defaults. 【F:default_config.yaml†L35-L45】【F:generator.py†L99-L118】
| `heatmaps.shapes.<name>.perlin_octaves` | Optional Perlin octave count per shape. | No | Only provided for some shapes in defaults. 【F:default_config.yaml†L35-L45】【F:generator.py†L99-L118】

### Figure rendering

| Field path | Purpose | Exposed in web UI? | Notes |
| --- | --- | --- | --- |
| `figures.scale_factor` | Scales the imported pose geometry. | Yes | Slider input writes to this key and `add_figures` consumes it. 【F:default_config.yaml†L47-L51】【F:static/script.js†L41-L61】【F:generator.py†L246-L307】
| `figures.tranparency_factor` | Intended opacity modifier for figures (typo preserved). | No | Not used anywhere in the renderer or UI today. 【F:default_config.yaml†L47-L51】【F:generator.py†L246-L307】【F:static/script.js†L41-L62】
| `figures.amount_figures` | Target number of figures to place. | No | `add_figures` still relies on its positional `num_figures` argument; the UI lacks a control. 【F:default_config.yaml†L47-L51】【F:generator.py†L236-L308】【F:static/script.js†L41-L62】
| `figures.line_thickness` | Intended outline weight for figure paths. | No | Outlines are not currently drawn; value is unused in code and absent from the UI. 【F:default_config.yaml†L47-L51】【F:generator.py†L246-L307】【F:static/script.js†L41-L62】

## Next steps

Expose any "No" entries above through the web configuration when the corresponding generator logic is implemented or updated to consume the settings.
