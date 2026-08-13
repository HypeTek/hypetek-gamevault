const state = {games: [], query: "", filter: "all", settings: null};
const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
const labels = {direct_setup: "Direktes Setup", iso: "ISO", manual: "Manuell", archive: "Archiv", manual_image: "Sonderabbild", ignore: "Ausgeblendet"};
const library = document.querySelector("#library");
const statusEl = document.querySelector("#status");
const editor = document.querySelector("#editor");
const settingsDialog = document.querySelector("#settingsDialog");

const formatBytes = (value) => {
  if (!value) return "0 B";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let index = 0;
  let amount = value;
  while (amount >= 1024 && index < units.length - 1) { amount /= 1024; index += 1; }
  return `${amount.toFixed(index > 2 ? 2 : 1)} ${units[index]}`;
};

async function api(url, options = {}) {
  const headers = {"Content-Type": "application/json", ...(options.headers || {})};
  if ((options.method || "GET").toUpperCase() !== "GET") headers["X-CSRF-Token"] = csrf;
  const response = await fetch(url, {...options, headers});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function applySettings(settings) {
  state.settings = settings;
  document.body.dataset.theme = settings.theme;
  document.body.classList.toggle("crosshair", Boolean(settings.crosshair_cursor));
  document.body.style.setProperty("--custom-background", settings.background_url ? `url("${settings.background_url}")` : "none");
  document.body.style.setProperty("--background-opacity", settings.background_opacity);
  document.body.style.setProperty("--background-blur", `${settings.background_blur}px`);
  document.querySelector("#libraryName").textContent = settings.library_name;
  document.title = `HypeTek Mission Control · ${settings.server_name}`;
}

async function load() {
  statusEl.textContent = "Lade …";
  const [games, settings] = await Promise.all([api("/api/games"), api("/api/settings")]);
  state.games = games;
  applySettings(settings);
  statusEl.textContent = "";
  render();
}

function actionLabel(game) {
  if (game.action === "direct_setup") return "Installieren";
  if (game.action === "iso") return "Einbinden & installieren";
  return "Manuelle Installation";
}

function render() {
  const query = state.query.toLocaleLowerCase("de");
  const games = state.games.filter((game) =>
    (state.filter === "all" || game.action === state.filter) &&
    `${game.title} ${game.platform} ${game.relative_path}`.toLocaleLowerCase("de").includes(query));
  const counts = state.games.reduce((result, game) => {
    result[game.action] = (result[game.action] || 0) + 1;
    return result;
  }, {});
  document.querySelector("#stats").innerHTML =
    `<div class="stat"><strong>${state.games.length}</strong>Einträge</div>` +
    `<div class="stat"><strong>${counts.direct_setup || 0}</strong>Setups</div>` +
    `<div class="stat"><strong>${counts.iso || 0}</strong>ISOs</div>`;
  library.innerHTML = games.map((game) => {
    const launchable = ["direct_setup", "iso"].includes(game.action) && game.launcher;
    const cover = game.cover_name ? `background-image:url('/covers/${encodeURIComponent(game.cover_name)}')` : "";
    return `<article class="card"><div class="cover" style="${cover}"><div class="cover-title">${escapeHtml(game.title)}</div></div><div class="card-body"><h3>${escapeHtml(game.title)}</h3><div class="meta"><span class="badge ${launchable ? "launchable" : ""}">${labels[game.action] || game.action}</span><span class="badge">${escapeHtml(game.platform || "Unbekannt")}</span><span>${formatBytes(game.logical_size)}</span></div>${launchable ? "" : `<div class="manual">${escapeHtml(game.detection_note)}</div>`}<div class="card-actions">${launchable ? `<button onclick="launchGame('${game.id}')">${actionLabel(game)}</button>` : ""}<button class="secondary" onclick="openGameFolder('${game.id}')">Ordner öffnen</button><button class="secondary" onclick="editGame('${game.id}')">Edit</button></div></div></article>`;
  }).join("") || "<p>Keine passenden Einträge.</p>";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"})[character]);
}

async function launchGame(id, action = null) {
  try {
    const ticket = await api(`/api/games/${id}/launch-ticket`, {method: "POST", body: JSON.stringify(action ? {action} : {})});
    window.location.href = ticket.protocol_url;
  } catch (error) { alert(error.message); }
}

function openGameFolder(id) { return launchGame(id, "open_folder"); }

function editGame(id) {
  const game = state.games.find((candidate) => candidate.id === id);
  if (!game) return;
  document.querySelector("#editId").value = id;
  document.querySelector("#editTitle").value = game.custom_title || "";
  document.querySelector("#editPlatform").value = game.platform || "";
  document.querySelector("#editAction").value = game.action_override || "";
  document.querySelector("#editLauncher").value = game.launcher_override || game.detected_launcher || "";
  document.querySelector("#editDescription").value = game.description || "";
  document.querySelector("#editCover").value = "";
  document.querySelector("#editNote").textContent = `Erkannt: ${labels[game.detected_type] || game.detected_type} · ${game.detection_note} · ${game.relative_path}`;
  editor.showModal();
}

function updateRangeOutputs() {
  document.querySelector("#opacityValue").textContent = `${Math.round(Number(document.querySelector("#settingOpacity").value) * 100)} %`;
  document.querySelector("#blurValue").textContent = `${document.querySelector("#settingBlur").value} px`;
}

function openSettings() {
  const settings = state.settings;
  document.querySelector("#settingServerName").value = settings.server_name;
  document.querySelector("#settingLibraryName").value = settings.library_name;
  document.querySelector("#settingTheme").value = settings.theme;
  document.querySelector("#settingCrosshair").checked = settings.crosshair_cursor;
  document.querySelector("#settingOpacity").value = settings.background_opacity;
  document.querySelector("#settingBlur").value = settings.background_blur;
  document.querySelector("#settingExclusions").value = settings.scan_exclusions.join(", ");
  document.querySelector("#settingBackground").value = "";
  updateRangeOutputs();
  settingsDialog.showModal();
}

document.querySelector("#editorForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#editId").value;
  const body = {
    custom_title: document.querySelector("#editTitle").value.trim() || null,
    platform: document.querySelector("#editPlatform").value.trim() || "Unbekannt",
    action_override: document.querySelector("#editAction").value || null,
    launcher_override: document.querySelector("#editLauncher").value.trim() || null,
    description: document.querySelector("#editDescription").value.trim(),
  };
  try {
    await api(`/api/games/${id}`, {method: "PATCH", body: JSON.stringify(body)});
    const cover = document.querySelector("#editCover").files[0];
    if (cover) {
      const form = new FormData();
      form.append("cover", cover);
      const response = await fetch(`/api/games/${id}/cover`, {method: "POST", headers: {"X-CSRF-Token": csrf}, body: form});
      if (!response.ok) throw new Error((await response.json()).error);
    }
    editor.close();
    await load();
  } catch (error) { alert(error.message); }
});

document.querySelector("#settingsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    server_name: document.querySelector("#settingServerName").value.trim(),
    library_name: document.querySelector("#settingLibraryName").value.trim(),
    theme: document.querySelector("#settingTheme").value,
    crosshair_cursor: document.querySelector("#settingCrosshair").checked,
    background_opacity: Number(document.querySelector("#settingOpacity").value),
    background_blur: Number(document.querySelector("#settingBlur").value),
    scan_exclusions: document.querySelector("#settingExclusions").value.split(/[,\n]/).map((value) => value.trim()).filter(Boolean),
  };
  try {
    let settings = await api("/api/settings", {method: "PATCH", body: JSON.stringify(payload)});
    const background = document.querySelector("#settingBackground").files[0];
    if (background) {
      const form = new FormData();
      form.append("background", background);
      const response = await fetch("/api/settings/background", {method: "POST", headers: {"X-CSRF-Token": csrf}, body: form});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      settings = data;
    }
    applySettings(settings);
    settingsDialog.close();
  } catch (error) { alert(error.message); }
});

document.querySelector("#removeBackgroundButton").addEventListener("click", async () => {
  try {
    const settings = await api("/api/settings/background", {method: "DELETE"});
    applySettings(settings);
    document.querySelector("#settingBackground").value = "";
  } catch (error) { alert(error.message); }
});

document.querySelector("#scanButton").addEventListener("click", async () => {
  statusEl.textContent = "Scanne Bibliothek …";
  try {
    const result = await api("/api/scan", {method: "POST"});
    statusEl.textContent = `${result.scanned} Einträge gescannt`;
    await load();
  } catch (error) { statusEl.textContent = error.message; }
});
document.querySelector("#settingsButton").addEventListener("click", openSettings);
document.querySelector("#settingOpacity").addEventListener("input", updateRangeOutputs);
document.querySelector("#settingBlur").addEventListener("input", updateRangeOutputs);
document.querySelector("#search").addEventListener("input", (event) => { state.query = event.target.value; render(); });
document.querySelector("#filter").addEventListener("change", (event) => { state.filter = event.target.value; render(); });

load();
