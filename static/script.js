let currentConfig = {};

async function loadConfig() {
  const res = await fetch("/get_config");
  currentConfig = await res.json();

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

  document.getElementById("figure_scale_factor").value = currentConfig.figures.scale_factor;
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
      scale_factor: parseFloat(document.getElementById("figure_scale_factor").value)
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
