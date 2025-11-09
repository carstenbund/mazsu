from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os, tempfile, uuid, yaml, json
from pathlib import Path
from PIL import Image, ImageOps
from generator import SymbolicField, add_grid_dots, add_random_lines, add_figures, load_config
import svgwrite

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAPS_DIR = Path("maps")
MAPS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
    ".avif",
}

DEFAULT_CONFIG_PATH = "default_config.yaml"
ACTIVE_CONFIG_PATH = "active_config.yaml"

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ============================================================
# --- YAML + MERGE HELPERS -----------------------------------
# ============================================================

def load_yaml_file(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Failed to parse YAML from {path}: {exc}")
            return {}
        if isinstance(data, dict):
            return data
        return {}
    return {}


def write_yaml_file(path, data):
    """Atomically write YAML data to disk."""
    abs_path = os.path.abspath(path)
    target_dir = os.path.dirname(abs_path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix=".tmp_cfg_", suffix=".yaml")
    try:
        with os.fdopen(fd, "w") as tmp:
            yaml.safe_dump(data or {}, tmp, sort_keys=False)
        os.replace(tmp_path, abs_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def ensure_active_config():
    """Ensure the active config exists by seeding it from defaults if needed."""
    needs_seed = False
    if not os.path.exists(ACTIVE_CONFIG_PATH):
        needs_seed = True
    else:
        try:
            if os.path.getsize(ACTIVE_CONFIG_PATH) == 0:
                needs_seed = True
        except OSError:
            needs_seed = True

        if not needs_seed:
            cfg = load_yaml_file(ACTIVE_CONFIG_PATH)
            if not isinstance(cfg, dict) or not cfg:
                needs_seed = True

    if needs_seed:
        cfg = load_yaml_file(DEFAULT_CONFIG_PATH)
        write_yaml_file(ACTIVE_CONFIG_PATH, cfg or {})


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
    ensure_active_config()
    cfg = load_yaml_file(ACTIVE_CONFIG_PATH)
    return jsonify(cfg or {})


@app.route("/maps", methods=["GET"])
def list_maps():
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    maps = []
    for file_path in MAPS_DIR.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            continue
        try:
            rel_path = file_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = file_path
        label = file_path.stem.replace("_", " ").strip() or file_path.stem
        maps.append(
            {
                "name": label.title(),
                "path": str(rel_path).replace(os.sep, "/"),
            }
        )
    maps.sort(key=lambda item: item["name"].lower())
    return jsonify({"maps": maps})


@app.route("/upload_map", methods=["POST"])
def upload_map():
    if "map" not in request.files:
        return jsonify({"error": "No map file provided"}), 400

    file = request.files["map"]
    if file is None or file.filename == "":
        return jsonify({"error": "No map file provided"}), 400

    desired_name = request.form.get("name", "").strip()
    base_name = secure_filename(desired_name) or secure_filename(Path(file.filename).stem)
    if not base_name:
        base_name = f"map_{uuid.uuid4().hex[:8]}"

    output_name = f"{base_name}_{uuid.uuid4().hex[:8]}.png"
    output_path = MAPS_DIR / output_name

    try:
        with Image.open(file.stream) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("L")
            img = ImageOps.autocontrast(img)
            img.save(output_path, format="PNG")
    except Exception as exc:
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        return jsonify({"error": f"Failed to process map: {exc}"}), 400

    rel_path = output_path.relative_to(Path.cwd()) if output_path.is_absolute() else output_path
    rel_path_str = str(rel_path).replace(os.sep, "/")

    return jsonify({
        "status": "ok",
        "path": rel_path_str,
        "name": output_path.stem.replace("_", " ").title(),
    })


@app.route("/save_config", methods=["POST"])
def save_config():
    data = request.get_json(silent=True) or {}
    cfg = data.get("config")
    if not isinstance(cfg, dict):
        return jsonify({"error": "Invalid config payload"}), 400

    ensure_active_config()
    existing_cfg = load_yaml_file(ACTIVE_CONFIG_PATH)
    if not isinstance(existing_cfg, dict):
        existing_cfg = {}

    merged_cfg = deep_merge(existing_cfg, cfg)

    write_yaml_file(ACTIVE_CONFIG_PATH, merged_cfg)

    return jsonify({"status": "ok"})


@app.route("/get_defaults", methods=["POST"])
def get_defaults():
    cfg = load_yaml_file(DEFAULT_CONFIG_PATH)
    write_yaml_file(ACTIVE_CONFIG_PATH, cfg or {})
    return jsonify(cfg or {})


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
    ensure_active_config()
    cfg = load_yaml_file(ACTIVE_CONFIG_PATH)
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

    seed_value = None
    random_cfg = cfg.get("randomization")
    if isinstance(random_cfg, dict) and random_cfg.get("use_fixed_seed"):
        try:
            seed_candidate = random_cfg.get("seed")
            if seed_candidate is not None:
                seed_value = int(seed_candidate)
        except (TypeError, ValueError):
            seed_value = None

    # --- Generate SVG ---
    field = SymbolicField(
        cols=(width // grid_size) + 1,
        rows=(height // grid_size) + 1,
        grid_size=grid_size,
        config=cfg,
        seed=seed_value
    )

    out_svg = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4().hex}.svg")
    dwg = svgwrite.Drawing(out_svg, size=(f"{width}px", f"{height}px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))

    add_grid_dots(dwg, width, height, grid_size, radius=1, fill="#cccccc", cfg=cfg)
    add_random_lines(dwg, grid_size, width, height, field=field, cfg=cfg)
    add_figures(dwg, field, grid_size, width, height, poses_dir="poses", cfg=cfg)
    dwg.save()

    return send_file(out_svg, mimetype="image/svg+xml", as_attachment=False)


@app.route("/preview_heatmap")
def preview_heatmap():
    path = request.args.get("path", "")
    if not path:
        return "Missing path", 400

    base_dir = os.path.abspath(os.getcwd())
    abs_path = os.path.abspath(os.path.join(base_dir, path))

    if not abs_path.startswith(base_dir):
        return "Invalid path", 400

    if not os.path.isfile(abs_path):
        return "Heatmap not found", 404

    return send_file(abs_path)


@app.route("/")
def index():
    return app.send_static_file("index.html")


# ============================================================
# --- MAIN ---------------------------------------------------
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, port=port, host="0.0.0.0")
