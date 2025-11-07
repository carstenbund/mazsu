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
| `grid.dot_radius` | Radius for background dots. | Yes | UI binds to this value and `add_grid_dots` honours it. 【F:default_config.yaml†L1-L8】【F:generator.py†L135-L154】【F:static/index.html†L61-L85】【F:static/script.js†L1-L92】
| `grid.dot_opacity` | Opacity for background dots. | Yes | Forwarded through the UI and rendered via `fill_opacity`. 【F:default_config.yaml†L1-L8】【F:generator.py†L135-L154】【F:static/script.js†L1-L92】
| `grid.dot_color` | Fill colour for grid dots. | Yes | New UI field writes to this key. 【F:default_config.yaml†L1-L8】【F:generator.py†L135-L154】【F:static/index.html†L61-L85】【F:static/script.js†L1-L92】
| `grid.lines.stroke_width` | Styling for random grid lines. | Yes | Passed through to `add_random_lines`. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】【F:static/script.js†L93-L155】
| `grid.lines.stroke_color` | Stroke colour for grid lines. | Yes | Same as above. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】
| `grid.lines.opacity` | Opacity for grid lines. | Yes | Same as above. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】
| `grid.lines.center_probability` | Base probability near the centre. | Yes | Controls line density alongside the UI slider. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】【F:static/index.html†L86-L111】【F:static/script.js†L93-L155】
| `grid.lines.edge_probability` | Probability near the edges. | Yes | Same as above. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】【F:static/script.js†L93-L155】
| `grid.lines.diagonal_bias` | Weighting for diagonal links. | Yes | Same as above. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】
| `grid.lines.max_connections` | Max connections per node. | Yes | Same as above. 【F:default_config.yaml†L5-L13】【F:generator.py†L156-L205】

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
| `figures.scale_factor` | Scales the imported pose geometry. | Yes | Slider input writes to this key and `add_figures` consumes it. 【F:default_config.yaml†L47-L53】【F:static/script.js†L93-L155】【F:generator.py†L210-L307】
| `figures.tranparency_factor` | Opacity modifier for figures (typo preserved). | Yes | Forwarded from the UI to polygon `fill_opacity`. 【F:default_config.yaml†L47-L53】【F:generator.py†L210-L307】【F:static/index.html†L118-L137】【F:static/script.js†L93-L155】
| `figures.amount_figures` | Target number of figures to place. | Yes | Now drives the placement loop. 【F:default_config.yaml†L47-L53】【F:generator.py†L210-L307】【F:static/script.js†L93-L155】
| `figures.line_thickness` | Outline weight for figure paths. | Yes | Applied when drawing polygons. 【F:default_config.yaml†L47-L53】【F:generator.py†L210-L307】【F:static/script.js†L93-L155】
| `figures.line_color` | Outline colour. | Yes | New UI field writes to this key. 【F:default_config.yaml†L47-L53】【F:generator.py†L210-L307】【F:static/index.html†L118-L137】
| `figures.line_opacity` | Outline opacity. | Yes | Applied to polygon stroke. 【F:default_config.yaml†L47-L53】【F:generator.py†L210-L307】【F:static/script.js†L93-L155】

## Next steps

Expose any "No" entries above through the web configuration when the corresponding generator logic is implemented or updated to consume the settings.
