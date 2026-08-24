#!/usr/bin/env python3
"""Build the branded API and integrated translator guide."""

from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "server/static/docs/HypeTek-Mission-Control-API-und-Translator-Anleitung.pdf"
LOGO = ROOT / "server/static/hypetek-gaming.jpg"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

NAVY = colors.HexColor("#071820")
PANEL = colors.HexColor("#0D2731")
CYAN = colors.HexColor("#00D1C7")
ORANGE = colors.HexColor("#F28C28")
INK = colors.HexColor("#E8F3F4")
MUTED = colors.HexColor("#91AAB1")
LINE = colors.HexColor("#224B57")


pdfmetrics.registerFont(TTFont("HypeSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("HypeSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("HypeMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))


def qr_drawing(value: str, size: float = 30 * mm) -> Drawing:
    widget = QrCodeWidget(value)
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size / width, 0, 0, size / height, 0, 0])
    drawing.add(Rect(0, 0, width, height, fillColor=colors.white, strokeColor=colors.white))
    drawing.add(widget)
    return drawing


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyMC",
            parent=styles["BodyText"],
            fontName="HypeSans",
            fontSize=9.2,
            leading=13.2,
            textColor=INK,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMC",
            parent=styles["BodyMC"],
            fontSize=7.7,
            leading=10.8,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitleMC",
            parent=styles["Title"],
            fontName="HypeSans-Bold",
            fontSize=25,
            leading=29,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleMC",
            parent=styles["BodyMC"],
            fontSize=11,
            leading=15,
            textColor=MUTED,
            spaceAfter=7 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1MC",
            parent=styles["Heading1"],
            fontName="HypeSans-Bold",
            fontSize=16,
            leading=20,
            textColor=CYAN,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2MC",
            parent=styles["Heading2"],
            fontName="HypeSans-Bold",
            fontSize=11,
            leading=14,
            textColor=ORANGE,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeMC",
            parent=styles["Code"],
            fontName="HypeMono",
            fontSize=6.6,
            leading=8.8,
            textColor=INK,
            backColor=colors.HexColor("#061117"),
            borderColor=LINE,
            borderWidth=0.5,
            borderPadding=7,
            spaceBefore=2 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CalloutMC",
            parent=styles["BodyMC"],
            backColor=PANEL,
            borderColor=CYAN,
            borderWidth=0.8,
            borderPadding=8,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableMC",
            parent=styles["SmallMC"],
            textColor=INK,
            spaceAfter=0,
        )
    )
    return styles


def bullet(text: str, styles):
    return Paragraph(f"• {text}", styles["BodyMC"])


def page_chrome(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.setFillColor(CYAN)
    canvas.rect(0, height - 3 * mm, width * 0.68, 3 * mm, stroke=0, fill=1)
    canvas.setFillColor(ORANGE)
    canvas.rect(width * 0.68, height - 3 * mm, width * 0.32, 3 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFont("HypeSans", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, f"HypeTek Mission Control {VERSION}")
    canvas.drawCentredString(width / 2, 9 * mm, "© 2026 Michael Härtwig · HypeTek")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Seite {doc.page}")
    canvas.restoreState()


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        title="HypeTek Mission Control API- und Translator-Anleitung",
        author="Michael Härtwig · HypeTek",
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates(PageTemplate(id="mc", frames=[frame], onPage=page_chrome))

    story = []
    if LOGO.exists():
        logo = Image(str(LOGO), width=24 * mm, height=24 * mm)
        logo.hAlign = "LEFT"
        story.extend([logo, Spacer(1, 3 * mm)])
    story.extend(
        [
            Paragraph("API- und Translator-Anleitung", styles["TitleMC"]),
            Paragraph(
                "TheGamesDB, integrierter lokaler Translator und sichere TrueNAS-Konfiguration",
                styles["SubtitleMC"],
            ),
            Paragraph("Was ist ab Version 0.3.23 neu?", styles["H1MC"]),
            Paragraph(
                "Mission Control kann den lokalen Translator jetzt als zweiten Dienst derselben "
                "TrueNAS-App betreiben. Die interne Adresse wird automatisch gesetzt. Es ist weder "
                "ein externer Übersetzungsdienst noch ein Translator-API-Key nötig. Gemischte "
                "TheGamesDB-Texte werden abschnittsweise erkannt. Dabei ist keine Ausgangssprache "
                "fest vorgegeben: Alle im Translator installierten Sprachen können auch innerhalb "
                "desselben Spielinhalts dynamisch erkannt und verarbeitet werden.",
                styles["CalloutMC"],
            ),
        ]
    )
    overview = [
        [Paragraph("Baustein", styles["TableMC"]), Paragraph("Aufgabe", styles["TableMC"]), Paragraph("Status", styles["TableMC"])],
        [Paragraph("TheGamesDB", styles["TableMC"]), Paragraph("Cover, offizieller Titel und Spielinformationen", styles["TableMC"]), Paragraph("Optional, eigener Key", styles["TableMC"])],
        [Paragraph("LibreTranslate", styles["TableMC"]), Paragraph("Lokale Übersetzung im internen App-Netz", styles["TableMC"]), Paragraph("Integriert", styles["TableMC"])],
        [Paragraph("Windows-Agent", styles["TableMC"]), Paragraph("Installieren, ISO einbinden und Ordner öffnen", styles["TableMC"]), Paragraph("Für Aktionen nötig", styles["TableMC"])],
    ]
    table = Table(overview, colWidths=[37 * mm, 91 * mm, 40 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PANEL),
                ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
                ("FONTNAME", (0, 0), (-1, 0), "HypeSans-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#091D25")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([table, Spacer(1, 5 * mm), Paragraph("Sicherheit", styles["H2MC"])])
    story.extend(
        [
            bullet("API-Keys und Tokens niemals in GitHub, Screenshots oder öffentliche Chats kopieren.", styles),
            bullet("Port 5000 des Translators wird nicht am TrueNAS-Host veröffentlicht.", styles),
            bullet("Sprachmodelle liegen persistent im dafür vorgesehenen Dataset.", styles),
            Paragraph(
                "Der Translator ist ein separater LibreTranslate-Container (AGPL-3.0). Mission Control "
                "referenziert das Image, verteilt es aber nicht im Projektpaket.",
                styles["SmallMC"],
            ),
            PageBreak(),
            Paragraph("1. TheGamesDB einrichten", styles["H1MC"]),
            Paragraph(
                "TheGamesDB liefert Metadaten und Cover. Jeder Betreiber verwendet seinen eigenen "
                "API-Key; ein privater HypeTek-Key wird nicht in Images oder Releases eingebaut.",
                styles["BodyMC"],
            ),
            Paragraph("API-Key anfordern", styles["H2MC"]),
            bullet("https://api.thegamesdb.net/key.php öffnen und anmelden.", styles),
            bullet("Application Name: HypeTek Mission Control", styles),
            bullet("Use: private, self-hosted game library with manual metadata and cover search.", styles),
            bullet("Application URL: eigene Projekt- oder Repository-Adresse, falls vorhanden.", styles),
            Paragraph("Key prüfen und speichern", styles["H2MC"]),
            bullet("Mission Control öffnen, Einstellungen wählen und den TheGamesDB-Key einfügen.", styles),
            bullet("Speichern wählen. Ein abgelehnter Key ersetzt keinen bereits gespeicherten Wert.", styles),
            bullet("Bei einem Spiel Edit öffnen, einen passenden PC-Treffer wählen und übernehmen.", styles),
            Paragraph(
                "Tipp: Bei abgekürzten Ordnernamen mit dem vollständigen Spieletitel suchen, zum "
                "Beispiel Assassin's Creed Valhalla statt AC Valhalla. Mission Control bereinigt "
                "bekannte Zusätze, die endgültige Trefferwahl bleibt bewusst beim Benutzer.",
                styles["CalloutMC"],
            ),
            Paragraph("Datenhaltung", styles["H2MC"]),
            Paragraph(
                "Cover, Quellhinweis und Texte werden lokal in der Mission-Control-Konfiguration "
                "gespeichert. Eigene Bemerkungen bleiben davon getrennt. Beim erneuten Übernehmen "
                "eines Treffers wird die zuvor gespeicherte Übersetzung verworfen, damit Original "
                "und Übersetzung nicht auseinanderlaufen.",
                styles["BodyMC"],
            ),
            Spacer(1, 9 * mm),
            KeepTogether(
                [
                    Paragraph("Direktlinks", styles["H2MC"]),
                    Table(
                        [[qr_drawing("https://api.thegamesdb.net/key.php", 28 * mm), Paragraph("TheGamesDB API-Key<br/><font color='#91AAB1'>api.thegamesdb.net/key.php</font>", styles["BodyMC"])],
                         [qr_drawing("https://github.com/HypeTek/hypetek-gamevault", 28 * mm), Paragraph("HypeTek Mission Control<br/><font color='#91AAB1'>github.com/HypeTek/hypetek-gamevault</font>", styles["BodyMC"])]],
                        colWidths=[36 * mm, 120 * mm],
                        style=TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]),
                    ),
                ]
            ),
            PageBreak(),
            Paragraph("2. Integrierten Translator starten", styles["H1MC"]),
            Paragraph(
                "Die vollständige TrueNAS-YAML enthält Mission Control und LibreTranslate 1.9.6. "
                "Beide Dienste teilen ein internes App-Netz. Mission Control verwendet automatisch "
                "http://translator:5000.",
                styles["BodyMC"],
            ),
            Paragraph("Datasets vorbereiten", styles["H2MC"]),
            bullet("/mnt/Application/gamevault für Datenbank, Cover und Einstellungen.", styles),
            bullet("/mnt/Application/mission-control-translator für Sprachmodelle.", styles),
            bullet("Translator-Dataset für die Container-Identität 1032:65534 beschreibbar machen.", styles),
            Paragraph("Relevanter YAML-Ausschnitt", styles["H2MC"]),
            Paragraph(
                "gamevault:<br/>"
                "  image: ghcr.io/hypetek/hypetek-gamevault:latest<br/>"
                "  pull_policy: always<br/>"
                "  labels:<br/>"
                "    com.hypetek.mission-control.deployment: \"0.3.23\"<br/>"
                "  environment:<br/>"
                "    MISSION_CONTROL_TRANSLATOR_URL: http://translator:5000<br/>"
                "translator:<br/>"
                "  image: libretranslate/libretranslate:v1.9.6<br/>"
                "  pull_policy: always<br/>"
                "  environment:<br/>"
                "    LT_DISABLE_WEB_UI: \"true\"<br/>"
                "    LT_UPDATE_MODELS: \"true\"<br/>"
                "    LT_LOAD_ONLY: en,de,ru,it,fr,es,pt,pl,nl,tr<br/>"
                "  volumes:<br/>"
                "    - /mnt/Application/mission-control-translator:/home/libretranslate/.local<br/>"
                "  healthcheck:<br/>"
                "    test: [\"CMD-SHELL\", \"./venv/bin/python scripts/healthcheck.py\"]<br/>"
                "    interval: 30s<br/>"
                "    timeout: 10s<br/>"
                "    retries: 10<br/>"
                "    start_period: 10m",
                styles["CodeMC"],
            ),
            Paragraph(
                "Die vollständige, direkt einsetzbare YAML steht in INSTALL-TRUENAS.md. Der Translator "
                "hat absichtlich keinen ports-Eintrag. GAMEVAULT_ADMIN_PASSWORD, AGENT_TOKEN und "
                "SECRET_KEY müssen durch eigene Werte ersetzt werden.",
                styles["CalloutMC"],
            ),
            Paragraph("Erster Start", styles["H2MC"]),
            bullet("Custom App speichern und warten, bis beide Container laufen.", styles),
            bullet("Beim ersten Start werden Sprachmodelle geladen; das kann mehrere Minuten dauern.", styles),
            bullet("Browser danach mit Strg+F5 aktualisieren.", styles),
            PageBreak(),
            Paragraph("3. Prüfen, übersetzen und erweitern", styles["H1MC"]),
            Paragraph("Gesundheitsprüfung", styles["H2MC"]),
            Paragraph("http://TRUENAS-IP:9998/health", styles["CodeMC"]),
            Paragraph(
                "Die Antwort muss unter anderem version 0.3.23, agent_api 3 und "
                "translator_managed true enthalten. Danach in Einstellungen bei Translator auf "
                "Verbindung testen klicken. Mission Control zeigt die erreichbaren Sprachcodes.",
                styles["BodyMC"],
            ),
            Paragraph("Übersetzung verwenden", styles["H2MC"]),
            bullet("Im Spiele-Infofenster auf Spieleinhalt übersetzen klicken, die Zielsprache im Dropdown auswählen und die Übersetzung starten.", styles),
            bullet("Der Stern markiert eine bevorzugte Zielsprache und sortiert sie beim nächsten Öffnen nach oben.", styles),
            bullet("Original anzeigen und Übersetzung anzeigen wechseln zwischen beiden Fassungen.", styles),
            Paragraph("Sprachen schlank erweitern", styles["H2MC"]),
            Paragraph(
                "Standardmäßig werden en,de,ru,it,fr,es,pt,pl,nl,tr als verwaltetes Sprachpaket geladen. Die Erkennung "
                "selbst ist nicht darauf beschränkt. Weitere Codes werden in LT_LOAD_ONLY "
                "kommasepariert ergänzt, zum Beispiel ar,zh,ja,ko. Nur tatsächlich "
                "benötigte Sprachen laden, weil Modelle Speicherplatz, Startzeit und Arbeitsspeicher "
                "benötigen.",
                styles["BodyMC"],
            ),
            Paragraph("Fehlerdiagnose", styles["H2MC"]),
        ]
    )
    diagnostics = [
        [Paragraph("Meldung", styles["TableMC"]), Paragraph("Prüfung", styles["TableMC"])],
        [Paragraph("Nicht eingerichtet", styles["TableMC"]), Paragraph("MISSION_CONTROL_TRANSLATOR_URL und translator-Dienst in derselben YAML prüfen.", styles["TableMC"])],
        [Paragraph("Nicht erreichbar", styles["TableMC"]), Paragraph("Erststart abwarten, Containerstatus und persistentes Model-Dataset prüfen.", styles["TableMC"])],
        [Paragraph("Sprache fehlt", styles["TableMC"]), Paragraph("Code in LT_LOAD_ONLY ergänzen, App neu bereitstellen und Modellinitialisierung abwarten.", styles["TableMC"])],
        [Paragraph("Text bleibt gemischt", styles["TableMC"]), Paragraph("Originalquelle prüfen und Übersetzung erneut auslösen; sehr kurze Abschnitte sind schwerer erkennbar.", styles["TableMC"])],
    ]
    diag_table = Table(diagnostics, colWidths=[47 * mm, 121 * mm], repeatRows=1)
    diag_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PANEL),
                ("TEXTCOLOR", (0, 0), (-1, 0), CYAN),
                ("FONTNAME", (0, 0), (-1, 0), "HypeSans-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#091D25")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend(
        [
            diag_table,
            Spacer(1, 5 * mm),
            Paragraph("Quellen und Lizenzhinweise", styles["H2MC"]),
            Paragraph(
                "LibreTranslate 1.9.6: github.com/LibreTranslate/LibreTranslate - GNU AGPL v3.0<br/>"
                "Container-Tags: hub.docker.com/r/libretranslate/libretranslate/tags<br/>"
                "TheGamesDB API: api.thegamesdb.net",
                styles["SmallMC"],
            ),
            Paragraph(
                "Diese Anleitung gehört zu HypeTek Mission Control. Der Besitz- und Urhebervermerk "
                "darf bei Weitergabe des Projektpakets nicht entfernt werden.",
                styles["CalloutMC"],
            ),
        ]
    )

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
    print(OUTPUT)
