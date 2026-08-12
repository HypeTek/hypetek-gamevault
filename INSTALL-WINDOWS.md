# Windows-Agent installieren

Voraussetzung: Die TrueTitan-Freigabe ist beim gleichen Windows-Benutzer als
`Z:` verbunden und der Games-Ordner ist unter `Z:\Game` erreichbar.

1. Den Ordner `windows-agent` auf den Windows-PC kopieren.
2. PowerShell **normal, nicht als Administrator** öffnen.
3. In den kopierten Ordner wechseln.
4. Den Agenten installieren:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Agent.ps1 `
  -ServerUrl "http://10.69.78.143:9998" `
  -AgentToken "HIER_DEN_GAMEVAULT_AGENT_TOKEN_EINTRAGEN" `
  -GameRoot "Z:\Game"
```

Die Installation erfolgt nur für den aktuellen Benutzer unter
`%LOCALAPPDATA%\HypeTek\GameVault`. Dort liegt auch `agent.json` mit Serveradresse,
Agent-Token und SMB-Wurzel. Das Protokoll wird unter `HKCU\Software\Classes`
registriert und benötigt daher keine Administratorrechte.

Beim ersten Klick im Browser fragt Windows eventuell, ob der Link mit PowerShell
geöffnet werden darf. Erst danach zeigt GameVault seine eigene Bestätigungsabfrage.

## Fehlerdiagnose

- **Pfad nicht erreichbar:** Im Explorer prüfen, ob `Z:\Game` beim aktuellen Benutzer
  geöffnet werden kann.
- **Ticket ungültig:** Erneut auf Installieren/Ordner öffnen klicken; Tickets gelten nur
  120 Sekunden und genau einmal.
- **ISO lässt sich nicht mounten:** Datei zunächst über „Ordner öffnen“ anzeigen und in
  Windows manuell einbinden.
- **Installer fordert Adminrechte:** Das ist die normale Windows-UAC des Installers und
  keine Rechteerweiterung durch GameVault.

Deinstallation:

```powershell
powershell -ExecutionPolicy Bypass -File .\Uninstall-Agent.ps1
```

