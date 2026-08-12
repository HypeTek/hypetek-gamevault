# HypeTek GameVault

GameVault ist eine private, Jellyfin-artige Bibliothek für die Installationsmedien
unter `/mnt/Titan/Game`. Die Web-App läuft auf TrueTitan; ein kleiner Agent auf dem
Windows-PC öffnet die bereits über SMB erreichbaren Dateien.

## Stand dieses MVP

- scannt ausschließlich die oberste Ebene von `/mnt/Titan/Game`
- erkennt direkte `setup*.exe`, `install*.exe`, `autorun.exe` und ISO-Abbilder
- zeigt CUE/BIN, Archive, DOS-/Emulator-Kandidaten und unklare Einträge sicher als
  manuelle Installation an
- bietet Suche, Filter, manuelle Titel/Plattformen/Beschreibungen und Cover-Uploads
- kann jeden Eintrag im Windows-Explorer öffnen
- startet direkte Installer oder bindet ISO-Dateien über Windows ein
- verwendet kurzlebige, nur einmal nutzbare Starttickets
- lässt den Games-Bestand im Container schreibgeschützt

GameVault installiert Spiele **nicht unbeaufsichtigt**. Vor jeder automatischen
Aktion zeigt der Windows-Agent Titel, Aktion und Quellpfad an und verlangt eine
Bestätigung. Archive und fremde Abbildformate werden niemals automatisch entpackt,
eingebunden oder ausgeführt.

## Architektur

1. Der Scanner katalogisiert `/games` (auf TrueTitan: `/mnt/Titan/Game`).
2. Metadaten und hochgeladene Cover liegen getrennt unter `/config`.
3. Der Browser fordert für eine Aktion ein 120 Sekunden gültiges Ticket an.
4. Das benutzerdefinierte Windows-Protokoll `hypetek-gamevault://` startet den Agenten.
5. Der Agent holt das Ticket ab, prüft den relativen Pfad gegen `Z:\Game` und fragt
   vor dem Start noch einmal nach.

## Projektstruktur

- `server/` – Web-App, Scanner und SQLite-Datenbank
- `windows-agent/` – PowerShell-Agent und Installation pro Windows-Benutzer
- `tests/` – Scanner-, Sicherheits- und Ticket-Tests
- `Dockerfile`, `docker-compose.yml` – Containerdefinition
- `.github/workflows/container.yml` – Tests und Veröffentlichung bei GHCR
- `INSTALL-TRUETITAN.md` – geplanter TrueNAS-Rollout
- `INSTALL-WINDOWS.md` – Einrichtung des Windows-Agents

## Lokaler Funktionstest

```bash
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt
GAMEVAULT_GAME_ROOT=/pfad/zu/Games \
GAMEVAULT_CONFIG_DIR=/tmp/gamevault-config \
GAMEVAULT_ADMIN_PASSWORD='ein-langes-kennwort' \
GAMEVAULT_AGENT_TOKEN='ein-zufaelliger-agent-token' \
GAMEVAULT_SECRET_KEY='ein-zufaelliger-session-key' \
.venv/bin/waitress-serve --host=127.0.0.1 --port=8080 --chdir=server app:app
```

## Bewusste Grenzen von Version 0.1

- Keine automatische Metadatensuche im Internet. Titel, Plattform, Beschreibung und
  Cover können in der Oberfläche gepflegt werden.
- Keine automatische Archivextraktion.
- CUE/BIN wird nur angezeigt und als manuell markiert.
- Noch keine Emulator- oder DOSBox-Profile.
- Ein eingebundenes ISO bleibt nach dem Start des Installers zunächst eingebunden und
  kann in Windows über „Auswerfen“ wieder getrennt werden.
- Die App darf nicht ungefiltert aus dem Internet veröffentlicht werden. Für entfernten
  Zugriff ist Tailscale oder ein korrekt abgesicherter Reverse Proxy vorgesehen.

## Tests

```bash
python -m unittest discover -s tests -v
```
