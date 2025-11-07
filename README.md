# Mazsu Symbolic Field Generator

Mazsu is a Flask web application that produces generative SVG compositions made of a dotted grid, connective lines, and polygonal “figure” silhouettes.  The layout of each layer is driven by configurable heatmaps that can be blended with procedurally generated Perlin noise fields.

The web UI (served from `static/index.html`) lets you tweak heatmap options, collapse/expand the control panel, and preview the generated SVG inline.  You can also POST directly to the `/generate` endpoint with form-data or JSON if you want to automate experiments.

## Running the app

1. **Install dependencies**
   ```bash
   pip install flask svgwrite pillow perlin-noise numpy pyyaml
   ```
2. **Start the development server**
   ```bash
   python app.py
   ```
   The app listens on <http://localhost:8000> by default.

Generated SVGs are written to the system temp directory and streamed back to the browser.  Uploaded heatmap files are stored under `uploads/` and referenced only for the current request.

## Deploying to Koyeb

The project is ready to run on the [Koyeb](https://www.koyeb.com/) serverless platform using Gunicorn.  A `Procfile` and `requirements.txt` are included so Koyeb's buildpack-based builder can install dependencies and boot the app with Gunicorn bound to the platform-provided `PORT`.

1. Fork this repository so you can connect it to your Koyeb account.
2. Visit the Koyeb Control Panel and click **Create Web Service**.
3. Choose **GitHub** as the deployment method and select your fork.
4. In the **Builder** section, override the run command with:
   ```bash
   gunicorn --bind 0.0.0.0:$PORT app:app
   ```
   (The provided `Procfile` contains the same command if you prefer to reference it.)
5. Pick a name for your App and Service, then click **Deploy**.

Once the deployment finishes building, the application will be available at `<YOUR_APP_NAME>-<YOUR_ORG_NAME>.koyeb.app`.

## Configuration surface

Configuration is loaded from `default_config.yaml` and deep-merged with any JSON provided under the `config` key of the `/generate` request.  You can pass overrides either as JSON in a POST body or by stringifying a JSON object inside `FormData` (which is what the web UI does).

### Request parameters

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `grid_size` | integer | `10` | Determines pixel spacing between grid points (also influences figure scale).
| `width` | integer | `1000` | Output SVG width in pixels.
| `height` | integer | `1000` | Output SVG height in pixels.
| `config` | JSON object | see below | Heatmap and figure options, merged with `default_config.yaml`.
| file uploads keyed by layer name (e.g. `grid`, `figure`) | file | — | Uploaded grayscale images replace the `file` path for the matching heatmap layer for this request.

### Grid appearance (`config.grid`)

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `dot_radius` | float | `1.5` | Controls the radius of each background dot.
| `dot_opacity` | float | `0.7` | Sets the opacity of dots (clamped in the UI between 0–1).
| `dot_color` | string | `#cccccc` | Fill colour applied to each dot.
| `lines.stroke_width` | float | `1.5` | Stroke width for the connective grid lines.
| `lines.stroke_color` | string | `#222222` | Stroke colour for the lines.
| `lines.opacity` | float | `0.8` | Opacity applied to the line strokes.
| `lines.center_probability` | float | `0.4` | Base probability of drawing a line near the centre of the canvas.
| `lines.edge_probability` | float | `0.05` | Line probability at the edges of the canvas.
| `lines.diagonal_bias` | float | `0.3` | Multiplier applied when considering diagonal connections.
| `lines.max_connections` | int | `2` | Caps how many connections any grid node may emit.

### Heatmap configuration (`config.heatmaps`)

Each heatmap layer supports both image-driven and Perlin-noise-driven density maps.  Modes control how the two sources blend.

| Layer | Option | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `grid` / `figure` | `file` | string | Path from `default_config.yaml` | Grayscale image used as a probability map (black = 0, white = 1).
| | `use_perlin` | boolean | `false` | Whether to multiply in a Perlin noise field.
| | `mode` | enum (`replace`, `add`, `multiply`) | `add` | Blend mode used when combining image and Perlin noise.
| | `perlin_scale` | float | `0.05` (`grid`), `0.06` (`figure`) | Spatial frequency used when generating Perlin noise.
| | `perlin_octaves` | integer | `3` (`grid`), `4` (`figure`) | Number of octaves for Perlin noise detail.
| `figure` only | `palettes` | list[str] | `[#E13A9D, #3F51B5, #000000, #f59e0b]` | Colors randomly sampled when drawing figure polygons.

#### Shape-specific heatmaps (`config.heatmaps.shapes`)

Any key added under `heatmaps.shapes` maps to a specific pose filename (e.g., `pose_standing.svg`).  Each entry supports:

- `file`: grayscale probability map
- `use_perlin`: boolean toggle
- `mode`: blend mode
- `perlin_scale`: float (optional; defaults to `0.05` if omitted)
- `perlin_octaves`: integer (optional; defaults to `3`)

These maps override the general `figure` layer whenever a matching pose is being placed.

### Figure settings (`config.figures`)

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `scale_factor` | float | `0.06` | Multiplied by `grid_size` to set pose polygon scale.
| `amount_figures` | int | `20` | Target number of silhouettes to place (the algorithm will make several attempts to hit this count).
| `tranparency_factor` | float | `0.8` | Opacity applied to the polygon fills (typo preserved for compatibility).
| `line_thickness` | float | `1.5` | Outline stroke width for the polygons; set to `0` for no outline.
| `line_color` | string | `#000000` | Stroke colour for the outlines.
| `line_opacity` | float | `0.8` | Stroke opacity for outlines.

## Fixed behavioural parameters

Some behaviours are currently hard-coded in `generator.py` and can be adjusted only by editing the source:

- **Figure placement** (`add_figures`):
  - Attempts up to `num_figures=40` silhouettes per render.
  - Uses `radius=3` cells when checking for overlapping figures.
  - Reads SVG poses from the `poses/` directory matching the pattern `pose_*.svg`.
- **Occupancy padding**: `SymbolicField.is_free` and `mark_used` use a default `radius=2` when tracking filled cells.
- **Heatmap normalization**: Perlin noise outputs are normalized to `[0, 1]` before blending with image heatmaps.

Adjust these defaults in code if you need finer control than the current UI or config file exposes.

## API summary

| Route | Method | Description |
| --- | --- | --- |
| `/` | GET | Serves the static single-page UI (`static/index.html`). |
| `/get_config` | GET | Returns the server-side default configuration (`default_config.yaml`) as JSON. |
| `/generate` | POST | Generates an SVG using posted dimensions, config overrides, and optional heatmap uploads. |

## Assets

- `maps/` contains example heatmap images referenced in the default config.
- `poses/` holds SVG pose silhouettes (`pose_*.svg`) that are randomly sampled during figure placement.
- `static/` provides the browser UI (HTML, CSS, JS).

This documentation should give you everything needed to run the app, tune the configuration surface, and understand the parameters that are currently hard-coded in the generator.
