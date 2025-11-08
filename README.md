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

## Configuring the generator in the web app

Mazsu now persists your tweaks directly from the UI.  When the page loads it reads `active_config.yaml` (created on first run from `default_config.yaml`), fills the form controls, and automatically saves any edits back to `active_config.yaml`.  Generations pull from those saved values unless you explicitly override them in the current request.

### Global settings

The **Global Settings** section controls the SVG canvas:

- **Grid Size** – spacing between grid points (also influences figure scale).
- **Width / Height** – output dimensions in pixels.

These values are sent alongside the configuration JSON whenever you click **Generate SVG**.

### Heatmap controls

Both the grid and figure layers expose the same knobs:

- **File** – a grayscale image path relative to the project root.  Use the **Preview** button to open the map in a new tab.
- **Use Perlin** – toggles whether Perlin noise is blended into the layer.
- **Mode** – chooses how the image and noise combine (`replace`, `add`, or `multiply`).
- **Perlin Scale / Octaves** – adjust the noise frequency and detail level.

The figure layer additionally offers a palette editor.  You can add or remove colours, edit them as hex codes, or use the colour picker inputs; the list is saved with the rest of the config.

### Grid appearance

The **Grid Appearance** section lets you refine the dot layer and connective lines without touching YAML:

- Dot radius, opacity, and colour.
- Line stroke width, colour, opacity.
- Line placement probabilities for the centre vs. edges, a diagonal bias, and the maximum connections per node.

### Figure rendering

Figure-specific sliders match the options in `config.figures`:

- Scale factor used to size pose silhouettes relative to the grid.
- Target count of figures to place.
- Fill transparency (typo `tranparency_factor` preserved in config).
- Outline stroke thickness, colour, and opacity.

### Saving and defaults

The form auto-saves after short inactivity.  Use **Get Defaults** to restore `default_config.yaml` into `active_config.yaml` if you want a clean slate.

### Advanced / not yet implemented controls

Some options remain editable only by hand in `default_config.yaml` / `active_config.yaml` or the Python source:

- **Shape-specific heatmaps** under `heatmaps.shapes` (per-pose masks and noise blends) – not yet surfaced in the UI.
- **Generator internals** such as extra placement attempts, occupancy padding, and Perlin normalization – still hard-coded in `generator.py` (see the next section).

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
