# HypeTek Mission Control

HypeTek Mission Control ist eine selbst gehostete Spielebibliothek und ein sicherer
Windows-Launcher für Installationsmedien auf TrueNAS oder einem anderen Docker-Host.
Die Anwendung katalogisiert einen bestehenden Games-Ordner, ohne dessen Inhalt zu
verändern oder in ein neues Format zu zwingen.

## Funktionen in Version 0.6.3

- mehrere getrennte Netzwerkbibliotheken mit eigener TrueNAS-, Windows-/SMB- und Linux-Zuordnung verwalten
- rein lokale Windows-Bibliotheken ohne erfundenen Containerpfad über den Windows-Agent scannen
- Bibliotheken einzeln oder gemeinsam scannen und im Dashboard filtern
- kompakte Seitennummerierung mit direktem Sprung zur ersten und letzten Seite
- vorhandene 0.4.x-Datenbank automatisch und ohne Verlust als primäre Bibliothek übernehmen

- direkte Setup-Programme und Windows-ISOs automatisch erkennen
- kryptische Ordnercodes automatisch mit aussagekräftigeren ISO-, Archiv- oder Abbildnamen ersetzen
- CUE/BIN, Archive und unklare Einträge bewusst nur anzeigen
- vorhandene SMB-Bibliothek schreibgeschützt einbinden
- Suche, Filter, manuelle Metadaten und Cover-Uploads
- Favoritenmarkierung im Spiele-Infofenster und eigener Favoritenfilter
- Mission-, Cyberpunk-, LCARS-Console- und Midnight-Ausgangsprofile
- eigene speicherbare Designprofile mit Farben, Hintergrundbild und Effekten
- portable, versionierte Designpakete mit sicher geprüftem Profil-Export und -Import
- frei wählbarer Farbverlauf für den Energiestreifen je Designprofil
- Design unabhängig mit Karten-/Fensterstil und Schriftgruppe kombinieren
- Live-Vorschau vor dem Speichern eines Profils
- optionales Fadenkreuz als Mauszeiger
- frei benennbarer Server und Archivtitel
- konfigurierbare Scanner-Ausschlüsse
- Ordner öffnen, Setup starten und ISO einbinden
- einmalige, 120 Sekunden gültige Starttickets
- geführter Windows-EXE-Installer mit Serveradresse, Games-Pfad und Agent-Token
- unsichtbarer Agentenstart; nur die Sicherheitsabfrage wird angezeigt
- Windows PowerShell 5.1 und PowerShell 7
- gemeinsame, manuell ausgelöste Metadatensuche in TheGamesDB und RAWG mit Vorschau und Quellenlink
- Spiele-Infofenster mit lokal gespeichertem Spielinhalt und getrennten eigenen Bemerkungen
- Installations- und Ordneraktionen direkt im Spiele-Infofenster
- integrierter lokaler Mission Control Translator als interner zweiter Container
- automatisches Translator-Ziel ohne externen Port oder API-Key
- gemeinsame Sprachauswahl für Oberfläche, Spieleinhalte und Windows-Agent in Deutsch, Englisch, Russisch, Italienisch, Französisch, Spanisch, Portugiesisch, Polnisch, Niederländisch und Türkisch
- abschnittsweise Quellsprachenerkennung für gemischte TheGamesDB-Spielinhalte
- Translator-Verbindungstest mit Anzeige der tatsächlich verfügbaren Sprachcodes
- sichere Windows-Agent-Erkennung über kurzlebige Prüftickets
- integrierte API-/Translator-Hilfe mit PDF-Download und QR-Code
- klar geführte Windows-Agent-Ersteinrichtung mit EXE, Installation und Verbindungstest
- eingeklappter PowerShell-Fallback für Experten
- maßstabsgetreue Kartenvorschau mit direkter vertikaler Bildausrichtung per Maus oder Tastatur
- wirklich unabhängig vom Header fixiertes HypeTek-Logo
- umschaltbare Kachel- und Listenansicht mit gespeicherter Auswahl
- Seitennavigation mit 12, 24, 48 oder 96 Einträgen pro Seite
- sichtbare laufende Version und HypeTek-Urhebervermerk in den Einstellungen
- zum Linienverlauf farbsynchron glimmender Energiepunkt statt weißem Laufbalken
- anklickbares HypeTek-Logo als Rücksprung zum Seitenanfang
- mitgelieferte TXT-Kurzanleitung im PowerShell-Fallback-Paket
- vollständiger integrierter Oberflächenkern für Deutsch, Englisch und Russisch; unabhängig von der Sprache der Spielinhalte
- automatische Browser-Spracherkennung mit Fallback von Region zu Basissprache und anschließend Englisch
- direkt prüfbarer Status des integrierten Mission Control Translators
- Ein-Instanz-Start der installierten PWA: erneutes Öffnen fokussiert das vorhandene App-Fenster
- Wartungszentrale für vollständige Sicherungen, Wiederherstellung, Diagnose und Update-Prüfung
- automatische rotierende Sicherungen vor Bibliotheksscans und ein frischer Rücksetzpunkt vor jeder Wiederherstellung
- Sicherungs- und Diagnosepakete ohne Kennwörter, Tokens oder API-Keys

Mission Control installiert Spiele niemals unbeaufsichtigt. Vor jeder automatischen
Aktion zeigt der Agent Titel, Aktion und vollständigen SMB-Pfad an. Erst nach einer
Bestätigung wird Explorer, Setup oder ISO-Installer geöffnet.

## Architektur

1. Der Server scannt bei Netzwerkbibliotheken ausschließlich die oberste Ebene des jeweiligen eingebundenen Containerpfads.
   Rein lokale Windows-Bibliotheken werden auf ausdrücklichen Wunsch vom authentifizierten Windows-Agent gescannt.
2. SQLite-Datenbank, Cover, Hintergrund und Einstellungen liegen unter `/config`.
3. Der Browser fordert für eine Aktion ein einmal verwendbares Ticket an.
4. Das Windows-Protokoll `hypetek-gamevault://` startet den lokalen Agenten verborgen.
5. Der Agent authentifiziert sich, begrenzt jeden Pfad auf die konfigurierte SMB-Wurzel
   und fordert eine lokale Bestätigung an.

Der technische Protokollname bleibt in 0.2 aus Upgrade-Gründen unverändert. Branding
und Benutzeroberfläche heißen bereits HypeTek Mission Control.

## Projektstruktur

- `server/` – Flask-Web-App, Scanner, Einstellungen und SQLite
- `windows-agent/` – PowerShell-5/7-kompatibler Fallback-Agent
- `windows-installer/` – Inno-Setup-Projekt für den geführten EXE-Installer
- `tests/` – Scanner-, Einstellungs-, Ticket- und Sicherheitstests
- `.github/workflows/container.yml` – Tests, Container und Windows-Installer
- `INSTALL-TRUENAS.md` – Installation und Upgrade auf TrueNAS SCALE
- `INSTALL-WINDOWS.md` – Windows-Agent und Diagnose
- `TRANSLATOR-TRUENAS.yml.example` – Auszug des integrierten Translator-Dienstes für TrueNAS

## Container

Das veröffentlichte Image lautet weiterhin:

```text
ghcr.io/hypetek/hypetek-gamevault:latest
```

Die alten `GAMEVAULT_*`-Umgebungsvariablen bleiben für Upgrades gültig. Allgemeine
Darstellungswerte werden in `/config/mission-control-settings.json`, eigene Profile
atomar in `/config/mission-control-designs.json` gespeichert.

### Optionale Metadatensuche in TheGamesDB und RAWG

Unter **Einstellungen** können eigene API-Keys für TheGamesDB und RAWG hinterlegt werden.
Mission Control gibt die gespeicherten Keys nicht an den Browser zurück. Sind beide Keys
vorhanden, durchsucht ein Klick auf **Suchen** zuerst TheGamesDB und danach RAWG. Die
Treffer erscheinen ohne getrennte Ansicht in genau dieser Reihenfolge in derselben Liste.
Fällt ein Anbieter aus, bleiben Treffer des anderen nutzbar und die Oberfläche zeigt eine
Warnung. Cover und Metadaten werden erst nach manueller Auswahl lokal gespeichert.

API-Key: <https://api.thegamesdb.net/key.php>  
Offizielle API-Dokumentation: <https://api.thegamesdb.net/>

Auch mit nur einem der beiden Keys bleibt die Suche verwendbar. Ohne API-Key bleiben
Bibliothek, manuelle Cover-Uploads und alle Startfunktionen unverändert nutzbar.

Beim Anlegen einer Bibliothek wird zuerst ihr Typ gewählt:

- **Netzwerk/TrueNAS:** Mission Control scannt den eingebundenen Containerpfad. Derselbe
  Bestand erhält eine Windows-Laufwerks-/UNC-Zuordnung und optional eine absolute
  Linux-Clientzuordnung. Beispiel: `/games`, `Z:\\Game` und `/mnt/games` zeigen auf
  denselben Inhalt, nur aus Sicht der jeweiligen Plattform.
- **Lokale Windows-Festplatte:** Nur Name und Windows-Pfad werden benötigt, etwa
  `F:\\Games`. Der installierte Windows-Agent scannt den lokalen Bestand über einen
  kurzlebigen authentifizierten Auftrag. TrueNAS muss und kann dieses Laufwerk nicht
  als Containerpfad erreichen.

Der Linux-Pfad einer Netzwerkbibliothek wird bereits sicher validiert und in
Starttickets bereitgestellt; ein vollständiger nativer Linux-Agent gehört weiterhin
zur Roadmap. Eine lokale Windows-Bibliothek ist nur scan- und startfähig, während der
zugehörige Windows-PC und sein Agent erreichbar sind.

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions führt die Tests vor jedem Container- und Installer-Build aus. Bei einem
Push erzeugt der Workflow aus `VERSION` automatisch ein versioniertes Container-Image
und Release; der Windows-Agent wird als Release-Artefakt veröffentlicht.

## Updates nach GitHub übertragen

Für vollständige Updates unter Windows wird **GitHub Desktop** empfohlen:

1. Das Repository einmal mit GitHub Desktop klonen.
2. Den Inhalt des neuen Mission-Control-Pakets in diesen lokalen Repository-Ordner kopieren.
3. In GitHub Desktop alle erkannten Änderungen kontrollieren, committen und mit **Push origin** hochladen.
4. Unter **Actions** warten, bis Python-Tests, Container-Build und Windows-Installer grün sind.

Damit wird auch `.github/workflows/container.yml` zuverlässig übernommen. Beim manuellen
Upload im Browser kann der mit einem Punkt beginnende Ordner leicht übersehen werden;
ohne diese Datei werden weder Tests noch Container oder Windows-Agent gebaut.

### GitHub-Repository umbenennen

Das Repository kann unter **Settings → General → Repository name** beispielsweise in
`hypetek-mission-control` umbenannt werden. GitHub leitet bestehende Web-, Clone-,
Fetch- und Push-Adressen auf den neuen Namen weiter. Der lokale Clone sollte danach
trotzdem auf die neue Adresse umgestellt werden. GitHub Desktop bietet dies beim
nächsten Abruf an; alternativ gilt:

```bash
git remote set-url origin https://github.com/HypeTek/hypetek-mission-control.git
```

Der technische Protokollname `hypetek-gamevault://` und das bestehende Container-Image
`ghcr.io/hypetek/hypetek-gamevault` bleiben zunächst absichtlich kompatibel. Eine
spätere kontrollierte Umbenennung des Images benötigt eine Übergangsphase in der
TrueNAS-YAML und ist nicht dasselbe wie die gefahrlose Repository-Umbenennung.

## Sicherheitsgrenzen

- Games-Mount im Container nur lesbar
- keine beliebigen Browserpfade ausführbar
- Pfadnormalisierung auf Server und Agent
- kurzlebige Einmal-Tickets
- separater Agent-Token mit Prüfung vor der Installation
- lokale Bestätigung vor jedem Start
- CSRF-geschützte Änderungen
- Uploadprüfung für Cover und Hintergründe
- keine automatische Archivextraktion

Für entfernten Zugriff werden Tailscale oder ein korrekt abgesicherter HTTPS-Reverse-
Proxy empfohlen. Die App sollte nicht ungefiltert ins öffentliche Internet gestellt
werden.

## Rechte und Nutzung

Der Quellcode ist aus Gründen der Transparenz öffentlich einsehbar, aber **nicht
Open Source**. Offizielle, unveränderte Releases dürfen persönlich und
nichtkommerziell genutzt werden. Weitergabe, Veröffentlichung, kommerzielle Nutzung
und die Verbreitung abgeleiteter Fassungen erfordern eine vorherige schriftliche
Genehmigung. Einzelheiten stehen in [LICENSE.md](LICENSE.md).

---

Copyright © 2026 Michael Härtwig · HypeTek
