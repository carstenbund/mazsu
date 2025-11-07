let currentConfig = {};

function readNumber(id, parser = parseFloat) {
  const raw = document.getElementById(id).value;
  if (raw === "") return undefined;
  const parsed = parser(raw);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function readText(id) {
  const value = document.getElementById(id).value.trim();
  return value === "" ? undefined : value;
}

async function loadConfig() {
  const res = await fetch("/get_config");
  currentConfig = await res.json();

  const gridAppearance = currentConfig.grid || {};
  document.getElementById("grid_dot_radius").value = gridAppearance.dot_radius ?? "";
  document.getElementById("grid_dot_opacity").value = gridAppearance.dot_opacity ?? "";
  document.getElementById("grid_dot_color").value = gridAppearance.dot_color ?? "";

  const gridLines = gridAppearance.lines || {};
  document.getElementById("grid_line_width").value = gridLines.stroke_width ?? "";
  document.getElementById("grid_line_color").value = gridLines.stroke_color ?? "";
  document.getElementById("grid_line_opacity").value = gridLines.opacity ?? "";
  document.getElementById("grid_line_center_probability").value = gridLines.center_probability ?? "";
  document.getElementById("grid_line_edge_probability").value = gridLines.edge_probability ?? "";
  document.getElementById("grid_line_diagonal_bias").value = gridLines.diagonal_bias ?? "";
  document.getElementById("grid_line_max_connections").value = gridLines.max_connections ?? "";

  const grid = currentConfig.heatmaps.grid;
  document.getElementById("grid_file").value = grid.file || "";
  document.getElementById("grid_use_perlin").checked = grid.use_perlin;
  document.getElementById("grid_mode").value = grid.mode;
  document.getElementById("grid_scale").value = grid.perlin_scale;
  document.getElementById("grid_octaves").value = grid.perlin_octaves;

  const figure = currentConfig.heatmaps.figure;
  document.getElementById("figure_file").value = figure.file || "";
  document.getElementById("figure_use_perlin").checked = figure.use_perlin;
  document.getElementById("figure_mode").value = figure.mode;
  document.getElementById("figure_scale").value = figure.perlin_scale;
  document.getElementById("figure_octaves").value = figure.perlin_octaves;
  document.getElementById("figure_palettes").value = figure.palettes.join(", ");

  const figureSettings = currentConfig.figures || {};
  document.getElementById("figure_scale_factor").value = figureSettings.scale_factor ?? "";
  document.getElementById("figure_amount").value = figureSettings.amount_figures ?? "";
  document.getElementById("figure_transparency").value = figureSettings.tranparency_factor ?? "";
  document.getElementById("figure_line_thickness").value = figureSettings.line_thickness ?? "";
  document.getElementById("figure_line_color").value = figureSettings.line_color ?? "";
  document.getElementById("figure_line_opacity").value = figureSettings.line_opacity ?? "";
}

window.addEventListener("DOMContentLoaded", loadConfig);

// --- Toggle / collapse setup ---
const toggleBtn = document.getElementById('toggleConfig');
const configContainer = document.getElementById('configContainer');
const preview = document.getElementById('preview');

toggleBtn.addEventListener('click', () => {
  configContainer.classList.toggle('collapsed');
});

// --- Single unified generator ---
async function generate() {
  // Collapse UI while generating
  configContainer.classList.add('collapsed');

  const cfg = {
    grid: {
      dot_radius: readNumber("grid_dot_radius"),
      dot_opacity: readNumber("grid_dot_opacity"),
      dot_color: readText("grid_dot_color"),
      lines: {
        stroke_width: readNumber("grid_line_width"),
        stroke_color: readText("grid_line_color"),
        opacity: readNumber("grid_line_opacity"),
        center_probability: readNumber("grid_line_center_probability"),
        edge_probability: readNumber("grid_line_edge_probability"),
        diagonal_bias: readNumber("grid_line_diagonal_bias"),
        max_connections: readNumber("grid_line_max_connections", parseInt)
      }
    },
    heatmaps: {
      grid: {
        file: document.getElementById("grid_file").value,
        use_perlin: document.getElementById("grid_use_perlin").checked,
        mode: document.getElementById("grid_mode").value,
        perlin_scale: parseFloat(document.getElementById("grid_scale").value),
        perlin_octaves: parseInt(document.getElementById("grid_octaves").value)
      },
      figure: {
        file: document.getElementById("figure_file").value,
        use_perlin: document.getElementById("figure_use_perlin").checked,
        mode: document.getElementById("figure_mode").value,
        perlin_scale: parseFloat(document.getElementById("figure_scale").value),
        perlin_octaves: parseInt(document.getElementById("figure_octaves").value),
        palettes: document.getElementById("figure_palettes").value.split(",").map(s => s.trim())
      }
    },
    figures: {
      scale_factor: readNumber("figure_scale_factor"),
      amount_figures: readNumber("figure_amount", parseInt),
      tranparency_factor: readNumber("figure_transparency"),
      line_thickness: readNumber("figure_line_thickness"),
      line_color: readText("figure_line_color"),
      line_opacity: readNumber("figure_line_opacity")
    }
  };

  const formData = new FormData();
  formData.append("config", JSON.stringify(cfg));
  formData.append("grid_size", document.getElementById("grid_size").value);
  formData.append("width", document.getElementById("width").value);
  formData.append("height", document.getElementById("height").value);

  try {
    const response = await fetch("/generate", {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("Generation failed");

    const svgBlob = await response.blob();
    const url = URL.createObjectURL(svgBlob);
    preview.src = url;

  } catch (err) {
    alert(err.message);
    configContainer.classList.remove('collapsed');
  }
}

// --- Optional: re-expand config on edit ---
document.getElementById("configForm").addEventListener("input", () => {
  configContainer.classList.remove('collapsed');
});
