# Changelog

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
