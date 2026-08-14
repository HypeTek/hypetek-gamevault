const savedPageSize = Number(localStorage.getItem("missionControlPageSize"));
const state = {
  games: [],
  query: "",
  filter: "all",
  settings: null,
  page: 1,
  pageSize: [12, 24, 48, 96].includes(savedPageSize) ? savedPageSize : 24,
  view: localStorage.getItem("missionControlLibraryView") === "list" ? "list" : "grid",
};
const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
const missionControlI18n = window.MissionControlI18n || {};
const applyUiLanguage = typeof missionControlI18n.applyUiLanguage === "function" ? missionControlI18n.applyUiLanguage : () => {};
const tr = typeof missionControlI18n.tr === "function" ? missionControlI18n.tr : (key) => key;
const typeLabelKeys = {direct_setup: "type.directSetup", iso: "type.iso", manual: "type.manual", archive: "type.archive", manual_image: "type.manualImage", ignore: "type.ignore"};
const library = document.querySelector("#library");
const statusEl = document.querySelector("#status");
const editor = document.querySelector("#editor");
const settingsDialog = document.querySelector("#settingsDialog");
const connectionHelpDialog = document.querySelector("#connectionHelpDialog");
const integrationHelpDialog = document.querySelector("#integrationHelpDialog");
const gameInfoDialog = document.querySelector("#gameInfoDialog");
const designProfilesDialog = document.querySelector("#designProfilesDialog");
let designProfileState = {active: "mission", profiles: []};
let coverPreviewObjectUrl = null;
let coverDrag = null;

// Register the critical agent check before optional interface enhancements.
// Function declarations are initialized before this statement is evaluated.
document.querySelector("#agentProbeButton")?.addEventListener("click", probeWindowsAgent);

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
  applyUiLanguage(settings.ui_language || "de");
  const profile = settings.design_profile || {};
  const colors = profile.colors || {};
  document.body.dataset.theme = settings.active_design_profile || settings.theme;
  document.body.dataset.style = profile.style || "soft";
  document.body.dataset.font = profile.font || "system";
  const colorVariables = {background: "--bg", panel: "--panel", panel_alt: "--panel2", text: "--text", muted: "--muted", primary: "--teal", secondary: "--orange", line: "--line", energy_start: "--energy-start", energy_end: "--energy-end"};
  Object.entries(colorVariables).forEach(([key, variable]) => {
    if (colors[key]) document.body.style.setProperty(variable, colors[key]);
  });
  document.body.classList.toggle("crosshair", Boolean(settings.crosshair_cursor));
  document.body.style.setProperty("--custom-background", settings.background_url ? `url("${settings.background_url}")` : "none");
  document.body.style.setProperty("--background-opacity", profile.background_opacity ?? settings.background_opacity);
  document.body.style.setProperty("--background-blur", `${profile.background_blur ?? settings.background_blur}px`);
  document.querySelector("#libraryName").textContent = settings.library_name;
  document.querySelector("#appVersion").textContent = `v${settings.version || "development"}`;
  document.title = `HypeTek Mission Control · ${settings.server_name}`;
  const agentValidated = localStorage.getItem("missionControlAgentValidatedFor") === window.location.origin;
  document.querySelector("#agentNote").hidden = agentValidated;
  document.querySelector("#agentSetupButton").textContent = agentValidated ? tr("agent.ready") : tr("nav.agent");
  requestAnimationFrame(updateLcarsLayout);
}

function updateLcarsLayout() {
  const energyLine = document.querySelector(".energy-line");
  const logoButton = document.querySelector("#brandHomeButton");
  if (!energyLine || !logoButton) return;
  const railTop = Math.ceil(energyLine.getBoundingClientRect().bottom + window.scrollY + 8);
  const stickyTop = Math.ceil(logoButton.getBoundingClientRect().bottom + 18);
  document.body.style.setProperty("--lcars-rail-top", `${railTop}px`);
  document.body.style.setProperty("--lcars-clock-sticky-top", `${stickyTop}px`);
}

function parseProfileColor(value) {
  const color = String(value || "").trim();
  const hex = color.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (hex) return hex.slice(1).map((part) => parseInt(part, 16));
  const rgb = color.match(/^rgba?\(\s*(\d+)\D+(\d+)\D+(\d+)/i);
  return rgb ? rgb.slice(1, 4).map(Number) : [0, 209, 199];
}

function animateEnergyColor(timestamp) {
  const point = document.querySelector(".energy-line span");
  if (!point || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const styles = getComputedStyle(document.body);
  const start = parseProfileColor(styles.getPropertyValue("--energy-start"));
  const end = parseProfileColor(styles.getPropertyValue("--energy-end"));
  const elapsed = timestamp % 6500;
  const ratio = Math.min(1, elapsed / 4750);
  const mixed = start.map((component, index) => Math.round(component + ((end[index] - component) * ratio)));
  point.style.setProperty("--energy-color", `rgb(${mixed.join(",")})`);
  requestAnimationFrame(animateEnergyColor);
}

function showAgentSetup() {
  const note = document.querySelector("#agentNote");
  note.hidden = false;
  document.querySelector("#agentSetup").scrollIntoView({behavior: "smooth", block: "start"});
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
  if (game.action === "direct_setup") return tr("game.install");
  if (game.action === "iso") return tr("game.mountInstall");
  return tr("game.manualInstall");
}

function typeLabel(type) {
  return tr(typeLabelKeys[type] || type);
}

function gameMonogram(title) {
  const words = String(title || "Game").replace(/[^\p{L}\p{N}]+/gu, " ").trim().split(/\s+/).filter(Boolean);
  return (words.slice(0, 2).map((word) => word[0]).join("") || "GV").toLocaleUpperCase();
}

function coverUrl(game) {
  return game.cover_name ? `/covers/${encodeURIComponent(game.cover_name)}` : "";
}

function coverPosition(game) {
  const value = Number(game.cover_position_y);
  return Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 50;
}

function render() {
  const query = state.query.toLocaleLowerCase("de");
  const filteredGames = state.games.filter((game) =>
    (state.filter === "all" || (state.filter === "favorites" ? game.favorite : game.action === state.filter)) &&
    `${game.title} ${game.platform} ${game.relative_path}`.toLocaleLowerCase("de").includes(query));
  const pageCount = Math.max(1, Math.ceil(filteredGames.length / state.pageSize));
  state.page = Math.max(1, Math.min(state.page, pageCount));
  const firstIndex = (state.page - 1) * state.pageSize;
  const games = filteredGames.slice(firstIndex, firstIndex + state.pageSize);
  const counts = state.games.reduce((result, game) => {
    result[game.action] = (result[game.action] || 0) + 1;
    return result;
  }, {});
  document.querySelector("#stats").innerHTML =
    `<div class="stat"><strong>${state.games.length}</strong>${tr("stats.entries")}</div>` +
    `<div class="stat"><strong>${counts.direct_setup || 0}</strong>${tr("stats.setups")}</div>` +
    `<div class="stat"><strong>${counts.iso || 0}</strong>${tr("stats.isos")}</div>`;
  library.classList.toggle("view-list", state.view === "list");
  document.querySelector("#viewGridButton").setAttribute("aria-pressed", String(state.view === "grid"));
  document.querySelector("#viewListButton").setAttribute("aria-pressed", String(state.view === "list"));
  document.querySelector("#pageSize").value = String(state.pageSize);
  library.innerHTML = games.map((game) => {
    const launchable = ["direct_setup", "iso"].includes(game.action) && game.launcher;
    const hasCover = Boolean(game.cover_name);
    const cover = hasCover ? `background-image:url('${coverUrl(game)}');background-position:center ${coverPosition(game)}%` : "";
    const monogram = escapeHtml(gameMonogram(game.title));
    const sourceNames = {rawg: "RAWG", thegamesdb: "TheGamesDB"};
    const sourceName = sourceNames[game.metadata_provider];
    const attribution = sourceName && game.metadata_source_url
      ? `<a class="cover-source" href="${escapeHtml(game.metadata_source_url)}" target="_blank" rel="noopener noreferrer">${tr("game.coverSource", {source: sourceName})}</a>` : "";
    return `<article class="card" data-game-id="${game.id}"><button class="card-info" type="button" onclick="showGameInfo('${game.id}')" aria-label="${escapeHtml(tr("game.info", {title: game.title}))}"><div class="cover ${hasCover ? "" : "placeholder"}" data-monogram="${monogram}" style="${cover}">${game.favorite ? '<span class="card-favorite" title="Favorit">★</span>' : ""}<div class="cover-title">${escapeHtml(game.title)}</div></div></button><div class="card-body"><h3 title="${escapeHtml(game.title)}">${escapeHtml(game.title)}</h3><div class="meta"><span class="badge ${launchable ? "launchable" : ""}">${typeLabel(game.action)}</span><span class="badge">${escapeHtml(game.platform || tr("game.unknown"))}</span><span>${formatBytes(game.logical_size)}</span></div>${attribution}${launchable ? "" : `<div class="manual">${escapeHtml(game.detection_note)}</div>`}<div class="card-actions">${launchable ? `<button class="primary-action" onclick="launchGame('${game.id}')">${actionLabel(game)}</button>` : ""}<button class="secondary folder-action" onclick="openGameFolder('${game.id}')">${tr("game.folder")}</button><button class="secondary edit-action" onclick="editGame('${game.id}')">${tr("game.edit")}</button></div></div></article>`;
  }).join("") || `<p>${tr("game.empty")}</p>`;
  renderPagination(filteredGames.length, pageCount, firstIndex, games.length);
}

function renderPagination(total, pageCount, firstIndex, shown) {
  const pagination = document.querySelector("#pagination");
  if (!total) {
    pagination.innerHTML = "";
    pagination.hidden = true;
    return;
  }
  pagination.hidden = false;
  const start = firstIndex + 1;
  const end = firstIndex + shown;
  pagination.innerHTML = `<span>${start}–${end} / ${total}</span><div><button type="button" class="secondary" data-page="previous" ${state.page <= 1 ? "disabled" : ""}>← ${tr("pagination.previous")}</button><strong>${tr("pagination.page", {current: state.page, total: pageCount})}</strong><button type="button" class="secondary" data-page="next" ${state.page >= pageCount ? "disabled" : ""}>${tr("pagination.next")} →</button></div>`;
  pagination.querySelector('[data-page="previous"]')?.addEventListener("click", () => changePage(state.page - 1));
  pagination.querySelector('[data-page="next"]')?.addEventListener("click", () => changePage(state.page + 1));
}

function changePage(page) {
  state.page = page;
  render();
  document.querySelector("#library").scrollIntoView({behavior: "smooth", block: "start"});
}

function setLibraryView(view) {
  state.view = view === "list" ? "list" : "grid";
  localStorage.setItem("missionControlLibraryView", state.view);
  render();
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
  if (coverPreviewObjectUrl) URL.revokeObjectURL(coverPreviewObjectUrl);
  coverPreviewObjectUrl = null;
  document.querySelector("#editCoverPosition").value = coverPosition(game);
  document.querySelector("#metadataQuery").value = game.metadata_search_title || game.title;
  document.querySelector("#metadataResults").innerHTML = "";
  document.querySelector("#editNote").textContent = `Erkannt: ${typeLabel(game.detected_type)} · ${game.detection_note} · ${game.relative_path}`;
  updateCoverPositionPreview();
  editor.showModal();
}

function updateCoverPositionPreview() {
  const id = document.querySelector("#editId").value;
  const game = state.games.find((candidate) => candidate.id === id);
  const value = Math.max(0, Math.min(100, Number(document.querySelector("#editCoverPosition").value || 50)));
  const preview = document.querySelector("#coverPositionPreview");
  const imageUrl = coverPreviewObjectUrl || (game?.cover_name ? coverUrl(game) : "");
  preview.style.backgroundImage = imageUrl ? `url('${imageUrl}')` : "none";
  preview.style.backgroundPosition = `center ${value}%`;
  preview.setAttribute("aria-valuenow", String(Math.round(value)));
  preview.classList.toggle("is-empty", !imageUrl);
  document.querySelector("#coverPositionPreviewTitle").textContent = document.querySelector("#editTitle").value.trim() || game?.title || "Cover-Vorschau";
}

function setCoverPosition(value) {
  document.querySelector("#editCoverPosition").value = String(Math.max(0, Math.min(100, Math.round(value))));
  updateCoverPositionPreview();
}

function startCoverDrag(event) {
  const preview = document.querySelector("#coverPositionPreview");
  if (preview.classList.contains("is-empty") || event.button !== 0) return;
  coverDrag = {
    pointerId: event.pointerId,
    startY: event.clientY,
    startValue: Number(document.querySelector("#editCoverPosition").value || 50),
  };
  preview.setPointerCapture(event.pointerId);
  preview.classList.add("is-dragging");
  event.preventDefault();
}

function moveCoverDrag(event) {
  if (!coverDrag || event.pointerId !== coverDrag.pointerId) return;
  const preview = document.querySelector("#coverPositionPreview");
  const deltaPercent = ((coverDrag.startY - event.clientY) / Math.max(1, preview.clientHeight)) * 100;
  setCoverPosition(coverDrag.startValue + deltaPercent);
}

function stopCoverDrag(event) {
  if (!coverDrag || event.pointerId !== coverDrag.pointerId) return;
  document.querySelector("#coverPositionPreview").classList.remove("is-dragging");
  coverDrag = null;
}

function nudgeCoverPosition(event) {
  if (!["ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
  const current = Number(document.querySelector("#editCoverPosition").value || 50);
  if (event.key === "Home") setCoverPosition(0);
  else if (event.key === "End") setCoverPosition(100);
  else setCoverPosition(current + (event.key === "ArrowUp" ? 2 : -2));
  event.preventDefault();
}

function showGameInfo(id) {
  const game = state.games.find((candidate) => candidate.id === id);
  if (!game) return;
  const hero = document.querySelector("#gameInfoHero");
  hero.style.backgroundImage = game.cover_name ? `url('${coverUrl(game)}')` : "none";
  hero.style.backgroundPosition = `center ${coverPosition(game)}%`;
  document.querySelector("#gameInfoProvider").textContent = game.metadata_provider === "thegamesdb" ? "TheGamesDB" : "Mission Control";
  document.querySelector("#gameInfoTitle").textContent = game.metadata_title || game.title;
  const metadata = [game.metadata_platform || game.platform, game.metadata_release_date, game.metadata_rating, game.metadata_players ? `${game.metadata_players} Spieler` : "", game.metadata_coop ? `Co-op: ${game.metadata_coop}` : ""].filter(Boolean);
  document.querySelector("#gameInfoMeta").innerHTML = metadata.map((value) => `<span>${escapeHtml(value)}</span>`).join("");
  const overview = String(game.metadata_overview || "").trim();
  const notes = String(game.description || "").trim();
  document.querySelector("#gameInfoOverview").textContent = overview || "Für diesen Eintrag wurde noch kein Spielinhalt übernommen.";
  document.querySelector("#gameInfoOverviewSection").classList.toggle("is-empty", !overview);
  document.querySelector("#gameInfoNotes").textContent = notes || "Keine eigenen Bemerkungen hinterlegt.";
  document.querySelector("#gameInfoNotesSection").classList.toggle("is-empty", !notes);
  document.querySelector("#gameInfoLibrary").innerHTML = `<dt>Bibliothekstitel</dt><dd>${escapeHtml(game.title)}</dd><dt>Typ</dt><dd>${escapeHtml(typeLabel(game.action))}</dd><dt>Größe</dt><dd>${formatBytes(game.logical_size)}</dd>`;
  const source = game.metadata_source_url ? `<a class="button-link secondary" href="${escapeHtml(game.metadata_source_url)}" target="_blank" rel="noopener noreferrer">Quelle ansehen</a>` : "";
  const launchable = ["direct_setup", "iso"].includes(game.action) && game.launcher;
  const launch = launchable ? `<button type="button" class="primary-info-action" onclick="launchGame('${game.id}')">${actionLabel(game)}</button>` : "";
  const translate = state.settings?.translator_configured && overview
    ? `<button type="button" class="secondary" onclick="translateGameInfo('${game.id}')">Spielinhalt übersetzen</button>` : "";
  const original = game.metadata_overview_original && game.metadata_overview_original !== game.metadata_overview
    ? `<button id="gameInfoOriginalButton" type="button" class="secondary" onclick="toggleGameInfoOriginal('${game.id}')">Original anzeigen</button>` : "";
  const favorite = `<button type="button" class="favorite-action ${game.favorite ? "is-favorite" : "secondary"}" onclick="toggleFavorite('${game.id}')" aria-pressed="${game.favorite ? "true" : "false"}">${game.favorite ? tr("game.favorite") : tr("game.makeFavorite")}</button>`;
  document.querySelector("#gameInfoActions").innerHTML = `${launch}${favorite}<button type="button" class="secondary" onclick="openGameFolder('${game.id}')">${tr("game.folder")}</button>${translate}${original}${source}<button type="button" class="secondary" onclick="gameInfoDialog.close(); editGame('${game.id}')">${tr("game.edit")}</button>`;
  if (!gameInfoDialog.open) gameInfoDialog.showModal();
}

async function toggleFavorite(id) {
  const index = state.games.findIndex((game) => game.id === id);
  if (index < 0) return;
  try {
    const updated = await api(`/api/games/${id}`, {method: "PATCH", body: JSON.stringify({favorite: !state.games[index].favorite})});
    state.games[index] = {...state.games[index], ...updated};
    render();
    showGameInfo(id);
  } catch (error) { alert(error.message); }
}

async function translateGameInfo(id) {
  try {
    const translated = await api(`/api/games/${id}/metadata/translate`, {method: "POST", body: "{}"});
    const index = state.games.findIndex((game) => game.id === id);
    if (index >= 0) state.games[index] = {...state.games[index], ...translated};
    showGameInfo(id);
  } catch (error) { alert(error.message); }
}

function toggleGameInfoOriginal(id) {
  const game = state.games.find((candidate) => candidate.id === id);
  if (!game?.metadata_overview_original) return;
  const overview = document.querySelector("#gameInfoOverview");
  const button = document.querySelector("#gameInfoOriginalButton");
  const showingOriginal = button.dataset.showingOriginal === "true";
  overview.textContent = showingOriginal ? game.metadata_overview : game.metadata_overview_original;
  button.dataset.showingOriginal = showingOriginal ? "false" : "true";
  button.textContent = showingOriginal ? "Original anzeigen" : "Übersetzung anzeigen";
}

function openSettings() {
  const settings = state.settings;
  document.querySelector("#settingServerName").value = settings.server_name;
  document.querySelector("#settingLibraryName").value = settings.library_name;
  document.querySelector("#settingCrosshair").checked = settings.crosshair_cursor;
  document.querySelector("#settingExclusions").value = settings.scan_exclusions.join(", ");
  document.querySelector("#settingTheGamesDbApiKey").value = "";
  document.querySelector("#theGamesDbKeyStatus").textContent = settings.thegamesdb_configured ? tr("settings.keyStored") : tr("settings.keyMissing");
  document.querySelector("#settingContentLanguage").value = settings.content_language || "de";
  document.querySelector("#settingUiLanguage").value = settings.ui_language || "de";
  document.querySelector("#settingTranslatorUrl").value = settings.translator_url || "";
  document.querySelector("#settingTranslatorApiKey").value = "";
  document.querySelector("#translatorStatus").textContent = settings.translator_configured ? tr("settings.translatorReady") : tr("settings.translatorMissing");
  settingsDialog.showModal();
}

function profilePayloadFromForm() {
  const colors = {};
  document.querySelectorAll("[data-profile-color]").forEach((input) => { colors[input.dataset.profileColor] = input.value; });
  return {
    name: document.querySelector("#designProfileName").value.trim(),
    style: document.querySelector('input[name="profileStyle"]:checked').value,
    font: document.querySelector("#designProfileFont").value,
    colors,
    background_name: document.querySelector("#designProfileBackgroundName").value || null,
    background_opacity: Number(document.querySelector("#designProfileOpacity").value),
    background_blur: Number(document.querySelector("#designProfileBlur").value),
  };
}

function renderDesignProfilePreview() {
  const profile = profilePayloadFromForm();
  const preview = document.querySelector("#designProfilePreview");
  preview.dataset.style = profile.style;
  preview.dataset.font = profile.font;
  const variables = {background: "--preview-bg", panel: "--preview-panel", panel_alt: "--preview-panel2", text: "--preview-text", muted: "--preview-muted", primary: "--preview-primary", secondary: "--preview-secondary", line: "--preview-line", energy_start: "--preview-energy-start", energy_end: "--preview-energy-end"};
  Object.entries(variables).forEach(([key, variable]) => preview.style.setProperty(variable, profile.colors[key]));
  const selectedBackground = document.querySelector("#designProfileBackground").files[0];
  if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
  let background = "none";
  if (selectedBackground) {
    preview.dataset.objectUrl = URL.createObjectURL(selectedBackground);
    background = `url('${preview.dataset.objectUrl}')`;
  } else if (profile.background_name) {
    preview.dataset.objectUrl = "";
    background = `url('/backgrounds/${encodeURIComponent(profile.background_name)}')`;
  } else {
    preview.dataset.objectUrl = "";
  }
  preview.style.setProperty("--preview-background", background);
  preview.style.setProperty("--preview-opacity", String(profile.background_opacity));
  preview.style.setProperty("--preview-blur", `${profile.background_blur}px`);
  document.querySelector("#profileOpacityValue").textContent = `${Math.round(profile.background_opacity * 100)} %`;
  document.querySelector("#profileBlurValue").textContent = `${profile.background_blur} px`;
}

function fillDesignProfileForm(profile = state.settings.design_profile, id = "") {
  document.querySelector("#designProfileSaveStatus").textContent = "";
  document.querySelector("#designProfileId").value = id;
  document.querySelector("#designProfileName").value = id ? profile.name : `${profile.name} Kopie`;
  document.querySelector(`input[name="profileStyle"][value="${profile.style || "soft"}"]`).checked = true;
  document.querySelector("#designProfileFont").value = profile.font || "system";
  document.querySelector("#designProfileBackground").value = "";
  document.querySelector("#designProfileBackgroundName").value = profile.background_name || "";
  document.querySelectorAll("[data-profile-color]").forEach((input) => { input.value = profile.colors[input.dataset.profileColor]; });
  document.querySelector("#designProfileOpacity").value = profile.background_opacity ?? 0.28;
  document.querySelector("#designProfileBlur").value = profile.background_blur ?? 2;
  document.querySelector("#designProfileForm").hidden = false;
  document.querySelector("#designProfileList").hidden = true;
  document.querySelector("#designProfileListActions").hidden = true;
  renderDesignProfilePreview();
}

function renderDesignProfiles() {
  document.querySelector("#designProfileSaveStatus").textContent = "";
  const list = document.querySelector("#designProfileList");
  list.hidden = false;
  document.querySelector("#designProfileListActions").hidden = false;
  document.querySelector("#designProfileForm").hidden = true;
  list.innerHTML = designProfileState.profiles.map((profile) => `<article class="design-profile-card ${profile.id === designProfileState.active ? "is-active" : ""}" style="--profile-primary:${escapeHtml(profile.colors.primary)};--profile-secondary:${escapeHtml(profile.colors.secondary)};--profile-panel:${escapeHtml(profile.colors.panel)}"><div class="profile-swatch"></div><div><strong>${escapeHtml(profile.name)}</strong><span>${escapeHtml(profile.style)} · ${escapeHtml(profile.font)}</span></div><span>${profile.id === designProfileState.active ? tr("profiles.active") : ""}</span><div class="profile-card-actions">${profile.id === designProfileState.active ? "" : `<button type="button" data-profile-activate="${profile.id}">${tr("profiles.activate")}</button>`}<button type="button" class="secondary" data-profile-copy="${profile.id}">${tr("profiles.duplicate")}</button>${profile.builtin ? "" : `<button type="button" class="secondary" data-profile-edit="${profile.id}">${tr("profiles.edit")}</button><button type="button" class="ghost" data-profile-delete="${profile.id}">${tr("profiles.delete")}</button>`}</div></article>`).join("");
  list.querySelectorAll("[data-profile-activate]").forEach((button) => button.addEventListener("click", () => activateDesignProfile(button.dataset.profileActivate)));
  list.querySelectorAll("[data-profile-copy]").forEach((button) => button.addEventListener("click", () => fillDesignProfileForm(designProfileState.profiles.find((item) => item.id === button.dataset.profileCopy), "")));
  list.querySelectorAll("[data-profile-edit]").forEach((button) => button.addEventListener("click", () => fillDesignProfileForm(designProfileState.profiles.find((item) => item.id === button.dataset.profileEdit), button.dataset.profileEdit)));
  list.querySelectorAll("[data-profile-delete]").forEach((button) => button.addEventListener("click", () => deleteDesignProfile(button.dataset.profileDelete)));
}

async function openDesignProfiles() {
  designProfileState = await api("/api/design-profiles");
  renderDesignProfiles();
  settingsDialog.close();
  designProfilesDialog.showModal();
}

async function activateDesignProfile(id) {
  applySettings(await api(`/api/design-profiles/${encodeURIComponent(id)}/activate`, {method: "POST", body: "{}"}));
  designProfileState = await api("/api/design-profiles");
  renderDesignProfiles();
}

async function deleteDesignProfile(id) {
  if (!confirm("Dieses eigene Designprofil wirklich löschen?")) return;
  const wasActive = designProfileState.active === id;
  designProfileState = await api(`/api/design-profiles/${encodeURIComponent(id)}`, {method: "DELETE"});
  if (wasActive) applySettings(await api("/api/settings"));
  renderDesignProfiles();
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
    cover_position_y: Number(document.querySelector("#editCoverPosition").value),
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
    crosshair_cursor: document.querySelector("#settingCrosshair").checked,
    scan_exclusions: document.querySelector("#settingExclusions").value.split(/[,\n]/).map((value) => value.trim()).filter(Boolean),
    content_language: document.querySelector("#settingContentLanguage").value,
    ui_language: document.querySelector("#settingUiLanguage").value,
    translator_url: document.querySelector("#settingTranslatorUrl").value.trim(),
  };
  const theGamesDbApiKey = document.querySelector("#settingTheGamesDbApiKey").value.trim();
  if (theGamesDbApiKey) payload.thegamesdb_api_key = theGamesDbApiKey;
  const translatorApiKey = document.querySelector("#settingTranslatorApiKey").value.trim();
  if (translatorApiKey) payload.translator_api_key = translatorApiKey;
  try {
    const settings = await api("/api/settings", {method: "PATCH", body: JSON.stringify(payload)});
    applySettings(settings);
    render();
    settingsDialog.close();
  } catch (error) { alert(error.message); }
});

document.querySelector("#removeTheGamesDbKeyButton").addEventListener("click", async () => {
  if (!confirm("Gespeicherten TheGamesDB-API-Key wirklich entfernen?")) return;
  try {
    const settings = await api("/api/settings", {method: "PATCH", body: JSON.stringify({thegamesdb_api_key: null})});
    applySettings(settings);
    document.querySelector("#settingTheGamesDbApiKey").value = "";
    document.querySelector("#theGamesDbKeyStatus").textContent = tr("settings.keyMissing");
  } catch (error) { alert(error.message); }
});

document.querySelector("#removeTranslatorButton").addEventListener("click", async () => {
  if (!confirm("Translator-Verbindung und gespeicherten Translator-API-Key wirklich entfernen?")) return;
  try {
    const settings = await api("/api/settings", {method: "PATCH", body: JSON.stringify({translator_url: "", translator_api_key: null})});
    applySettings(settings);
    document.querySelector("#settingTranslatorUrl").value = "";
    document.querySelector("#settingTranslatorApiKey").value = "";
    document.querySelector("#translatorStatus").textContent = tr("settings.translatorMissing");
  } catch (error) { alert(error.message); }
});

async function probeWindowsAgent() {
  const button = document.querySelector("#agentProbeButton");
  const output = document.querySelector("#agentProbeStatus");
  button.disabled = true;
  output.textContent = " · Prüfung läuft …";
  try {
    const probe = await api("/api/agent/probes", {method: "POST", body: "{}"});
    window.location.href = probe.protocol_url;
    for (let attempt = 0; attempt < 20; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const result = await api(`/api/agent/probes/${encodeURIComponent(probe.token)}`);
      if (result.confirmed) {
        localStorage.setItem("missionControlAgentValidatedFor", window.location.origin);
        output.textContent = " · Agent erkannt";
        setTimeout(() => { document.querySelector("#agentNote").hidden = true; }, 800);
        return;
      }
      if (result.expired) break;
    }
    throw new Error("Der Windows-Agent hat nicht geantwortet. Bitte installieren oder auf Version 0.3.7 aktualisieren.");
  } catch (error) {
    output.textContent = ` · ${error.message}`;
    button.disabled = false;
  }
}

// Keep this critical action callable through the button's inline safety
// handler even if an optional UI enhancement fails later during bootstrap.
window.probeWindowsAgent = probeWindowsAgent;

function updateLcarsSystemClock() {
  const clock = document.querySelector("#lcarsSystemClock");
  const date = document.querySelector("#lcarsSystemDate");
  if (!clock || !date) return;
  const now = new Date();
  const language = state.settings?.ui_language || document.documentElement.lang || "de";
  clock.textContent = now.toLocaleTimeString(language, {hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false});
  clock.dateTime = now.toISOString();
  date.textContent = now.toLocaleDateString(language, {day: "2-digit", month: "2-digit", year: "numeric"});
}

function renderMetadataResults(results) {
  const target = document.querySelector("#metadataResults");
  if (!results.length) { target.innerHTML = '<p class="note">Keine passenden Treffer gefunden.</p>'; return; }
  target.innerHTML = results.map((item, index) => `<article class="metadata-result"><img src="${escapeHtml(item.preview_url)}" alt="" loading="lazy"><div><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.platform || "Plattform unbekannt")} · ${escapeHtml(item.released || "Jahr unbekannt")}</span><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener noreferrer">Bei TheGamesDB ansehen</a></div><button type="button" data-metadata-index="${index}">Übernehmen</button></article>`).join("");
  target.querySelectorAll("[data-metadata-index]").forEach((button) => button.addEventListener("click", async () => {
    const item = results[Number(button.dataset.metadataIndex)];
    const id = document.querySelector("#editId").value;
    button.disabled = true;
    button.textContent = "Lade …";
    try {
      await api(`/api/games/${id}/metadata/apply`, {method: "POST", body: JSON.stringify(item)});
      await load();
      updateCoverPositionPreview();
      target.innerHTML = '<p class="note">Cover übernommen. Du kannst den Dialog jetzt speichern oder schließen.</p>';
    } catch (error) { alert(error.message); button.disabled = false; button.textContent = "Übernehmen"; }
  }));
}

document.querySelector("#metadataSearchButton").addEventListener("click", async () => {
  const id = document.querySelector("#editId").value;
  const query = document.querySelector("#metadataQuery").value.trim();
  const target = document.querySelector("#metadataResults");
  if (!query) { alert("Bitte einen Titel für die Suche eingeben."); return; }
  target.innerHTML = '<p class="note">Suche bei TheGamesDB …</p>';
  try {
    const data = await api(`/api/games/${id}/metadata/search`, {method: "POST", body: JSON.stringify({query})});
    renderMetadataResults(data.results);
  } catch (error) { target.innerHTML = `<p class="note error">${escapeHtml(error.message)}</p>`; }
});

document.querySelector("#scanButton").addEventListener("click", async () => {
  statusEl.textContent = tr("scan.running");
  try {
    const result = await api("/api/scan", {method: "POST"});
    statusEl.textContent = tr("scan.done", {count: result.scanned});
    await load();
  } catch (error) { statusEl.textContent = error.message; }
});
document.querySelector("#settingsButton").addEventListener("click", openSettings);
document.querySelector("#designProfilesButton").addEventListener("click", openDesignProfiles);
document.querySelector("#closeDesignProfiles").addEventListener("click", () => designProfilesDialog.close());
document.querySelector("#newDesignProfileButton").addEventListener("click", () => fillDesignProfileForm(state.settings.design_profile, ""));
document.querySelector("#cancelDesignProfileEdit").addEventListener("click", renderDesignProfiles);
document.querySelector("#designProfilesBackButton").addEventListener("click", () => {
  designProfilesDialog.close();
  openSettings();
});
document.querySelector("#designProfileForm").addEventListener("input", () => {
  document.querySelector("#designProfileSaveStatus").textContent = "";
  renderDesignProfilePreview();
});
document.querySelector("#designProfileBackground").addEventListener("change", renderDesignProfilePreview);
document.querySelector("#removeDesignProfileBackground").addEventListener("click", () => {
  document.querySelector("#designProfileBackground").value = "";
  document.querySelector("#designProfileBackgroundName").value = "";
  renderDesignProfilePreview();
});
document.querySelector("#designProfileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#designProfileId").value;
  const saveButton = document.querySelector("#saveDesignProfileButton");
  const saveStatus = document.querySelector("#designProfileSaveStatus");
  const isNew = !id;
  saveButton.disabled = true;
  saveStatus.textContent = tr("profiles.saving");
  try {
    const background = document.querySelector("#designProfileBackground").files[0];
    if (background) {
      const form = new FormData();
      form.append("background", background);
      const response = await fetch("/api/design-profiles/background", {method: "POST", headers: {"X-CSRF-Token": csrf}, body: form});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      document.querySelector("#designProfileBackgroundName").value = result.name;
    }
    const saved = id
      ? await api(`/api/design-profiles/${encodeURIComponent(id)}`, {method: "PUT", body: JSON.stringify(profilePayloadFromForm())})
      : await api("/api/design-profiles", {method: "POST", body: JSON.stringify(profilePayloadFromForm())});
    document.querySelector("#designProfileId").value = saved.id;
    if (isNew) applySettings(await api(`/api/design-profiles/${encodeURIComponent(saved.id)}/activate`, {method: "POST", body: "{}"}));
    designProfileState = await api("/api/design-profiles");
    if (!isNew && designProfileState.active === saved.id) applySettings(await api("/api/settings"));
    saveStatus.textContent = isNew ? tr("profiles.saved") : "✓ Profil gespeichert";
  } catch (error) {
    saveStatus.textContent = "Speichern fehlgeschlagen";
    alert(error.message);
  } finally {
    saveButton.disabled = false;
  }
});
document.querySelector("#agentSetupButton").addEventListener("click", showAgentSetup);
document.querySelector("#connectionHelpButton").addEventListener("click", () => connectionHelpDialog.showModal());
document.querySelector("#integrationHelpButton").addEventListener("click", () => integrationHelpDialog.showModal());
document.querySelector("#settingsIntegrationHelpButton").addEventListener("click", () => integrationHelpDialog.showModal());
document.querySelector("#closeIntegrationHelp").addEventListener("click", () => integrationHelpDialog.close());
document.querySelector("#integrationHelpDone").addEventListener("click", () => integrationHelpDialog.close());
document.querySelector("#closeConnectionHelp").addEventListener("click", () => connectionHelpDialog.close());
document.querySelector("#connectionHelpDone").addEventListener("click", () => connectionHelpDialog.close());
document.querySelector("#closeGameInfo").addEventListener("click", () => gameInfoDialog.close());
document.querySelector("#editTitle").addEventListener("input", updateCoverPositionPreview);
document.querySelector("#editCover").addEventListener("change", (event) => {
  if (coverPreviewObjectUrl) URL.revokeObjectURL(coverPreviewObjectUrl);
  coverPreviewObjectUrl = event.target.files[0] ? URL.createObjectURL(event.target.files[0]) : null;
  updateCoverPositionPreview();
});
document.querySelector("#coverPositionPreview").addEventListener("pointerdown", startCoverDrag);
document.querySelector("#coverPositionPreview").addEventListener("pointermove", moveCoverDrag);
document.querySelector("#coverPositionPreview").addEventListener("pointerup", stopCoverDrag);
document.querySelector("#coverPositionPreview").addEventListener("pointercancel", stopCoverDrag);
document.querySelector("#coverPositionPreview").addEventListener("keydown", nudgeCoverPosition);
document.querySelector("#brandHomeButton").addEventListener("click", () => window.scrollTo({top: 0, behavior: "smooth"}));
document.querySelector("#viewGridButton").addEventListener("click", () => setLibraryView("grid"));
document.querySelector("#viewListButton").addEventListener("click", () => setLibraryView("list"));
document.querySelector("#pageSize").addEventListener("change", (event) => {
  state.pageSize = Number(event.target.value);
  state.page = 1;
  localStorage.setItem("missionControlPageSize", String(state.pageSize));
  render();
});
document.querySelector("#search").addEventListener("input", (event) => { state.query = event.target.value; state.page = 1; render(); });
document.querySelector("#filter").addEventListener("change", (event) => { state.filter = event.target.value; state.page = 1; render(); });
window.addEventListener("resize", updateLcarsLayout);
document.fonts?.ready.then(updateLcarsLayout);

requestAnimationFrame(animateEnergyColor);
updateLcarsLayout();
updateLcarsSystemClock();
setInterval(updateLcarsSystemClock, 1000);
load();
