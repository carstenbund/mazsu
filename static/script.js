let currentConfig = {};
let saveTimeout = null;
let pendingSavePromise = null;
let isApplyingConfig = false;

function cloneDeep(value) {
  if (value === null || value === undefined) return value;
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value));
}

const paletteList = document.getElementById("paletteList");
const addPaletteBtn = document.getElementById("addPaletteColor");
const seedCheckbox = document.getElementById("use_fixed_seed");
const seedInput = document.getElementById("seed_value");

function updateSeedInputState() {
  const isFixed = seedCheckbox.checked;
  seedInput.disabled = !isFixed;
  if (!isFixed) {
    seedInput.classList.remove("invalid");
  }
}

updateSeedInputState();

function normalizeColor(value) {
  if (!value) return null;
  let hex = value.trim();
  if (!hex) return null;
  hex = hex.startsWith("#") ? hex.slice(1) : hex;

  if (/^[0-9a-fA-F]{3}$/.test(hex)) {
    hex = hex
      .split("")
      .map((ch) => ch + ch)
      .join("");
  } else if (!/^[0-9a-fA-F]{6}$/.test(hex)) {
    return null;
  }

  return `#${hex.toUpperCase()}`;
}

function createPaletteItem(color = "#000000") {
  const normalized = normalizeColor(color) || "#000000";
  const item = document.createElement("div");
  item.className = "palette-item";

  const colorInput = document.createElement("input");
  colorInput.type = "color";
  colorInput.value = normalized;

  const textInput = document.createElement("input");
  textInput.type = "text";
  textInput.className = "palette-hex";
  textInput.value = normalized;

  colorInput.addEventListener("input", () => {
    textInput.value = colorInput.value.toUpperCase();
    textInput.classList.remove("invalid");
  });

  textInput.addEventListener("input", () => {
    const normalizedValue = normalizeColor(textInput.value);
    if (normalizedValue) {
      colorInput.value = normalizedValue;
      textInput.value = normalizedValue;
      textInput.classList.remove("invalid");
    } else {
      textInput.classList.add("invalid");
    }
  });

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "palette-remove";
  removeBtn.textContent = "Remove";
  removeBtn.addEventListener("click", () => {
    item.remove();
    if (!paletteList.querySelector(".palette-item")) {
      createPaletteItem();
    }
    scheduleConfigSave();
  });

  item.append(colorInput, textInput, removeBtn);
  paletteList.appendChild(item);

  return item;
}

function setPaletteColors(colors) {
  paletteList.innerHTML = "";
  const paletteArray = Array.isArray(colors) && colors.length ? colors : ["#000000"];
  paletteArray.forEach((color) => {
    createPaletteItem(color);
  });
}

function getPaletteColors() {
  const hexInputs = paletteList.querySelectorAll(".palette-hex");
  const colors = [];
  hexInputs.forEach((input) => {
    const normalized = normalizeColor(input.value);
    if (normalized) {
      colors.push(normalized);
    }
  });
  return colors.length ? colors : ["#000000"];
}

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

function applyConfig(config) {
  isApplyingConfig = true;
  try {
    currentConfig = config || {};

    const gridAppearance = currentConfig.grid || {};
    document.getElementById("grid_dot_radius").value = gridAppearance.dot_radius ?? "";
    document.getElementById("grid_dot_opacity").value = gridAppearance.dot_opacity ?? "";
    document.getElementById("grid_dot_color").value = gridAppearance.dot_color ?? "";

    const randomization = currentConfig.randomization || {};
    seedCheckbox.checked = !!randomization.use_fixed_seed;
    seedInput.value = randomization.seed ?? "";
    updateSeedInputState();

    const gridLines = gridAppearance.lines || {};
    document.getElementById("grid_line_width").value = gridLines.stroke_width ?? "";
    document.getElementById("grid_line_color").value = gridLines.stroke_color ?? "";
    document.getElementById("grid_line_opacity").value = gridLines.opacity ?? "";
    document.getElementById("grid_line_center_probability").value = gridLines.center_probability ?? "";
    document.getElementById("grid_line_edge_probability").value = gridLines.edge_probability ?? "";
    document.getElementById("grid_line_diagonal_bias").value = gridLines.diagonal_bias ?? "";
    document.getElementById("grid_line_max_connections").value = gridLines.max_connections ?? "";

    const heatmaps = currentConfig.heatmaps || {};
    const gridHeatmap = heatmaps.grid || {};
    document.getElementById("grid_file").value = gridHeatmap.file ?? "";
    document.getElementById("grid_use_perlin").checked = !!gridHeatmap.use_perlin;
    document.getElementById("grid_mode").value = gridHeatmap.mode || "add";
    document.getElementById("grid_scale").value = gridHeatmap.perlin_scale ?? "";
    document.getElementById("grid_octaves").value = gridHeatmap.perlin_octaves ?? "";

    const figureHeatmap = heatmaps.figure || {};
    document.getElementById("figure_file").value = figureHeatmap.file ?? "";
    document.getElementById("figure_use_perlin").checked = !!figureHeatmap.use_perlin;
    document.getElementById("figure_mode").value = figureHeatmap.mode || "add";
    document.getElementById("figure_scale").value = figureHeatmap.perlin_scale ?? "";
    document.getElementById("figure_octaves").value = figureHeatmap.perlin_octaves ?? "";
    setPaletteColors(figureHeatmap.palettes);

    const figureSettings = currentConfig.figures || {};
    document.getElementById("figure_scale_factor").value = figureSettings.scale_factor ?? "";
    document.getElementById("figure_amount").value = figureSettings.amount_figures ?? "";
    document.getElementById("figure_transparency").value = figureSettings.tranparency_factor ?? "";
    document.getElementById("figure_line_thickness").value = figureSettings.line_thickness ?? "";
    document.getElementById("figure_line_color").value = figureSettings.line_color ?? "";
    document.getElementById("figure_line_opacity").value = figureSettings.line_opacity ?? "";
  } finally {
    isApplyingConfig = false;
  }
}

async function loadConfig() {
  const res = await fetch("/get_config");
  const cfg = await res.json();
  applyConfig(cfg);
}

window.addEventListener("DOMContentLoaded", loadConfig);

function collectConfigFromForm() {
  const shapes = currentConfig?.heatmaps?.shapes;
  const config = {
    randomization: {
      use_fixed_seed: seedCheckbox.checked,
      seed: readNumber("seed_value", parseInt)
    },
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
        file: readText("grid_file"),
        use_perlin: document.getElementById("grid_use_perlin").checked,
        mode: document.getElementById("grid_mode").value,
        perlin_scale: readNumber("grid_scale"),
        perlin_octaves: readNumber("grid_octaves", parseInt)
      },
      figure: {
        file: readText("figure_file"),
        use_perlin: document.getElementById("figure_use_perlin").checked,
        mode: document.getElementById("figure_mode").value,
        perlin_scale: readNumber("figure_scale"),
        perlin_octaves: readNumber("figure_octaves", parseInt),
        palettes: getPaletteColors()
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

  if (shapes && typeof shapes === "object") {
    config.heatmaps = config.heatmaps || {};
    config.heatmaps.shapes = cloneDeep(shapes);
  }

  return config;
}

async function saveConfig() {
  const config = collectConfigFromForm();
  currentConfig = config;
  try {
    const response = await fetch("/save_config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config })
    });
    if (!response.ok) {
      throw new Error("Failed to save config");
    }
  } catch (err) {
    console.error(err);
  }
  return config;
}

function scheduleConfigSave() {
  if (isApplyingConfig) return;
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  saveTimeout = setTimeout(() => {
    saveTimeout = null;
    pendingSavePromise = saveConfig().finally(() => {
      pendingSavePromise = null;
    });
  }, 400);
}

async function flushPendingSave() {
  if (saveTimeout) {
    clearTimeout(saveTimeout);
    saveTimeout = null;
    pendingSavePromise = saveConfig().finally(() => {
      pendingSavePromise = null;
    });
  }
  if (pendingSavePromise) {
    await pendingSavePromise;
  }
}

async function loadDefaults() {
  try {
    if (saveTimeout) {
      clearTimeout(saveTimeout);
      saveTimeout = null;
    }
    if (pendingSavePromise) {
      await pendingSavePromise;
    }
    const response = await fetch("/get_defaults", { method: "POST" });
    if (!response.ok) {
      throw new Error("Failed to load defaults");
    }
    const cfg = await response.json();
    applyConfig(cfg);
  } catch (err) {
    console.error(err);
    alert("Unable to load defaults");
  }
}

// --- Toggle / collapse setup ---
const toggleBtn = document.getElementById('toggleConfig');
const configContainer = document.getElementById('configContainer');
const preview = document.getElementById('preview');
const downloadBtn = document.getElementById('downloadBtn');
let currentSvgBlob = null;
let previewUrl = null;

function openHeatmapPreview(targetId) {
  const input = document.getElementById(targetId);
  if (!input) return;

  const value = input.value.trim();
  if (!value) {
    alert('Please enter a heatmap file path to preview.');
    return;
  }

  const previewWindowUrl = `/preview_heatmap?path=${encodeURIComponent(value)}`;
  window.open(previewWindowUrl, '_blank', 'noopener=yes,width=800,height=600');
}

document.querySelectorAll('.preview-heatmap').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetId = btn.getAttribute('data-target');
    openHeatmapPreview(targetId);
  });
});

toggleBtn.addEventListener('click', () => {
  configContainer.classList.toggle('collapsed');
});

// --- Single unified generator ---
async function generate() {
  // Collapse UI while generating
  configContainer.classList.add('collapsed');
  downloadBtn.disabled = true;

  await flushPendingSave();

  const cfg = collectConfigFromForm();

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
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    previewUrl = URL.createObjectURL(svgBlob);
    preview.src = previewUrl;
    currentSvgBlob = svgBlob;
    downloadBtn.disabled = false;

  } catch (err) {
    alert(err.message);
    configContainer.classList.remove('collapsed');
    downloadBtn.disabled = !currentSvgBlob;
  }
}

function downloadSVG() {
  if (!currentSvgBlob) return;

  const downloadUrl = URL.createObjectURL(currentSvgBlob);
  const anchor = document.createElement('a');
  anchor.href = downloadUrl;
  anchor.download = 'symbolic-field.svg';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(downloadUrl);
}

downloadBtn.addEventListener('click', downloadSVG);

// --- Optional: re-expand config on edit ---
document.getElementById("configForm").addEventListener("input", () => {
  configContainer.classList.remove('collapsed');
  scheduleConfigSave();
});

seedCheckbox.addEventListener("change", () => {
  updateSeedInputState();
  scheduleConfigSave();
});

addPaletteBtn.addEventListener("click", () => {
  createPaletteItem();
  scheduleConfigSave();
});

document.getElementById("getDefaultsBtn")?.addEventListener("click", loadDefaults);
