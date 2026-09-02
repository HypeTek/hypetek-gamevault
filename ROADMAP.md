# HypeTek Mission Control – Roadmap

Copyright © 2026 Michael Härtwig · HypeTek

## Nächste Ausbaustufen

### Internationalisierung

- Übersetzungskern mit sprachneutralen Schlüsseln statt fest eingebauter UI-Texte (Basis seit 0.3.2)
- automatische Browsererkennung plus frei wählbare Sprache (vollständig seit 0.3.9)
- vollständig integriert: Deutsch, Englisch, Russisch, Französisch, Spanisch, Italienisch,
  Portugiesisch, Polnisch, Niederländisch, Türkisch und Arabisch (Arabisch seit 0.8.0)
- vollständige Rechts-nach-links-Unterstützung für Arabisch einschließlich technischer
  LTR-Inseln für Pfade, URLs, IDs und API-Keys (vollständig seit 0.8.0)
- vereinfachtes Chinesisch vollständig seit 0.8.0; Klingonisch und Sindarin seit
  0.8.0 als gekennzeichnete experimentelle Spaß-Sprachpakete
- Spieleinhaltsübersetzung seit 0.9.0-rc.3 für alle verwalteten Translator-Sprachen
  einschließlich Arabisch und Chinesisch; `Klingon (Beta)` und
  `Elvish / Sindarin (Beta)` verwenden einen lokalen experimentellen Wortschatz über
  eine englische Zwischenübersetzung und beanspruchen keine kanonische Vollübersetzung
- künftig: Japanisch und Koreanisch
- weitere Sprachen als nachladbare, versionierte JSON-Pakete
- keine unnötige Aufteilung: reine Textübersetzungen sind klein; separate Downloads
  sind vor allem für zusätzliche Schriftarten, Sprachmedien oder Community-Pakete sinnvoll
- Fallback-Kette gewählte Regionalsprache → Basissprache → Englisch (seit 0.3.9)

### Bibliothek und Darstellung

- kombinierte Metadatensuche in TheGamesDB und RAWG mit stabiler Provider-Reihenfolge und unabhängigem Fehler-Fallback (vollständig seit 0.6.0)
- sichere Windows- und Linux-Pfadzuordnungen je Bibliothek in Einstellungen und Starttickets (Grundlage seit 0.6.0); nativer Linux-Agent folgt
- getrennte Bibliothekstypen für serverseitige Netzwerkbestände und rein lokale Windows-Laufwerke samt authentifiziertem Agent-Scan (vollständig seit 0.6.1)

- echtes Mehrbibliotheken-Modell für zusätzliche Server-/Container-Pfade mit eigener
  sicherer Windows-Pfadzuordnung je Bibliothek; keine unüberprüften Browserpfade
  (vollständig seit 0.5.0)
- kontrollierte Stapelzuordnung von Covers mit Trefferprüfung
- weitere Metadatenfelder, ohne vorhandene Ordnernamen zu verändern
- intelligente lokale Titelwahl aus Ordner- und Installationsmediennamen, ohne manuelle
  Titel oder Katalogmetadaten zu überschreiben (vollständig seit 0.5.3 einschließlich Altbeständen)
- kompakte Seitennummerierung mit direktem Sprung zum Anfang und Ende großer Bibliotheken
  (vollständig seit 0.5.3)
- Designprofile mit eigenen Farben, Hintergründen und regelbaren Effekten (Basis seit 0.3.0)
- unabhängige Karten-, Fenster- und Schriftstile (Basis seit 0.3.0)
- Profil-Export und -Import mit geprüftem, versioniertem Austauschformat (vollständig seit 0.3.22)
- Barrierefreiheit, Tastaturbedienung und reduzierte Animationen (Basis seit 0.3.23)

### Veröffentlichung

- versionierte Container-Images und reproduzierbare Windows-Installer
- TrueNAS-Catalog-App mit gepflegten Metadaten und Upgrade-Pfad
  (Community-Catalog-Staging seit 0.9.0-rc.1; Upstream-CI, CDN-Assets und PR noch offen)
- erweiterte Migrations-, Sicherheits- und Oberflächentests
- mehrsprachige SMB-, Tailscale- und Installationsanleitungen
- Community-Catalog-Paket für `truenas/apps` mit `app.yaml`, `questions.yaml`,
  Compose-Template und Testwerten (Staging seit 0.9.0-rc.1; finale CDN-Assets und Upstream-Abnahme offen)
- reproduzierbarer Release-Kandidat mit unveränderlichen Image-Digests
  (Digest-Manifest seit 0.9.0-rc.1; Sicherheitsprüfung sowie Neuinstallations-, Upgrade- und Rollback-Test auf TrueNAS noch offen)

### Windows-Client und Standalone-App

- nativer Mission-Control-Desktop-Client, bevorzugt als schlanke Tauri-Anwendung
- Weboberfläche parallel als Browser- und installierbare PWA-Version erhalten
  (installierbare PWA-Basis mit bewusst statischem Offline-Cache seit 0.4.0)
- Dashboard und Agent in der Desktop-App verbinden, damit Windows-Aktionen ohne
  externe Browser-Protokollabfrage ausgelöst werden können
- Geräte-Pairing mit eigenen Geräteschlüsseln und dauerhaft vertrauenswürdigen Servern
- kurzlebige signierte Aufträge, Schutz vor Wiederholung und widerrufbare Geräte
- wählbare Sicherheitsstufen: immer fragen, nur Programmstarts bestätigen oder nie fragen
- sinnvolle Standardwerte: Ordner ohne Nachfrage, ISO optional, Installer mit Bestätigung
- eigener Tray-Betrieb, verständlicher App-Name und eigenes Symbol statt PowerShell-Anzeige
- Browser-Protokoll und PowerShell-Agent während der Migration kompatibel halten
