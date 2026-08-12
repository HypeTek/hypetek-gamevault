# TrueTitan-Rollout (TrueNAS 25.04)

## Vor dem Installieren

Das Container-Image wird nach bestandenen Tests automatisch über GitHub Actions als
`ghcr.io/hypetek/hypetek-gamevault:latest` veröffentlicht. So bleibt die
TrueNAS-Konfiguration innerhalb der unterstützten Wege WebUI/CLI/API und benötigt
keine handgebauten Systemdienste.

Geplante Hostpfade:

| Zweck | Hostpfad | Containerpfad | Modus |
|---|---|---|---|
| Games | `/mnt/Titan/Game` | `/games` | read-only |
| Datenbank/Cover | `/mnt/Titan/Applications/gamevault` | `/config` | read-write |

Geplanter Web-Port: `9998` auf TrueTitan, Container-Port `8080`.

## Vorbereitung

```bash
sudo install -d -o 568 -g 568 -m 750 /mnt/Titan/Applications/gamevault
```

Vor der Bereitstellung drei voneinander unabhängige Geheimnisse erzeugen:

```bash
python3 - <<'PY'
import secrets
for name in ("GAMEVAULT_ADMIN_PASSWORD", "GAMEVAULT_AGENT_TOKEN", "GAMEVAULT_SECRET_KEY"):
    print(f"{name}={secrets.token_urlsafe(32)}")
PY
```

Diese Werte nicht in Screenshots, Logs oder das Handbuch kopieren. Das Admin-Kennwort
ist für die Weboberfläche; der Agent-Token kommt zusätzlich auf autorisierte
Windows-PCs; der Session-Key bleibt nur am Server.

## Vorgesehener Installationsweg

In TrueNAS: **Apps → Discover → ⋮ → Install via YAML**. App-Name `gamevault` und eine
Compose-Konfiguration mit dem Image, den beiden obigen Hostpfaden,
Port `9998:8080`, den drei Umgebungsvariablen, `cap_drop: ALL` und
`no-new-privileges:true` verwenden.

Die mitgelieferte `docker-compose.yml` dokumentiert die vollständige Zielkonfiguration.
Sie ist derzeit Build-Vorlage und noch nicht als fertige TrueNAS-YAML gedacht.

## Abnahmetests

1. Weboberfläche ausschließlich aus LAN/Tailscale öffnen und anmelden.
2. „Bibliothek scannen“ ausführen und Anzahl/Typen mit dem bekannten Bestand prüfen.
3. Einen manuellen Eintrag über „Ordner öffnen“ testen.
4. Ein direktes Setup testen und die Windows-Bestätigung abbrechen.
5. Ein kleines ISO testen.
6. CUE/BIN und Archive müssen ohne Installationsknopf als manuell erscheinen.
7. Container prüfen: Games-Mount muss `ro` sein und keine zusätzlichen Linux-
   Fähigkeiten besitzen.

## Netzwerkgrenze

Port 9998 nicht an der FritzBox oder am Omada ins öffentliche Internet weiterleiten.
Für Zugriff außerhalb des LANs Tailscale verwenden. Bei reinem HTTP kann ein Gerät im
gleichen Netz theoretisch Verkehr mitlesen; für ein späteres produktives Mehrbenutzer-
Setup ist HTTPS über den vorgesehenen Reverse Proxy sinnvoll.
