# HypeTek Mission Control – Roadmap

Copyright © 2026 Michael Härtwig · HypeTek

## Nächste Ausbaustufen

### Internationalisierung

- Übersetzungskern mit sprachneutralen Schlüsseln statt fest eingebauter UI-Texte (Basis seit 0.3.2)
- automatische Browsererkennung plus frei wählbare Sprache
- integriert seit 0.3.2: Deutsch, Englisch und Russisch; anschließend Französisch, Spanisch, Italienisch,
  Portugiesisch (Brasilien), Polnisch, Russisch, Türkisch, vereinfachtes Chinesisch,
  Japanisch, Koreanisch und Arabisch
- vollständige Rechts-nach-links-Unterstützung für Arabisch
- weitere Sprachen als nachladbare, versionierte JSON-Pakete
- keine unnötige Aufteilung: reine Textübersetzungen sind klein; separate Downloads
  sind vor allem für zusätzliche Schriftarten, Sprachmedien oder Community-Pakete sinnvoll
- Fallback-Kette: gewählte Regionalsprache → Basissprache → Englisch

### Bibliothek und Darstellung

- echtes Mehrbibliotheken-Modell für zusätzliche Server-/Container-Pfade mit eigener
  sicherer Windows-Pfadzuordnung je Bibliothek; keine unüberprüften Browserpfade
- kontrollierte Stapelzuordnung von Covers mit Trefferprüfung
- weitere Metadatenfelder, ohne vorhandene Ordnernamen zu verändern
- Designprofile mit eigenen Farben, Hintergründen und regelbaren Effekten (Basis seit 0.3.0)
- unabhängige Karten-, Fenster- und Schriftstile (Basis seit 0.3.0)
- Profil-Export und -Import mit geprüftem, versioniertem Austauschformat
- Barrierefreiheit, Tastaturbedienung und reduzierte Animationen

### Veröffentlichung

- versionierte Container-Images und reproduzierbare Windows-Installer
- TrueNAS-Catalog-App mit gepflegten Metadaten und Upgrade-Pfad
- erweiterte Migrations-, Sicherheits- und Oberflächentests
- mehrsprachige SMB-, Tailscale- und Installationsanleitungen

### Windows-Client und Standalone-App

- nativer Mission-Control-Desktop-Client, bevorzugt als schlanke Tauri-Anwendung
- Weboberfläche parallel als Browser- und installierbare PWA-Version erhalten
- Dashboard und Agent in der Desktop-App verbinden, damit Windows-Aktionen ohne
  externe Browser-Protokollabfrage ausgelöst werden können
- Geräte-Pairing mit eigenen Geräteschlüsseln und dauerhaft vertrauenswürdigen Servern
- kurzlebige signierte Aufträge, Schutz vor Wiederholung und widerrufbare Geräte
- wählbare Sicherheitsstufen: immer fragen, nur Programmstarts bestätigen oder nie fragen
- sinnvolle Standardwerte: Ordner ohne Nachfrage, ISO optional, Installer mit Bestätigung
- eigener Tray-Betrieb, verständlicher App-Name und eigenes Symbol statt PowerShell-Anzeige
- Browser-Protokoll und PowerShell-Agent während der Migration kompatibel halten
