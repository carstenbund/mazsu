from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os, tempfile, uuid, yaml, json
from generator import SymbolicField, add_grid_dots, add_random_lines, add_figures, load_config
import svgwrite

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ============================================================
# --- YAML + MERGE HELPERS -----------------------------------
# ============================================================

def load_yaml_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    return {}


def deep_merge(a, b):
    """Recursively merge dict b into dict a (b overwrites a where keys overlap)."""
    for k, v in b.items():
        if isinstance(v, dict) and k in a and isinstance(a[k], dict):
            deep_merge(a[k], v)
        else:
            a[k] = v
    return a


# ============================================================
# --- ROUTES -------------------------------------------------
# ============================================================

@app.route("/get_config")
def get_config():
    cfg = load_yaml_file("default_config.yaml")
    return jsonify(cfg)


@app.route("/generate", methods=["POST"])
def generate_svg():
    # --- Accept either form or JSON ---
    data = request.form or request.json or {}

    # --- Parse stringified JSON config if sent via FormData ---
    if "config" in data and isinstance(data.get("config"), str):
        try:
            data = data.copy()
            data["config"] = json.loads(data["config"])
        except Exception as e:
            print("Config JSON parse error:", e)
            data["config"] = {}

    # --- Merge with defaults ---
    cfg = load_yaml_file("default_config.yaml")
    user_cfg = data.get("config") if isinstance(data.get("config"), dict) else {}
    cfg = deep_merge(cfg, user_cfg)

    # --- Numeric fields ---
    grid_size = int(data.get("grid_size", 10))
    width = int(data.get("width", 1000))
    height = int(data.get("height", 1000))

    # --- Handle uploads (optional) ---
    uploaded_files = {}
    for key, file in request.files.items():
        if file and file.filename:
            fname = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{fname}")
            file.save(path)
            uploaded_files[key] = path

    for layer, section in cfg.get("heatmaps", {}).items():
        if layer in uploaded_files and isinstance(section, dict):
            section["file"] = uploaded_files[layer]

    # --- Generate SVG ---
    field = SymbolicField(
        cols=(width // grid_size) + 1,
        rows=(height // grid_size) + 1,
        grid_size=grid_size,
        config=cfg
    )

    out_svg = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4().hex}.svg")
    dwg = svgwrite.Drawing(out_svg, size=(f"{width}px", f"{height}px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))

    add_grid_dots(dwg, width, height, grid_size, radius=1, fill="#cccccc", cfg=cfg)
    add_random_lines(dwg, grid_size, width, height, field=field, cfg=cfg)
    add_figures(dwg, field, grid_size, width, height, poses_dir="poses", cfg=cfg)
    dwg.save()

    return send_file(out_svg, mimetype="image/svg+xml", as_attachment=False)


@app.route("/")
def index():
    return app.send_static_file("index.html")


# ============================================================
# --- MAIN ---------------------------------------------------
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, port=port, host="0.0.0.0")
