# Changelog

## 0.3.24

- Tastaturkürzel für die Kachelansicht von `Alt+G` auf `Alt+K` geändert; `Alt+L` bleibt für die Listenansicht erhalten.
- Bewegung und Farbverlauf des Energiepunkts laufen nun in derselben CSS-Animation. Dadurch fadet der Punkt auch im LCARS-Stil ohne abrupten Farbwechsel durch den eingestellten Verlauf.
- Installierbare PWA-Basis mit Web-App-Manifest, App-Symbolen und Service Worker ergänzt. Der Offline-Cache ist bewusst auf statische Oberflächen-Dateien begrenzt; API-, Anmelde- und Bibliotheksdaten werden nicht zwischengespeichert.

## 0.3.23

- Abbrechen und Schließen im Eintragseditor lösen keinen Speichervorgang mehr aus; eine ungültige Coverdatei wird verworfen und kann den Dialog nicht erneut blockieren.
- Escape verhält sich im Editor wie Abbrechen und räumt temporäre Cover-Vorschauen zuverlässig auf.
- Neue Animationseinstellung mit den Modi Automatisch (System), Reduziert und Voll ergänzt; reduzierte Bewegung gilt auch für den Energiepunkt und weiches Scrollen.
- Sichtbare Tastaturfokusse, Sprunglink zum Hauptinhalt und Shortcuts für Suche (`/`), Kachel-/Listenansicht (damals `Alt+G`/`Alt+L`) sowie Seitenwechsel (`Alt+←`/`Alt+→`) ergänzt.
- Die neuen Barrierefreiheits- und Animationstexte sind in allen zehn integrierten Oberflächensprachen enthalten.

## 0.3.22

- Designprofile lassen sich als versionierte `.mcdesign.json`-Pakete exportieren und wieder importieren.
- Optionale Profil-Hintergründe werden direkt in das portable Paket eingebettet und beim Import auf Format, Dateisignatur, Größe und Integrität geprüft.
- Importierte Profile überschreiben keine vorhandenen Profile, erhalten bei Namenskonflikten automatisch einen eindeutigen Namen und werden direkt aktiviert.
- Export und Import sind angemeldeten Benutzern vorbehalten; der Import ist zusätzlich CSRF-geschützt und größenbegrenzt.
- Export-, Import- und Statusmeldungen für alle zehn integrierten Oberflächensprachen ergänzt.

## 0.3.21

- Die bislang englischen technischen Hinweise und Entfernen-Aktionen im Einstellungsfenster für Italienisch, Französisch, Spanisch, Portugiesisch, Polnisch, Niederländisch und Türkisch vollständig lokalisiert.
- Translator-Verwaltung, API-Key-Speicherung und Scanner-Ausschlüsse werden nun in jeder auswählbaren Oberflächensprache erklärt.

## 0.3.20

- Vollständige Sprachauswahl für Oberfläche, Spielinhalte und Windows-Agent vereinheitlicht: Deutsch, Englisch, Russisch, Italienisch, Französisch, Spanisch, Portugiesisch, Polnisch, Niederländisch und Türkisch.
- Der EXE-Agent zeigt direkt beim Start die Inno-Setup-Sprachauswahl; Assistent, Feldbeschriftungen, SMB-Hinweise, Token-Prüfung und Hilfetexte folgen der gewählten Sprache statt nur der Windows-Systemsprache.
- Die beim Setup gewählte Sprache wird in der lokalen Agent-Konfiguration hinterlegt; die Laufzeit-Bestätigung folgt weiterhin vorrangig der in Mission Control gewählten Oberflächensprache.
- Das Spiele-Sprachmenü zeigt alle vom tatsächlich laufenden LibreTranslate-Container bereitgestellten Modelle. Die mitgelieferte TrueNAS-YAML lädt denselben Satz aus zehn Sprachen.
- Ukrainisch aus dem schlanken Standardpaket und dem verwalteten Translator-Modellsatz entfernt.
- Italienische, französische, spanische, portugiesische, polnische, niederländische und türkische Navigation, Einstellungen, Bibliotheksaktionen und Agent-Bestätigungen ergänzt.
- Den doppelten kleinen Übersetzungs-Timer unterhalb der Sprachauswahl entfernt; Spinner und verstrichene Zeit bleiben ausschließlich im aktiven Übersetzungsbutton sichtbar.
- Sprachpakete erben sämtliche technischen Hilfe-, Fehler- und Barrierefreiheits-Schlüssel, damit kein auswählbares Paket unvollständige UI-Elemente erzeugt.

## 0.3.17

- Überschriften, Platzhalter und Bibliotheksfelder im Spiele-Infofenster folgen nun der tatsächlich gespeicherten Sprache des Spielinhalts.
- Die globale Oberflächensprache bleibt davon unabhängig; Titel, Dateinamen und eigene Bemerkungen werden nicht automatisch verändert.
- „Spielinhalt übersetzen“ scrollt das Infofenster zuverlässig zur eingeblendeten Sprachauswahl – sowohl sofort beim Öffnen als auch nach dem Laden der Translator-Sprachen.

## 0.3.16

- Zielsprachen im Spiele-Infofenster in ein kompaktes Dropdown mit Favoritenstern und getrenntem Startknopf überführt.
- Während LibreTranslate arbeitet, zeigen Übersetzungsbutton und Statuszeile einen Spinner sowie die verstrichene Zeit.
- Die TheGamesDB-Coversuche lässt sich nun auch mit Enter im Suchfeld starten.

## 0.3.15

- Zielsprachen-Auswahl aus den globalen Einstellungen in das jeweilige Spiele-Infofenster verschoben.
- Scrollbare, vom Translator gelieferte Sprachliste mit dauerhaft speicherbarer Favoritensprache ergänzt.
- Mischsprachige Inhalte werden ohne fest verdrahtete Ausgangssprachen fragmentweise erkannt und mehrstufig übersetzt.
- Aktionsbereich im Spielefenster neu geordnet: Edit oben, Zurück unten rechts.

## 0.3.14

- Kurze italienische Systemanforderungs-Begriffe wie `REQUISITI DI SISTEMA`, `MINIMI`, `Scheda video` und `CONSIGLIATI` werden nun ausdrücklich als Italienisch an LibreTranslate übergeben.
- Normale Beschreibungstexte behalten weiterhin die automatische Quellsprachenerkennung, sodass gemischte TheGamesDB-Inhalte zeilenweise korrekt verarbeitet werden.
- Regressionstest für gemischte englische Beschreibungen und kurze italienische Anforderungszeilen ergänzt.

## 0.3.13

- Italienisch zum verwalteten LibreTranslate-Sprachpaket ergänzt, damit gemischtsprachige TheGamesDB-Inhalte vollständig verarbeitet werden können.
- Spielinhalte werden nun zeilenweise mit eigener Quellsprachenerkennung übersetzt; englische Beschreibungen und italienische Systemanforderungen können dadurch in einem Datensatz gemeinsam übersetzt werden.
- Zeilenumbrüche und nichtsprachliche Trennzeichen bleiben bei der Übersetzung erhalten.
- TrueNAS-YAML, Compose-Beispiel, integrierte Hilfe und Tests auf das neue Basispaket Deutsch, Englisch, Russisch und Italienisch aktualisiert.

## 0.3.12

- LibreTranslate 1.9.6 als versionierten internen zweiten Container in Compose und TrueNAS-YAML integriert.
- Mission Control erkennt den Translator automatisch unter `http://translator:5000`; ein externer Dienst oder API-Key ist nicht nötig.
- Der Translator veröffentlicht keinen Host-Port und ist nur im internen App-Netz erreichbar.
- Persistente Modellablage und ein schlankes Basispaket für Deutsch, Englisch und Russisch ergänzt.
- Verbindungstest und Statusendpunkt zeigen die vom Translator tatsächlich gemeldeten Sprachcodes.
- Bestehende leere Translator-Einstellungen werden beim Upgrade automatisch auf den verwalteten Dienst migriert.
- Integrierte Hilfe und Installationsdokumentation auf den neuen Ein-Schritt-Betrieb aktualisiert.

## 0.3.11

- Nach erfolgreicher Agent-Prüfung klappt die Einrichtung weiterhin automatisch ein.
- Beim späteren erneuten Öffnen erscheint ein kleiner lokalisierter Zurück-Button, mit dem sich der bereits erledigte Agent-Bereich wieder schließen lässt.
- Die übrige Agent-Einrichtung und alle Fixes aus 0.3.10 bleiben unverändert.

## 0.3.10

- LCARS reserviert sein linkes Systemband nun auch für den Agent-Einrichtungsbereich und das Einstellungsfenster; Inhalte liegen nicht mehr unter Uhr oder Band.
- Einstellungen verwenden auf ausreichend großen Desktopfenstern ein kompaktes Drei-Spalten-Layout ohne internen Scrollbereich.
- Translator-Verbindung kann mit der aktuell eingegebenen Adresse vor dem Speichern geprüft werden.
- Der Verbindungstest bleibt deaktiviert, solange weder eine Adresse eingegeben noch eine gespeicherte Verbindung vorhanden ist.
- Bestehende Funktionen aus 0.3.9 bleiben unverändert erhalten; 0.3.10 konzentriert sich auf Stabilität und Bedienbarkeit.

## 0.3.9

- Deutsche, englische und russische Oberflächentexte für Editor, Spiele-Infofenster, Metadatensuche, Profilverwaltung, Hilfen und dynamische Statusmeldungen vervollständigt.
- Automatische Browser-Spracherkennung mit sauberer Fallback-Kette Regionalsprache → Basissprache → Englisch ergänzt.
- Die automatische Sprache wird auch an den Windows-Agent weitergegeben; dieser verwendet dafür die Windows-Oberflächensprache.
- Live-Prüfung für den optionalen Mission Control Translator in den Einstellungen ergänzt, ohne API-Schlüssel an den Browser auszugeben.
- Translator-Statusendpunkt ist anmeldungsgeschützt und prüft die gespeicherte Verbindung serverseitig.
- Sprachwechsel aktualisiert Uhr, dynamische Karten, Dialoginhalte und Hilfetexte ohne Browser-Neustart.

## 0.3.8

- LCARS verwendet nur noch einen durchgehenden Querbalken über die vollständige Seitenbreite; der zusätzliche Hero-Rand wurde entfernt.
- Das vertikale LCARS-Systemband beginnt mit einem minimalen Abstand direkt unterhalb des Querbalkens.
- Die Position wird weiterhin aus der tatsächlichen Kopfzeilenhöhe berechnet und bleibt damit unabhängig von Deutsch, Englisch oder Russisch.

## 0.3.7

- LCARS-Band richtet sich dynamisch an der tatsächlichen, sprachabhängigen Höhe der Kopfzeile aus und hält acht Pixel Abstand zum Querbalken.
- Doppelter LCARS-Querbalken entfernt; die animierte Energielinie ist nun die einzige obere Trennlinie.
- Sticky-Systemuhr hält automatisch Abstand zum feststehenden HypeTek-Logo.
- Windows-Agent erhält die eingestellte Oberflächensprache im sicheren Startticket und übersetzt Bestätigungstitel, Felder, Aktion und Rückfrage auf Deutsch, Englisch oder Russisch.

## 0.3.6

- LCARS-Systemband auf Dokumenthöhe umgestellt: Rundung und Querbalken scrollen wie vorgesehen aus dem Sichtbereich, statt Spielekarten zu überlagern.
- LCARS-Uhr als eigener Sticky-Bereich erhalten, während das Band beim Scrollen durchgehend sichtbar bleibt.
- Vertikales Band beginnt am Seitenanfang unterhalb des Querbalkens.

## 0.3.5

- Englisches und russisches Sprachpaket auf dynamische Bibliothekskarten, Zähler, Typen, Agent-Einrichtung und die wichtigsten Einstellungen erweitert.
- Sprachwechsel rendert Karten, Aktionsbuttons und Statistik sofort neu; ein Browser-Refresh ist nicht mehr erforderlich.
- LCARS-Systemband horizontal gespiegelt und mit feststehender oberer Rundung an den ebenfalls feststehenden Querbalken angeschlossen.
- Stylesheet erhält wie JavaScript einen Versionsparameter gegen gemischte Browser-Caches.

## 0.3.4

- Globalen JavaScript-Namenskonflikt zwischen UI-Sprachpaket und Hauptanwendung behoben, der `app.js` in Chrome vollständig am Start hinderte.
- Sprachpaket in einen eigenen Gültigkeitsbereich gekapselt; Sprachfunktionen werden nur noch über die ausdrücklich vorgesehene Schnittstelle veröffentlicht.
- Windows-Agent-Verbindungstest frühzeitig und CSP-kompatibel als nativen Ereignishandler registriert; Inline-JavaScript wurde wieder entfernt.
- Source-Available-Rechtehinweis ergänzt: öffentlich einsehbar und als offizielles Release persönlich nutzbar, jedoch ausdrücklich nicht Open Source.
- Alle Funktionen und Designänderungen aus 0.3.3 vollständig beibehalten.

## 0.3.3

- Kritischen Windows-Agent-Verbindungstest gegen gemischte Browser-Caches abgesichert: JavaScript und CSS werden jetzt mit der laufenden Serverversion geladen.
- „Verbindung prüfen“ erhält einen direkten Ausweich-Handler und bleibt auch dann nutzbar, wenn eine optionale Oberflächenfunktion nicht initialisiert werden kann.
- Integrierte UI-Sprachpakete auf ältere Browser abgesichert; nicht unterstützte Übersetzungsselektoren können die Hauptanwendung nicht mehr blockieren.
- LCARS-Systemband deutlich verbreitert, mit gerundeter oberer Kante und feststehender Systemuhr samt Datum ergänzt.
- Mission Control weist vor dem Agent-Download deutlich auf das zuerst zu verbindende SMB-Netzlaufwerk hin.
- Windows-Installer nennt dieselbe SMB-Voraussetzung direkt auf der Seite zur Auswahl der Spielebibliothek.

## 0.3.2

- Windows-Agent-Installer um einen nativen Durchsuchen-Dialog für verbundene SMB-Laufwerke und lokale Ordner ergänzt.
- Integrierte UI-Sprachpaket-Grundlage mit Deutsch, Englisch und Russisch eingeführt; die Oberflächensprache bleibt von der Sprache der Spielinhalte getrennt.
- Neue Designprofile werden nach dem Speichern automatisch aktiviert und unmittelbar angewendet.
- „Abbrechen“ im Profileditor in „Zurück“ umbenannt und eine eigene Zurück-Schaltfläche neben „+ Neues Profil“ ergänzt.
- Tactical-Frame-Vorschau durch echte HUD-Eckmarkierungen ersetzt und an die spätere Kartendarstellung angeglichen.
- Energiestreifen erhält einen expliziten, mathematisch mittigen Farbstopp zwischen Start- und Endfarbe.
- Mehrbibliotheken-Unterstützung für zusätzliche lokale und serverseitige Pfade als sicherheitsrelevante nächste Ausbaustufe spezifiziert.

## 0.3.1

- Spiele können direkt im Infofenster als Favorit markiert und über den neuen Favoritenfilter angezeigt werden.
- Favoriten werden in SQLite gespeichert und bleiben bei erneuten Bibliotheksscans erhalten.
- Farben des Energiestreifens lassen sich unabhängig als Verlauf „von“ und „bis“ je Designprofil festlegen.
- Der Energiepunkt bleibt vollständig innerhalb der Bildschirmbreite und erzeugt keinen horizontalen Überlauf mehr.
- Schriftgruppen „System“ und „Technical“ visuell klar voneinander getrennt.
- Erfolgreiches Speichern eines Designprofils wird direkt am Speichern-Button bestätigt.
- Abbrechen und der Wechsel zwischen Profilliste und Editor funktionieren durch eine robuste Behandlung versteckter Bereiche wieder zuverlässig.
- Das bisherige LCARS-Profil zu einer eigenständigen „LCARS Console“ mit schwarzen Funktionsflächen, Farbbändern und Kapselenden ausgebaut.
- Bestehende eigene Profile erhalten beim Upgrade automatisch einen Energiestreifen aus ihren bisherigen Primär- und Sekundärfarben.

## 0.3.0

- Designprofile als eigene persistente Ebene für Farben, Hintergrundbild und Hintergrundeffekte ergänzt.
- Design und Oberflächenstil getrennt: sechs frei kombinierbare Stile und fünf Schriftgruppen stehen unabhängig von der Farbwelt zur Wahl.
- Vier geschützte Ausgangsprofile Mission, Cyberpunk, LCARS und Midnight integriert.
- Eigene Profile können dupliziert, live bearbeitet, gespeichert, aktiviert und gelöscht werden.
- Profilwerte werden serverseitig strikt geprüft und atomar mit restriktiven Dateirechten gespeichert.
- Bestehende Design- und Hintergrundeinstellungen werden beim ersten Wechsel in das Profilsystem übernommen.
- Live-Vorschau zeigt Farben, Kartenform, Schrift, Hintergrundbild, Abdunklung und Unschärfe vor dem Speichern.
- Energiepunkt übernimmt während des Durchlaufs stufenlos die jeweilige Farbe des Linienverlaufs und glüht passend dazu.

## 0.2.9

- Energiepunkt als flachere, glühende orange Linse dargestellt.
- Durchlauf gegenüber 0.2.8 leicht beschleunigt.
- Nach jedem vollständigen Durchlauf exakt 1,75 Sekunden Pause ergänzt.
- Erfolgreiche manuelle Abnahme von Versionsanzeige, Ansichtswechsel, Seitennavigation, Logo-Rücksprung und Einstellungen aus 0.2.8 dokumentiert.

## 0.2.8

- Laufende Serverversion links unten in den Einstellungen ergänzt.
- HypeTek-Urhebervermerk mit Michael Härtwig dauerhaft in der Anwendung verankert.
- Bibliothek zwischen Kachel- und Listenansicht umschaltbar; Auswahl bleibt im Browser erhalten.
- Seitennavigation mit wählbaren 12, 24, 48 oder 96 Einträgen pro Seite ergänzt.
- Suche und Typfilter springen kontrolliert auf die erste Ergebnisseite zurück.
- Weißen Laufbalken durch einen orange glimmenden Energiepunkt ersetzt.
- Festes HypeTek-Logo führt beim Anklicken weich zum Seitenanfang zurück.
- PowerShell-Fallback-ZIP um eine sichtbare TXT-Kurzanleitung mit Sicherheits- und Urheberhinweisen ergänzt.
- Reduzierte Animationen werden über die Betriebssystem-/Browsereinstellung berücksichtigt.

## 0.2.7

- Windows-Agent-Ersteinrichtung als klare Reihenfolge aus Download, Installation und Verbindungstest dargestellt.
- PowerShell-Fallback in einen eingeklappten Expertenbereich verschoben.
- HypeTek-Logo aus dem gefilterten Header gelöst, damit es unabhängig vom Seiteninhalt fest positioniert bleibt.
- Missverständliche Prozentanzeige für den Cover-Ausschnitt entfernt.
- Cover-Ausrichtung erfolgt direkt durch vertikales Ziehen in einer maßstabsgetreuen Kartenvorschau.
- Tastatursteuerung für die Cover-Ausrichtung mit Pfeiltasten, Pos1 und Ende ergänzt.
- Roadmap um nativen Standalone-/Tray-Client, PWA, Geräte-Pairing und wählbare Sicherheitsstufen erweitert.
- Release-Erzeugung fängt ein noch nicht vorhandenes GitHub-Release unter Windows PowerShell kontrolliert ab.

## 0.2.6

- Installer-Download zeigt auf das exakte versionierte Release statt auf einen möglicherweise fehlenden Latest-Asset.
- GitHub Actions erzeugt beim Push automatisch das Release aus `VERSION` und lädt den Windows-Agenten dort hoch.
- Container werden zusätzlich mit der in `VERSION` angegebenen Versionsnummer veröffentlicht.
- Cover-Ausschnitt kann pro Spiel vertikal zwischen oberem und unterem Bildrand positioniert werden.
- Cover-Dateinamen erhalten bei jeder Übernahme eine neue Revision, damit Änderungen ohne Browser-Refresh sichtbar werden.
- Nur das HypeTek-Logo bleibt beim Scrollen sichtbar; die restliche Navigationsleiste scrollt weiterhin normal.
- Hinweis zur Agent-Prüfung nennt die erforderliche aktuelle Agent-Version eindeutiger.

## 0.2.5

- Installieren, ISO einbinden, Ordner öffnen, Übersetzen und Bearbeiten sind direkt im Spiele-Infofenster erreichbar.
- Optionale LibreTranslate-kompatible Translator-Verbindung mit lokaler Speicherung von Original und Übersetzung ergänzt.
- Zielsprachen für Spielinhalte einschließlich Deutsch, Englisch, Russisch, Arabisch, Chinesisch und weiterer wichtiger Sprachen ergänzt.
- Gemischtsprachige TheGamesDB-Texte werden abschnittsweise zur Übersetzung übergeben.
- Allgemeine Fallback-Suche für kurze Titelakronyme ersetzt die bisherige spezielle AC-Titelliste.
- Windows-Agent kann über ein kurzlebiges Prüfticket sicher erkannt werden; der Installationshinweis verschwindet anschließend in diesem Browser.
- Agent-Bezeichnungen verständlicher in Windows-Agent, Windows-Agent installieren und Manuelle Installation umbenannt.
- Integrierte API-/Translator-Hilfe mit downloadbarer, visuell geprüfter PDF-Anleitung und serverbezogenem QR-Code ergänzt.

## 0.2.4

- Klick auf ein Cover öffnet ein eigenes Spiele-Infofenster mit lokalem Cover als Hintergrund.
- TheGamesDB-Spielinhalt, offizieller Titel, Plattform, Erscheinungsdatum, Rating und Spielerangaben werden bei der Auswahl lokal gespeichert.
- Das bisherige Freitextfeld „Beschreibung“ heißt in der Oberfläche nun „Bemerkungen“ und wird getrennt vom offiziellen Spielinhalt angezeigt.
- Suchfeld zeigt den bereinigten Titel ohne Release-/Repack-Zusätze.
- Bekannte `AC`-Kurztitel werden für die Suche zu `Assassin's Creed` erweitert.
- PC-/Windows-Treffer werden vor Konsolenfassungen sortiert.
- Treffer-Vorschaubilder werden über Mission Control geladen, geprüft und privat zwischengespeichert.
- TrueNAS-Anleitung von `INSTALL-TRUETITAN.md` in `INSTALL-TRUENAS.md` umbenannt.

## 0.2.3

- TheGamesDB als aktiven Hauptanbieter für die manuelle Cover-Suche ergänzt.
- API-Key wird vor dem Speichern gegen den offiziellen Suchendpunkt geprüft.
- Suchtreffer zeigen Titel, Plattform, Erscheinungsdatum und Covervorschau.
- Boxart wird ausschließlich vom offiziellen TheGamesDB-CDN geladen, geprüft und lokal zwischengespeichert.
- Quellenlink verweist je Cover auf den zugehörigen TheGamesDB-Eintrag.
- Bereits gespeicherte RAWG-Cover und deren Quellenlinks bleiben sichtbar; neue RAWG-Abfragen sind wegen der unklaren Verfügbarkeit deaktiviert.
- Metadatenanbieter-Schicht und Tests für weitere spätere Quellen vorbereitet.

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
