# TrueNAS-Installation und Upgrade

## Persistente Pfade

| Inhalt | Host | Container | Zugriff |
| --- | --- | --- | --- |
| Spiele | `/mnt/Titan/Game` | `/games` | nur lesen |
| Datenbank, Cover, Designs | `/mnt/Application/gamevault` | `/config` | lesen/schreiben |
| Translator-Sprachmodelle | `/mnt/Application/mission-control-translator` | `/home/libretranslate/.local` | lesen/schreiben |

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

    labels:
      com.hypetek.mission-control.deployment: "0.4.0"

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
      MISSION_CONTROL_TRANSLATOR_URL: "http://translator:5000"

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

  translator:
    image: libretranslate/libretranslate:v1.9.6
    pull_policy: always
    restart: unless-stopped

    environment:
      LT_DISABLE_WEB_UI: "true"
      LT_UPDATE_MODELS: "true"
      LT_LOAD_ONLY: "en,de,ru,it,fr,es,pt,pl,nl,tr"

    volumes:
      - type: bind
        source: /mnt/Application/mission-control-translator
        target: /home/libretranslate/.local

    healthcheck:
      test: ["CMD-SHELL", "./venv/bin/python scripts/healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 10m

    security_opt:
      - no-new-privileges:true
```

## Upgrade

1. In TrueNAS **Apps → gamevault → Edit** öffnen.
2. Den Translator-Dienst und `MISSION_CONTROL_TRANSLATOR_URL` aus der YAML ergänzen.
3. `pull_policy: always` und den Deployment-Label der Version beibehalten.
4. Speichern und auf **Running** warten.
5. Browser mit `Strg+F5` aktualisieren.
6. Unter **Einstellungen** Design, Hintergrund und Ausschlüsse festlegen.

Die tatsächlich laufende Version lässt sich anschließend ohne Anmeldung prüfen:

```text
http://TRUENAS-IP:9998/health
```

Für Version 0.4.0 muss die Antwort unter anderem `"version":"0.4.0"`,
`"agent_api":3` und `"translator_managed":true` enthalten. So lässt sich ein noch laufendes altes Container-Image
sofort von einem aktuellen Image unterscheiden.

Weder Agent-Token noch Admin-Passwort müssen beim Upgrade geändert werden. Ein geänderter
Secret-Key meldet lediglich bestehende Browser-Sitzungen ab.

## Integrierter lokaler Translator

Die vollständige YAML enthält einen LibreTranslate-kompatiblen zweiten Dienst. Er
ist ausschließlich innerhalb des App-Netzes als `http://translator:5000`
erreichbar; Port 5000 wird bewusst nicht am TrueNAS-Host veröffentlicht. Mission
Control übernimmt diese Adresse automatisch. Die vollständige Anleitung kann
in Mission Control unter **API-/Translator-Hilfe** als PDF heruntergeladen oder
per QR-Code auf einem zweiten Gerät geöffnet werden.

Beim ersten Start lädt LibreTranslate das verwaltete Paket für Deutsch,
Englisch, Russisch, Italienisch, Französisch, Spanisch, Portugiesisch, Polnisch,
Niederländisch, Türkisch und Ukrainisch. Die Erkennung gemischter Inhalte ist nicht
auf diese Ausgangssprachen festgelegt; verarbeitet werden alle im Translator
installierten Sprachen. Der erste Modell-Download kann mehrere Minuten dauern.
Der Zustand lässt sich danach unter
**Einstellungen → Verbindung testen** prüfen; Mission Control zeigt dort auch die
vom Container gemeldeten Sprachcodes an. Zusätzliche Modelle werden über
`LT_LOAD_ONLY` kommasepariert ergänzt, etwa `fr,es,it,pl,tr,ar,zh,ja,ko`.

Der Translator benötigt keinen externen API-Key. Die vorhandenen Felder bleiben
für Nutzer kompatibler externer Translator-Dienste erhalten.

## Berechtigungen

Mission Control läuft als UID/GID `568` (`apps`). Für `/mnt/Titan/Game` genügen Lesen
und Durchqueren; Schreib-, Änderungs- und Löschrechte sind nicht erforderlich. Der
Scanner überspringt nicht zugängliche Ordner und zusätzlich alle unter
**Einstellungen → Scanner-Ausschlüsse** eingetragenen Namen.

LibreTranslate 1.9.6 verwendet im Container UID/GID `1032:65534` und benötigt
Schreibzugriff auf sein Modell-Dataset. Einmalig auf dem TrueNAS-Host ausführen:

```bash
sudo chown -R 1032:65534 /mnt/Application/mission-control-translator
```

Bei einem anderen Translator-Image lässt sich dessen Identität vorab mit
`docker run --rm --entrypoint id IMAGE` ermitteln.
---

Copyright © 2026 Michael Härtwig · HypeTek
