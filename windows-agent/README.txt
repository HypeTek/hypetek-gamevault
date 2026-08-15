HYPETEK MISSION CONTROL – WINDOWS-AGENT
Version 0.3.15

© 2026 Michael Härtwig · HypeTek

EMPFOHLENE INSTALLATION

Nutze in Mission Control die Schaltfläche „Windows-Agent herunterladen“.
Der EXE-Installer führt dich durch Serveradresse, SMB-Spielepfad und Agent-Token.

POWERSHELL-FALLBACK (NUR FÜR EXPERTEN)

1. Dieses ZIP vollständig entpacken.
2. Install-Agent.ps1 mit Windows PowerShell ausführen.
3. Als Serveradresse die Adresse von Mission Control eintragen.
4. Als Spielepfad das verbundene SMB-Laufwerk auswählen, z. B. Z:\Game.
5. Ausschließlich GAMEVAULT_AGENT_TOKEN verwenden.
   GAMEVAULT_SECRET_KEY gehört niemals in den Windows-Agenten.
6. In Mission Control „Verbindung prüfen“ wählen.

DATEIEN

- GameVaultAgent.ps1: führt bestätigte Mission-Control-Aufträge aus.
- Install-Agent.ps1: richtet Agent und Windows-Protokoll ein.
- Uninstall-Agent.ps1: entfernt Agent, Konfiguration und Protokoll wieder.

SICHERHEIT

- Installationsmedien nur aus vertrauenswürdigen Quellen verwenden.
- SMB-Port 445 niemals direkt aus dem Internet erreichbar machen.
- Für Fernzugriff Tailscale oder ein abgesichertes VPN verwenden.
- Agent-Token nicht veröffentlichen und nicht in Git-Repositories speichern.

Projekt: https://github.com/HypeTek/hypetek-gamevault
