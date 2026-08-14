# TrueNAS-Installation und Upgrade

## Persistente Pfade

| Inhalt | Host | Container | Zugriff |
| --- | --- | --- | --- |
| Spiele | `/mnt/Titan/Game` | `/games` | nur lesen |
| Datenbank, Cover, Designs | `/mnt/Application/gamevault` | `/config` | lesen/schreiben |

Das Upgrade von 0.1 auf 0.2 behält die bestehende SQLite-Datenbank und alle Cover. Die
neue Datei `mission-control-settings.json` wird beim ersten Start ergänzt.

## Compose-YAML für TrueNAS SCALE

Vor dem Einfügen drei eigene Werte verwenden. Schlüssel niemals in GitHub oder einen
öffentlichen Chat kopieren.

```yaml
services:
  gamevault:
    image: ghcr.io/hypetek/hypetek-gamevault:latest
    pull_policy: always
    restart: unless-stopped

    ports:
      - "9998:8080"

    environment:
      GAMEVAULT_ADMIN_PASSWORD: "HIER_ADMIN_PASSWORT"
      GAMEVAULT_AGENT_TOKEN: "HIER_AGENT_TOKEN"
      GAMEVAULT_CONFIG_DIR: "/config"
      GAMEVAULT_GAME_ROOT: "/games"
      GAMEVAULT_SECRET_KEY: "HIER_SECRET_KEY"
      MISSION_CONTROL_SERVER_NAME: "TrueTitan"
      MISSION_CONTROL_LIBRARY_NAME: "TrueTitan Game Archive"

    volumes:
      - type: bind
        source: /mnt/Titan/Game
        target: /games
        read_only: true

      - type: bind
        source: /mnt/Application/gamevault
        target: /config

    security_opt:
      - no-new-privileges:true

    cap_drop:
      - ALL
```

## Upgrade

1. In TrueNAS **Apps → gamevault → Edit** öffnen.
2. Die beiden `MISSION_CONTROL_*`-Werte ergänzen.
3. `pull_policy: always` beibehalten.
4. Speichern und auf **Running** warten.
5. Browser mit `Strg+F5` aktualisieren.
6. Unter **Einstellungen** Design, Hintergrund und Ausschlüsse festlegen.

Die tatsächlich laufende Version lässt sich anschließend ohne Anmeldung prüfen:

```text
http://TRUENAS-IP:9998/health
```

Für Version 0.3.3 muss die Antwort unter anderem `"version":"0.3.3"` und
`"agent_api":3` enthalten. So lässt sich ein noch laufendes altes Container-Image
sofort von einem aktuellen Image unterscheiden.

Weder Agent-Token noch Admin-Passwort müssen beim Upgrade geändert werden. Ein geänderter
Secret-Key meldet lediglich bestehende Browser-Sitzungen ab.

## Optionaler lokaler Translator

Die Datei `TRANSLATOR-TRUENAS.yml.example` enthält den zusätzlichen
LibreTranslate-kompatiblen Dienst. Er wird unter `services:` derselben Custom App
ergänzt und ist anschließend innerhalb des App-Netzes als
`http://translator:5000` erreichbar. Die vollständige, bebilderte Anleitung kann
in Mission Control unter **API-/Translator-Hilfe** als PDF heruntergeladen oder
per QR-Code auf einem zweiten Gerät geöffnet werden.

## Berechtigungen

Der Container läuft als UID/GID `568` (`apps`). Für `/mnt/Titan/Game` genügen Lesen und
Durchqueren; Schreib-, Änderungs- und Löschrechte sind nicht erforderlich. Der Scanner
überspringt nicht zugängliche Ordner und zusätzlich alle unter **Einstellungen →
Scanner-Ausschlüsse** eingetragenen Namen.
---

Copyright © 2026 Michael Härtwig · HypeTek
