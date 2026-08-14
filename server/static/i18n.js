(() => {
"use strict";

// Small integrated UI packs. Game descriptions use the separately configured
// Translator and are deliberately not mixed with these interface strings.
const UI_PACKS = {
  de: {
    "nav.agent": "Agent-Setup", "nav.settings": "Einstellungen", "nav.scan": "Bibliothek scannen", "nav.logout": "Abmelden",
    "hero.title": "Deine Games. Ein Klick entfernt.", "hero.subtitle": "Installationsmedien über das verbundene SMB-Laufwerk verwalten.",
    "search.placeholder": "Titel durchsuchen …", "filter.all": "Alle Typen", "filter.favorites": "★ Favoriten", "filter.setup": "Direktes Setup", "filter.manual": "Nur anzeigen", "filter.archive": "Archiv", "filter.image": "Sonderabbild",
    "view.grid": "Kacheln", "view.list": "Liste", "view.perPage": "Pro Seite",
    "settings.title": "Mission Control konfigurieren", "settings.server": "Servername", "settings.archive": "Archivname", "settings.profiles": "Designprofile", "settings.manage": "Profile verwalten", "settings.crosshair": "Fadenkreuz als Mauszeiger", "settings.exclusions": "Scanner-Ausschlüsse", "settings.contentLanguage": "Sprache der Spielinhalte (optional)", "settings.uiLanguage": "Sprache der Oberfläche", "settings.translator": "Mission Control Translator (optional)", "settings.translatorKey": "Translator-API-Key (nur falls erforderlich)", "settings.save": "Speichern", "settings.cancel": "Abbrechen",
    "profiles.visual": "VISUAL CONFIGURATION", "profiles.title": "Designprofile", "profiles.new": "+ Neues Profil", "profiles.back": "Zurück", "profiles.save": "Profil speichern", "profiles.saved": "✓ Profil gespeichert und aktiviert", "profiles.saving": "Speichert …", "profiles.activate": "Aktivieren", "profiles.duplicate": "Duplizieren", "profiles.edit": "Edit", "profiles.delete": "Löschen", "profiles.active": "AKTIV", "profiles.name": "Profilname", "profiles.style": "Stil", "profiles.font": "Schriftstil", "profiles.background": "Eigenes Profil-Hintergrundbild", "profiles.removeBackground": "Profil-Hintergrund entfernen", "profiles.colorBackground": "Hintergrund", "profiles.colorWindow": "Fenster", "profiles.colorCards": "Karten", "profiles.colorText": "Text", "profiles.colorMuted": "Gedämpft", "profiles.colorPrimary": "Primär", "profiles.colorSecondary": "Sekundär", "profiles.colorFrame": "Rahmen", "profiles.colorFrom": "Streifen: von", "profiles.colorTo": "Streifen: bis", "profiles.dim": "Hintergrund-Abdunklung", "profiles.blur": "Hintergrund-Unschärfe",
    "game.install": "Installieren", "game.mountInstall": "Einbinden & installieren", "game.folder": "Ordner öffnen", "game.favorite": "★ Favorit", "game.makeFavorite": "☆ Als Favorit markieren", "game.edit": "Edit",
    "stats.entries": "Einträge", "stats.setups": "Setups", "stats.isos": "ISOs", "pagination.previous": "Zurück", "pagination.next": "Weiter", "pagination.page": "Seite {current} von {total}",
    "scan.running": "Scanne Bibliothek …", "scan.done": "{count} Einträge gescannt"
  },
  en: {
    "nav.agent": "Agent setup", "nav.settings": "Settings", "nav.scan": "Scan library", "nav.logout": "Log out",
    "hero.title": "Your games. One click away.", "hero.subtitle": "Manage installation media through the connected SMB drive.",
    "search.placeholder": "Search titles …", "filter.all": "All types", "filter.favorites": "★ Favorites", "filter.setup": "Direct setup", "filter.manual": "Show only", "filter.archive": "Archive", "filter.image": "Special image",
    "view.grid": "Tiles", "view.list": "List", "view.perPage": "Per page",
    "settings.title": "Configure Mission Control", "settings.server": "Server name", "settings.archive": "Archive name", "settings.profiles": "Design profiles", "settings.manage": "Manage profiles", "settings.crosshair": "Crosshair pointer", "settings.exclusions": "Scanner exclusions", "settings.contentLanguage": "Game-content language (optional)", "settings.uiLanguage": "Interface language", "settings.translator": "Mission Control Translator (optional)", "settings.translatorKey": "Translator API key (only if required)", "settings.save": "Save", "settings.cancel": "Cancel",
    "profiles.visual": "VISUAL CONFIGURATION", "profiles.title": "Design profiles", "profiles.new": "+ New profile", "profiles.back": "Back", "profiles.save": "Save profile", "profiles.saved": "✓ Profile saved and activated", "profiles.saving": "Saving …", "profiles.activate": "Activate", "profiles.duplicate": "Duplicate", "profiles.edit": "Edit", "profiles.delete": "Delete", "profiles.active": "ACTIVE", "profiles.name": "Profile name", "profiles.style": "Style", "profiles.font": "Font style", "profiles.background": "Custom profile background", "profiles.removeBackground": "Remove profile background", "profiles.colorBackground": "Background", "profiles.colorWindow": "Panels", "profiles.colorCards": "Cards", "profiles.colorText": "Text", "profiles.colorMuted": "Muted", "profiles.colorPrimary": "Primary", "profiles.colorSecondary": "Secondary", "profiles.colorFrame": "Borders", "profiles.colorFrom": "Strip: from", "profiles.colorTo": "Strip: to", "profiles.dim": "Background dimming", "profiles.blur": "Background blur",
    "game.install": "Install", "game.mountInstall": "Mount & install", "game.folder": "Open folder", "game.favorite": "★ Favorite", "game.makeFavorite": "☆ Add to favorites", "game.edit": "Edit",
    "stats.entries": "Entries", "stats.setups": "Setups", "stats.isos": "ISOs", "pagination.previous": "Previous", "pagination.next": "Next", "pagination.page": "Page {current} of {total}",
    "scan.running": "Scanning library …", "scan.done": "{count} entries scanned"
  },
  ru: {
    "nav.agent": "Настройка агента", "nav.settings": "Настройки", "nav.scan": "Сканировать библиотеку", "nav.logout": "Выйти",
    "hero.title": "Ваши игры. В одном клике.", "hero.subtitle": "Управление установочными носителями через подключённый SMB-диск.",
    "search.placeholder": "Поиск игр …", "filter.all": "Все типы", "filter.favorites": "★ Избранное", "filter.setup": "Прямая установка", "filter.manual": "Только показать", "filter.archive": "Архив", "filter.image": "Специальный образ",
    "view.grid": "Плитки", "view.list": "Список", "view.perPage": "На странице",
    "settings.title": "Настройка Mission Control", "settings.server": "Имя сервера", "settings.archive": "Имя архива", "settings.profiles": "Профили дизайна", "settings.manage": "Управление профилями", "settings.crosshair": "Курсор-прицел", "settings.exclusions": "Исключения сканера", "settings.contentLanguage": "Язык описаний игр (необязательно)", "settings.uiLanguage": "Язык интерфейса", "settings.translator": "Mission Control Translator (необязательно)", "settings.translatorKey": "API-ключ переводчика (если требуется)", "settings.save": "Сохранить", "settings.cancel": "Отмена",
    "profiles.visual": "ВИЗУАЛЬНАЯ НАСТРОЙКА", "profiles.title": "Профили дизайна", "profiles.new": "+ Новый профиль", "profiles.back": "Назад", "profiles.save": "Сохранить профиль", "profiles.saved": "✓ Профиль сохранён и активирован", "profiles.saving": "Сохранение …", "profiles.activate": "Активировать", "profiles.duplicate": "Дублировать", "profiles.edit": "Изменить", "profiles.delete": "Удалить", "profiles.active": "АКТИВЕН", "profiles.name": "Имя профиля", "profiles.style": "Стиль", "profiles.font": "Стиль шрифта", "profiles.background": "Фон профиля", "profiles.removeBackground": "Удалить фон профиля", "profiles.colorBackground": "Фон", "profiles.colorWindow": "Окна", "profiles.colorCards": "Карточки", "profiles.colorText": "Текст", "profiles.colorMuted": "Приглушённый", "profiles.colorPrimary": "Основной", "profiles.colorSecondary": "Дополнительный", "profiles.colorFrame": "Рамки", "profiles.colorFrom": "Полоса: начало", "profiles.colorTo": "Полоса: конец", "profiles.dim": "Затемнение фона", "profiles.blur": "Размытие фона",
    "game.install": "Установить", "game.mountInstall": "Подключить и установить", "game.folder": "Открыть папку", "game.favorite": "★ Избранное", "game.makeFavorite": "☆ Добавить в избранное", "game.edit": "Изменить",
    "stats.entries": "Записи", "stats.setups": "Установщики", "stats.isos": "ISO", "pagination.previous": "Назад", "pagination.next": "Далее", "pagination.page": "Страница {current} из {total}",
    "scan.running": "Сканирование библиотеки …", "scan.done": "Просканировано записей: {count}"
  }
};

let currentUiLanguage = "de";

function tr(key, variables = {}) {
  const pack = UI_PACKS[currentUiLanguage] || UI_PACKS.de;
  let value = pack[key] || UI_PACKS.de[key] || key;
  Object.entries(variables).forEach(([name, replacement]) => {
    value = value.split(`{${name}}`).join(String(replacement));
  });
  return value;
}

function setNodeText(selector, key) {
  const node = document.querySelector(selector);
  if (node) node.textContent = tr(key);
}

function setLabelLead(selector, key) {
  const label = document.querySelector(selector);
  if (!label) return;
  const textNode = [...label.childNodes].find((node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
  if (textNode) textNode.textContent = `${tr(key)} `;
}

function applyUiLanguage(language) {
  currentUiLanguage = Object.prototype.hasOwnProperty.call(UI_PACKS, language) ? language : "de";
  document.documentElement.lang = currentUiLanguage;
  document.documentElement.dir = "ltr";
  const text = {
    "#agentSetupButton": "nav.agent", "#settingsButton": "nav.settings", "#scanButton": "nav.scan", ".topbar nav form button": "nav.logout",
    ".hero h1": "hero.title", ".hero>div:first-child>p:last-child": "hero.subtitle",
    "#filter option[value='all']": "filter.all", "#filter option[value='favorites']": "filter.favorites", "#filter option[value='direct_setup']": "filter.setup", "#filter option[value='manual']": "filter.manual", "#filter option[value='archive']": "filter.archive", "#filter option[value='manual_image']": "filter.image",
    "#viewGridButton span": "view.grid", "#viewListButton span": "view.list",
    "#settingsForm .dialog-head h2": "settings.title", "#designProfilesButton": "settings.manage", "#saveSettingsButton": "settings.save",
    "#designProfilesDialog .eyebrow": "profiles.visual", "#designProfilesDialog h2": "profiles.title", "#newDesignProfileButton": "profiles.new", "#designProfilesBackButton": "profiles.back", "#cancelDesignProfileEdit": "profiles.back", "#saveDesignProfileButton": "profiles.save", "#removeDesignProfileBackground": "profiles.removeBackground"
  };
  Object.entries(text).forEach(([selector, key]) => setNodeText(selector, key));
  document.querySelector("#search")?.setAttribute("placeholder", tr("search.placeholder"));
  const leads = {
    "label:has(#settingServerName)": "settings.server", "label:has(#settingLibraryName)": "settings.archive", "label:has(#settingExclusions)": "settings.exclusions", "label:has(#settingContentLanguage)": "settings.contentLanguage", "label:has(#settingUiLanguage)": "settings.uiLanguage", "label:has(#settingTranslatorUrl)": "settings.translator", "label:has(#settingTranslatorApiKey)": "settings.translatorKey", ".page-size-label": "view.perPage",
    "label:has(#designProfileName)": "profiles.name", "label:has(#designProfileFont)": "profiles.font", "label:has(#designProfileBackground)": "profiles.background", "label:has([data-profile-color='background'])": "profiles.colorBackground", "label:has([data-profile-color='panel'])": "profiles.colorWindow", "label:has([data-profile-color='panel_alt'])": "profiles.colorCards", "label:has([data-profile-color='text'])": "profiles.colorText", "label:has([data-profile-color='muted'])": "profiles.colorMuted", "label:has([data-profile-color='primary'])": "profiles.colorPrimary", "label:has([data-profile-color='secondary'])": "profiles.colorSecondary", "label:has([data-profile-color='line'])": "profiles.colorFrame", "label:has([data-profile-color='energy_start'])": "profiles.colorFrom", "label:has([data-profile-color='energy_end'])": "profiles.colorTo", "label:has(#designProfileOpacity)": "profiles.dim", "label:has(#designProfileBlur)": "profiles.blur"
  };
  // :has() is supported by current browsers. An older browser must still be
  // able to initialize every functional control, so translation selectors are
  // isolated and may never abort the application bootstrap.
  Object.entries(leads).forEach(([selector, key]) => {
    try { setLabelLead(selector, key); } catch (_error) { /* optional translation only */ }
  });
  setNodeText(".profile-style-picker legend", "profiles.style");
  document.querySelectorAll("#settingsForm button[value='cancel']").forEach((button) => { button.textContent = tr("settings.cancel"); });
  document.dispatchEvent(new CustomEvent("mission-control-language-changed"));
}

window.MissionControlI18n = {applyUiLanguage, tr};
})();
