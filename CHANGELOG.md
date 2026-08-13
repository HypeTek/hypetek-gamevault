# Changelog

## 0.2.2

- Freiwillige RAWG-Coversuche im Bearbeiten-Dialog ergänzt.
- Treffer werden vor der Übernahme mit Titel, Veröffentlichungsdatum und Vorschau angezeigt.
- Externe Cover werden kontrolliert heruntergeladen, auf Typ und Größe geprüft und lokal unter `/config/covers` zwischengespeichert.
- RAWG-API-Key wird nur serverseitig gespeichert und nie an den Browser zurückgegeben.
- RAWG-Suche überträgt Titel ausschließlich nach einem ausdrücklichen Klick; automatische Massenabfragen bleiben deaktiviert.
- RAWG-Quellenlink wird an jeder Karte mit einem übernommenen Cover angezeigt.
- Manueller Cover-Upload bleibt erhalten und entfernt die externe Quellenzuordnung.

## 0.2.1

- Kartenraster auf lesbare Mindestbreiten begrenzt und für Mobilgeräte angepasst.
- Aktionsbuttons in eine eindeutige Hauptaktion und eine saubere zweite Zeile aufgeteilt.
- Flachere Thumbnail-Flächen mit Monogramm-Platzhalter für Einträge ohne Cover ergänzt.
- Navigation überdeckt beim Scrollen nicht länger die Hauptüberschrift.
- Projektweite Zeilenenden über `.gitattributes` festgelegt.
- Installer und Projektversion auf 0.2.1 vereinheitlicht.
- Integrierte Windows-Anleitung für SMB-Netzlaufwerke, Windows-Anmeldeinformationen und SMB über Tailscale ergänzt.
- Health-Endpunkt zeigt nun laufende Version und Agent-API-Version zur eindeutigen Update-Diagnose.

## 0.2.0

- Der Windows-Installer prüft den Agent-Token über einen eindeutigen Server-Endpunkt und speichert bei fehlgeschlagener Prüfung keine Konfiguration.
- Agent-Token-Prüfung auf nicht cachebaren POST umgestellt; Installer-Build 0.2.0.1 ist im Fenstertitel eindeutig erkennbar.

- Rebranding zu HypeTek Mission Control
- vier integrierte Designs und eigener Hintergrund
- konfigurierbarer Server- und Archivname
- optionales Fadenkreuz
- Scanner-Ausschlüsse und Überspringen unlesbarer Ordner
- Kartenaktionen responsiv; `Bearbeiten` durch `Edit` ersetzt
- Windows-Agent ohne sichtbares Konsolenfenster
- PowerShell 5.1 und PowerShell 7 unterstützt
- UTF-8-BOM-Fehler des Agent-Downloads behoben
- PowerShell-5-Pfadfehler bei Setup und ISO behoben
- verständliche Ticket- und Agent-Token-Fehlermeldungen
- geführter Windows-EXE-Installer
- einheitliche Bezeichnung Agent-Token, integrierte Hilfe und Serverprüfung vor Speicherung
- aktuelle Node-24-kompatible GitHub Actions
- zusätzliche Einstellungs- und Ausschlusstests

## 0.1.1

- HypeTek-Logo und Agent-Download ergänzt

## 0.1.0

- erstes MVP mit Scanner, Bibliothek, Setup/ISO und sicherem Windows-Agent
