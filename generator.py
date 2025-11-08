#!/usr/bin/env python3

import svgwrite, random, math, yaml
import numpy as np
import xml.etree.ElementTree as ET # <-- Added this import
from pathlib import Path
from PIL import Image, ImageOps # <-- Added this import
from perlin_noise import PerlinNoise


# ============================================================
# --- CONFIGURATION LOADER -----------------------------------
# ============================================================

def load_config(path="config_heatmaps.yaml"):
    if Path(path).exists():
        with open(path, "r") as f:
            return yaml.safe_load(f)
    print(f"Warning: Config file {path} not found. Using defaults.")
    return {}


# ============================================================
# --- SYMBOLIC FIELD CORE ------------------------------------
# ============================================================

class SymbolicField:
    def __init__(self, cols, rows, grid_size, config=None, seed=None):
        self.cols, self.rows, self.grid_size = cols, rows, grid_size
        self.seed = seed or np.random.randint(1e6)
        self.occupancy = np.zeros((rows, cols), dtype=np.uint8)
        self.connections = np.zeros((rows, cols), dtype=np.uint8)
        self.shape_fields = {}
        
        if config:
            self._load_from_config(config)
        else:
            # default perlin fields if no config is present
            print("No config, generating default Perlin fields.")
            self.grid_density = self._generate_perlin(0.05, 3)
            self.figure_density = self._generate_perlin(0.06, 3)
            
    # --- Field generation and combination ---
    def _generate_perlin(self, scale, octaves):
        noise = PerlinNoise(octaves=octaves, seed=self.seed)
        field = np.zeros((self.rows, self.cols), dtype=np.float32)
        for y in range(self.rows):
            for x in range(self.cols):
                field[y, x] = noise([x * scale, y * scale])
        field = (field - field.min()) / (field.max() - field.min())
        return field
    
    def _load_gray(self, path):
        if not path:
            return None
        p = Path(path)
        if not p.exists():
            print(f"Warning: Heatmap file not found: {path}")
            return None
        
        try:
            img = Image.open(path).convert("L").resize((self.cols, self.rows), Image.Resampling.LANCZOS)
            # Black (0) = 0.0, White (255) = 1.0
            return np.array(img, dtype=np.float32) / 255.0
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    
    def _combine(self, a, b, mode):
        if a is None: return b
        if b is None: return a
        if mode == "replace": return b
        if mode == "add": return np.clip(a + b, 0, 1)
        if mode == "multiply": return np.clip(a * b, 0, 1)
        return a # Default to 'a' (image) if mode is unknown
    
    def _load_from_config(self, cfg):
        hm = cfg.get("heatmaps", {})
        
        # grid
        g = hm.get("grid", {})
        print("Loading 'grid' heatmap...")
        perlin_grid = self._generate_perlin(g.get("perlin_scale", 0.05),
                                            g.get("perlin_octaves", 3)) if g.get("use_perlin", False) else None
        grid_file = self._load_gray(g.get("file"))
        self.grid_density = self._combine(grid_file, perlin_grid, g.get("mode", "replace"))
        if self.grid_density is None: self.grid_density = np.ones((self.rows, self.cols), dtype=np.float32) # Fallback

        
        # figure
        f = hm.get("figure", {})
        print("Loading 'figure' heatmap...")
        perlin_fig = self._generate_perlin(f.get("perlin_scale", 0.06),
                                            f.get("perlin_octaves", 4)) if f.get("use_perlin", False) else None
        fig_file = self._load_gray(f.get("file"))
        self.figure_density = self._combine(fig_file, perlin_fig, f.get("mode", "replace"))
        if self.figure_density is None: self.figure_density = np.ones((self.rows, self.cols), dtype=np.float32) # Fallback
        
        # shape-specific
        for shape, params in hm.get("shapes", {}).items():
            print(f"Loading '{shape}' heatmap...")
            filemap = self._load_gray(params.get("file"))
            perlinmap = self._generate_perlin(params.get("perlin_scale", 0.05),
                                                params.get("perlin_octaves", 3)) if params.get("use_perlin", False) else None
            self.shape_fields[shape] = self._combine(perlinmap, filemap, params.get("mode", "replace"))
            
    # --- Field Access Utilities ---
    def get_probability(self, col, row, layer="figure", shape=None):
        if col >= self.cols or row >= self.rows: return 0.0 # Safety check
        
        if layer == "grid":
            return self.grid_density[row, col]
        elif layer == "figure":
            if shape and shape in self.shape_fields:
                # Use shape-specific map if it exists
                return self.shape_fields[shape][row, col]
            # Otherwise, use the general figure map
            return self.figure_density[row, col]
        return 0.0
    
    def is_free(self, col, row, radius=2):
        rmin, rmax = max(0, row - radius), min(self.rows, row + radius + 1)
        cmin, cmax = max(0, col - radius), min(self.cols, col + radius + 1)
        return not self.occupancy[rmin:rmax, cmin:cmax].any()
    
    def mark_used(self, col, row, radius=2):
        rmin, rmax = max(0, row - radius), min(self.rows, row + radius + 1)
        cmin, cmax = max(0, col - radius), min(self.cols, col + radius + 1)
        self.occupancy[rmin:rmax, cmin:cmax] = 1
        
        
# ============================================================
# --- DRAWING UTILITIES --------------------------------------
# ============================================================
        
def get_pixel(grid_coord, grid_size):
    col, row = grid_coord
    return (col * grid_size, row * grid_size)

# --- THIS IS THE MISSING FUNCTION ---
def add_grid_dots(
    dwg,
    width,
    height,
    grid_size,
    radius=1,
    fill="#cccccc",
    cfg=None,
):
    """Adds the background dot grid."""
    print("Adding grid dots...")

    cfg = cfg or {}
    grid_cfg = cfg.get("grid", {})
    radius = grid_cfg.get("dot_radius", radius)
    fill = grid_cfg.get("dot_color", fill)
    dot_opacity = grid_cfg.get("dot_opacity", 1.0)

    def _safe_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    radius = _safe_float(radius, 1)
    dot_opacity = _safe_float(dot_opacity, 1.0)

    for x in range(0, width + 1, grid_size):
        for y in range(0, height + 1, grid_size):
            dwg.add(
                dwg.circle(
                    center=(x, y),
                    r=radius,
                    fill=fill,
                    fill_opacity=dot_opacity,
                )
            )
    print("Dots added.")


# ============================================================
# --- GRID GENERATION ----------------------------------------
# ============================================================

def calculate_spatial_probability(col, row, max_col, max_row, center_prob, edge_prob):
    """Radial probability falloff for base grid generation."""
    center_x, center_y = max_col / 2, max_row / 2
    dist = math.sqrt((col - center_x) ** 2 + (row - center_y) ** 2)
    max_dist = math.sqrt(center_x ** 2 + center_y ** 2)
    if max_dist == 0: return center_prob # Avoid divide by zero
    norm = dist / max_dist
    bias = max(0, 1.0 - norm)
    return (edge_prob * (1.0 - bias)) + (center_prob * bias)


def add_random_lines(
    dwg,
    grid_size,
    width,
    height,
    center_prob=0.4,
    edge_prob=0.05,
    diagonal_bias=0.3,
    max_connections=2,
    field=None,
    cfg=None,
):
    """Draws random grid lines with optional heatmap modulation."""
    print("Adding limited random lines...")
    max_col = width // grid_size
    max_row = height // grid_size

    cfg = cfg or {}
    grid_cfg = cfg.get("grid", {})
    line_cfg = grid_cfg.get("lines", {})

    def _safe_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    center_prob = _safe_float(line_cfg.get("center_probability", center_prob), center_prob)
    edge_prob = _safe_float(line_cfg.get("edge_probability", edge_prob), edge_prob)
    diagonal_bias = _safe_float(line_cfg.get("diagonal_bias", diagonal_bias), diagonal_bias)
    max_connections = _safe_int(line_cfg.get("max_connections", max_connections), max_connections)

    line_style = {
        "stroke": line_cfg.get("stroke_color", "black"),
        "stroke_width": _safe_float(line_cfg.get("stroke_width", 1), 1),
        "stroke_opacity": _safe_float(line_cfg.get("opacity", 1.0), 1.0),
    }
    
    connection_counts = [[0 for _ in range(max_row + 1)] for _ in range(max_col + 1)]
    
    for col in range(max_col + 1): # <-- Fixed loop to include last column/row
        for row in range(max_row + 1): # <-- Fixed loop
            
            # Use radial prob as a base
            base_prob = calculate_spatial_probability(col, row, max_col, max_row, center_prob, edge_prob)
            
            # Modulate by the 'grid' heatmap
            if field is not None:
                heatmap_prob = field.get_probability(col, row, layer="grid")
                base_prob *= heatmap_prob # Multiply radial by heatmap
                
            diag_prob = base_prob * diagonal_bias
            p_start = get_pixel((col, row), grid_size)
            
            # Horizontal (E)
            if col < max_col: # Check bounds
                if connection_counts[col][row] < max_connections and connection_counts[col + 1][row] < max_connections:
                    if random.random() < base_prob:
                        p_end = get_pixel((col + 1, row), grid_size)
                        dwg.add(dwg.line(p_start, p_end, **line_style))
                        connection_counts[col][row] += 1
                        connection_counts[col + 1][row] += 1
                    
            # Vertical (S)
            if row < max_row: # Check bounds
                if connection_counts[col][row] < max_connections and connection_counts[col][row + 1] < max_connections:
                    if random.random() < base_prob:
                        p_end = get_pixel((col, row + 1), grid_size)
                        dwg.add(dwg.line(p_start, p_end, **line_style))
                        connection_counts[col][row] += 1
                        connection_counts[col][row + 1] += 1
                    
            # Diagonal SE
            if col < max_col and row < max_row: # Check bounds
                if connection_counts[col][row] < max_connections and connection_counts[col + 1][row + 1] < max_connections:
                    if random.random() < diag_prob:
                        p_end = get_pixel((col + 1, row + 1), grid_size)
                        dwg.add(dwg.line(p_start, p_end, **line_style))
                        connection_counts[col][row] += 1
                        connection_counts[col + 1][row + 1] += 1
                    
            # Diagonal NE
            if col < max_col and row > 0: # Check bounds
                if connection_counts[col][row] < max_connections and connection_counts[col + 1][row - 1] < max_connections:
                    if random.random() < diag_prob:
                        p_end = get_pixel((col + 1, row - 1), grid_size)
                        dwg.add(dwg.line(p_start, p_end, **line_style))
                        connection_counts[col][row] += 1
                        connection_counts[col + 1][row - 1] += 1
                    
    print("Lines added.")
    
    
# ============================================================
# --- FIGURE PLACEMENT ---------------------------------------
# ============================================================
    
def add_figures(
    dwg,
    field,
    grid_size,
    width,
    height,
    poses_dir,
    num_figures=40,
    radius=3,
    cfg=None,
):
    
    pose_files = list(Path(poses_dir).glob("pose_*.svg"))
    if not pose_files:
        print("⚠ No poses found in", poses_dir)
        return

    max_col, max_row = width // grid_size, height // grid_size
    
    # Get figure config section
    cfg = cfg or {}
    fig_cfg = cfg.get("heatmaps", {}).get("figure", {})
    # Load scale factor from config
    figure_settings = cfg.get("figures", {})
    scale_factor = figure_settings.get("scale_factor", 0.08)
    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _safe_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    num_figures = _safe_int(figure_settings.get("amount_figures", num_figures), num_figures)
    figure_opacity = _safe_float(figure_settings.get("tranparency_factor", 1.0), 1.0)
    outline_thickness = _safe_float(figure_settings.get("line_thickness", 0), 0)
    outline_color = figure_settings.get("line_color", "#000000")
    outline_opacity = _safe_float(figure_settings.get("line_opacity", figure_opacity), figure_opacity)
    figure_scale = grid_size * scale_factor
    
    # Load palettes from config, default to black
    palettes = fig_cfg.get("palettes", ["#000000"])
    placed_count = 0
    # Try more times than num_figures to account for random misses
    for _ in range(num_figures * 10): 
        if placed_count >= num_figures: break

        shape_file = random.choice(pose_files)
        # Get shape name, e.g., 'standing' from 'pose_standing.svg'
        shape_name = shape_file.stem.replace("pose_", "")
        
        col, row = random.randint(0, max_col), random.randint(0, max_row)
        
        # Get probability from the field, checking for shape-specific maps
        prob = field.get_probability(col, row, "figure", shape_name)
        
        if random.random() > prob or not field.is_free(col, row, radius):
            continue
        
        try:
            root = ET.parse(shape_file).getroot()
            pts = []
            for poly in root.findall(".//{http://www.w3.org/2000/svg}polygon"):
                pts += [tuple(map(float, p.split(","))) for p in poly.attrib["points"].split()]
            
            if not pts:
                print(f"Warning: No polygon points found in {shape_file}")
                continue

        except Exception as e:
            print(f"Error parsing SVG {shape_file}: {e}")
            continue

        ox, oy = get_pixel((col, row), grid_size)
        
        # Normalize points (some SVGs might not start at 0,0)
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        pts = [(x - min_x, y - min_y) for x, y in pts]

        # Apply scaling and the initially requested offset.  This "optimal" position
        # (decided earlier by the probability field) is kept intact before we worry
        # about nudging the outline onto the dot grid.
        pts = [(x * figure_scale + ox, y * figure_scale + oy) for x, y in pts]

        # Once we know where the figure actually landed we can gently snap its outer
        # boundary to the nearest grid dot.  Doing this after the optimal placement
        # has been calculated means we only introduce a minimal adjustment while the
        # outline still aligns perfectly with the grid.
        min_px = min(x for x, _ in pts)
        max_px = max(x for x, _ in pts)
        min_py = min(y for _, y in pts)
        max_py = max(y for _, y in pts)

        bbox_width = max_px - min_px
        bbox_height = max_py - min_py

        def snap_min(value):
            return round(value / grid_size) * grid_size

        snapped_min_x = snap_min(min_px)
        snapped_min_y = snap_min(min_py)

        max_origin_x = max(0, width - bbox_width)
        max_origin_y = max(0, height - bbox_height)

        snapped_min_x = min(max(snapped_min_x, 0), max_origin_x)
        snapped_min_y = min(max(snapped_min_y, 0), max_origin_y)

        dx = snapped_min_x - min_px
        dy = snapped_min_y - min_py

        pts = [(x + dx, y + dy) for x, y in pts]
        
        # --- APPLY RANDOM COLOR ---
        color = random.choice(palettes)
        #print("color: ", color)
        polygon_kwargs = {
            "points": pts,
            "fill": color,
            "fill_opacity": figure_opacity,
        }

        if outline_thickness and outline_thickness > 0:
            polygon_kwargs.update(
                {
                    "stroke": outline_color,
                    "stroke_width": outline_thickness,
                    "stroke_opacity": outline_opacity,
                }
            )

        dwg.add(dwg.polygon(**polygon_kwargs))
        # --------------------------
        
        field.mark_used(col, row, radius)
        placed_count += 1
        
    print(f"Placed {placed_count} figures (tried for {num_figures}).")
    
    
# ============================================================
# --- MAIN ---------------------------------------------------
# ============================================================
    
if __name__ == "__main__":
    GRID_SIZE = 10
    WIDTH, HEIGHT = 1000, 1000
    CONFIG_FILE = "config.yaml"
    OUT_FILE = "grid_figures_out.svg"
    
    cfg = load_config(CONFIG_FILE)
    
    # You can override config values here if needed
    # GRID_SIZE = cfg.get("main", {}).get("grid_size", GRID_SIZE)
    # WIDTH = cfg.get("main", {}).get("width", WIDTH)
    # HEIGHT = cfg.get("main", {}).get("height", HEIGHT)

    
    field = SymbolicField(cols=(WIDTH // GRID_SIZE) + 1, # +1 to include edges
                            rows=(HEIGHT // GRID_SIZE) + 1,
                            grid_size=GRID_SIZE, config=cfg)
    
    dwg = svgwrite.Drawing(OUT_FILE, size=(f"{WIDTH}px", f"{HEIGHT}px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))
    
    # --- HERE IS THE FIX ---
    # 1. Add the dots first
    add_grid_dots(dwg, WIDTH, HEIGHT, GRID_SIZE, radius=1, fill="#cccccc", cfg=cfg)

    # 2. Add the random lines
    # These settings are now the 'base' which gets multiplied by the heatmap
    add_random_lines(dwg, GRID_SIZE, WIDTH, HEIGHT,
                    center_prob=0.8, edge_prob=0.1, # Base radial gradient
                    diagonal_bias=0.3, max_connections=2,
                    field=field, cfg=cfg)

    # 3. Add the figures
    add_figures(dwg, field, GRID_SIZE, WIDTH, HEIGHT,
                poses_dir="poses", num_figures=50, radius=3, cfg=cfg)
    
    dwg.save()
    print(f"Output saved to {OUT_FILE}")