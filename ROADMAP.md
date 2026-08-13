# HypeTek Mission Control – Roadmap

## Nächste Ausbaustufen

### Internationalisierung

- Übersetzungskern mit sprachneutralen Schlüsseln statt fest eingebauter UI-Texte
- automatische Browsererkennung plus frei wählbare Sprache
- zunächst integriert: Deutsch, Englisch, Französisch, Spanisch, Italienisch,
  Portugiesisch (Brasilien), Polnisch, Russisch, Türkisch, vereinfachtes Chinesisch,
  Japanisch, Koreanisch und Arabisch
- vollständige Rechts-nach-links-Unterstützung für Arabisch
- weitere Sprachen als nachladbare, versionierte JSON-Pakete
- keine unnötige Aufteilung: reine Textübersetzungen sind klein; separate Downloads
  sind vor allem für zusätzliche Schriftarten, Sprachmedien oder Community-Pakete sinnvoll
- Fallback-Kette: gewählte Regionalsprache → Basissprache → Englisch

### Bibliothek und Darstellung

- kontrollierte Stapelzuordnung von Covers mit Trefferprüfung
- weitere Metadatenfelder, ohne vorhandene Ordnernamen zu verändern
- eigene Akzentfarben, Karten- und Fensterformen
- zusätzliche Stile und regelbare Hintergrundeffekte
- Barrierefreiheit, Tastaturbedienung und reduzierte Animationen

### Veröffentlichung

- versionierte Container-Images und reproduzierbare Windows-Installer
- TrueNAS-Catalog-App mit gepflegten Metadaten und Upgrade-Pfad
- erweiterte Migrations-, Sicherheits- und Oberflächentests
- mehrsprachige SMB-, Tailscale- und Installationsanleitungen
