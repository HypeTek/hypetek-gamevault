# TrueNAS-Installation und Upgrade

## Persistente Pfade

| Inhalt | Host | Container | Zugriff |
| --- | --- | --- | --- |
| Spiele | `/mnt/Titan/Game` | `/games` | nur lesen |
| Weitere Bibliothek (Beispiel) | `/mnt/Titan/Archive2` | `/libraries/archive2` | nur lesen |
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
    image: ghcr.io/hypetek/hypetek-gamevault:0.9.0-rc.3
    pull_policy: always
    restart: unless-stopped

    labels:
      com.hypetek.mission-control.deployment: "0.9.0-rc.3"

    ports:
      - "9998:8080"

    environment:
      GAMEVAULT_ADMIN_PASSWORD: "HIER_ADMIN_PASSWORT"
      GAMEVAULT_AGENT_TOKEN: "HIER_AGENT_TOKEN"
      GAMEVAULT_CONFIG_DIR: "/config"
      GAMEVAULT_GAME_ROOT: "/games"
      GAMEVAULT_ALLOWED_LIBRARY_ROOTS: "/games,/libraries"
      GAMEVAULT_WINDOWS_ROOT: "Z:\\Game"
      GAMEVAULT_SECRET_KEY: "HIER_SECRET_KEY"
      MISSION_CONTROL_SERVER_NAME: "TrueTitan"
      MISSION_CONTROL_LIBRARY_NAME: "TrueTitan Game Archive"
      MISSION_CONTROL_TRANSLATOR_URL: "http://translator:5000"

    volumes:
      - type: bind
        source: /mnt/Titan/Game
        target: /games
        read_only: true

      # Optionales Beispiel für ein weiteres Archiv. Erst einkommentieren und
      # den Hostpfad anpassen, wenn das Dataset wirklich existiert:
      # - type: bind
      #   source: /mnt/Titan/Archive2
      #   target: /libraries/archive2
      #   read_only: true

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
      LT_LOAD_ONLY: "en,de,ru,it,fr,es,pt,pl,nl,tr,ar,zh"

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

Für Version 0.9.0-rc.3 muss die Antwort unter anderem `"version":"0.9.0-rc.3"`,
`"agent_api":3` und `"translator_managed":true` enthalten. So lässt sich ein noch laufendes altes Container-Image
sofort von einem aktuellen Image unterscheiden.

Weder Agent-Token noch Admin-Passwort müssen beim Upgrade geändert werden. Ein geänderter
Secret-Key meldet lediglich bestehende Browser-Sitzungen ab.

## Mehrere Spielebibliotheken

Unter **Einstellungen → Spielebibliotheken** wird beim Hinzufügen zuerst der Typ gewählt:

- **Netzwerk/TrueNAS:** dauerhafte ID, Name, eingebundener Containerpfad sowie passende
  Windows-/SMB- und optionale Linux-Clientpfade. Die primäre Bibliothek bleibt mit
  `/games` kompatibel. Zusätzliche Serverarchive werden unter `/libraries/<id>`
  nur-lesbar in der YAML eingebunden.
- **Lokale Windows-Festplatte:** dauerhafte ID, Name und lokaler Windows-Pfad. Es gibt
  absichtlich weder Container- noch Linux-Feld. Der TrueNAS-Container kann ein Laufwerk
  wie `F:\\Games` nicht sehen; der installierte Windows-Agent scannt es stattdessen auf
  ausdrücklichen Befehl mit einem einmaligen, 15 Minuten gültigen Auftrag.

Nach dem Speichern kann jede Bibliothek einzeln oder gemeinsam gescannt und im Dashboard
gefiltert werden. Für einen lokalen Windows-Scan müssen PC, Laufwerk und aktueller Agent
erreichbar sein. Eine rein lokale Bibliothek benötigt keinen zusätzlichen YAML-Mount.

Beim ersten Start eines Spiels aus einer zusätzlichen Bibliothek zeigt der Windows-
Agent den in Mission Control hinterlegten, erreichbaren SMB-Pfad an. Erst nach der
Bestätigung des Benutzers wird diese Zuordnung ausschließlich lokal im Agent gespeichert.
Ein Serverpfad wird daher niemals stillschweigend als Windows-Pfad übernommen.

## Integrierter lokaler Translator

Die vollständige YAML enthält einen LibreTranslate-kompatiblen zweiten Dienst. Er
ist ausschließlich innerhalb des App-Netzes als `http://translator:5000`
erreichbar; Port 5000 wird bewusst nicht am TrueNAS-Host veröffentlicht. Mission
Control übernimmt diese Adresse automatisch. Die vollständige Anleitung kann
in Mission Control unter **API-/Translator-Hilfe** als PDF heruntergeladen oder
per QR-Code auf einem zweiten Gerät geöffnet werden.

Beim ersten Start lädt LibreTranslate die verwalteten nativen Modelle für Deutsch,
Englisch, Russisch, Italienisch, Französisch, Spanisch, Portugiesisch, Polnisch,
Niederländisch, Türkisch, Arabisch und vereinfachtes Chinesisch. Die Erkennung
gemischter Inhalte ist nicht auf diese Ausgangssprachen festgelegt; verarbeitet
werden alle im Translator installierten Sprachen. Der erste Modell-Download kann
mehrere Minuten dauern.

`Klingon (Beta)` und `Elvish / Sindarin (Beta)` sind keine zusätzlichen
LibreTranslate-Modelle. Mission Control erzeugt diese beiden experimentellen Ziele
lokal aus einer englischen Zwischenübersetzung mit einem konservativen Wortschatz.
Unbekannte Namen und Fachbegriffe bleiben dabei bewusst erhalten; die Ergebnisse
sind ausdrücklich keine kanonischen Vollübersetzungen. Das englische Modell muss
dafür verfügbar bleiben.

Der Zustand lässt sich danach unter **Einstellungen → Verbindung testen** prüfen;
Mission Control zeigt dort die nativ gemeldeten Sprachcodes und stellt im
Spieleinhalts-Dropdown zusätzlich die beiden Beta-Ziele bereit. Weitere echte Modelle
werden über `LT_LOAD_ONLY` kommasepariert ergänzt, etwa `ja,ko`.

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
