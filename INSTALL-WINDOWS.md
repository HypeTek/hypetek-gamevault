# Windows-Agent installieren

## Empfohlen: EXE-Installer

Der GitHub-Workflow erzeugt:

```text
HypeTek-Mission-Control-Agent-Setup.exe
```

Der Installer läuft ohne Administratorrechte für den aktuellen Benutzer und fragt:

1. Mission-Control-Adresse, zum Beispiel `http://10.69.78.143:9998`
2. lokalen SMB-Pfad, zum Beispiel `Z:\Game`
3. Agent-Token (`GAMEVAULT_AGENT_TOKEN`) aus der TrueNAS-App-Konfiguration

Danach registriert er das Protokoll `hypetek-gamevault://`. PowerShell 7 wird
bevorzugt; Windows PowerShell 5.1 dient als Fallback. Das Konsolenfenster bleibt beim
normalen Aufruf verborgen.

Die Weboberfläche enthält unter **SMB-/Tailscale-Hilfe** eine Schritt-für-Schritt-
Anleitung zum Verbinden des Netzlaufwerks, zu gespeicherten Windows-Anmeldedaten und
zum sicheren Zugriff über ein bestehendes Tailscale-Netz. SMB-Port 445 darf niemals
direkt am Router ins Internet freigegeben werden.

## PowerShell-Fallback

ZIP aus Mission Control herunterladen, vollständig entpacken und in einer normalen
PowerShell ausführen:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Agent.ps1 `
  -ServerUrl "http://10.69.78.143:9998" `
  -AgentToken "HIER_DEN_AGENT_TOKEN_EINTRAGEN" `
  -GameRoot "Z:\Game"
```

Die Konfiguration liegt unter:

```text
%LOCALAPPDATA%\HypeTek\MissionControl\agent.json
```

Eine vorhandene 0.1-Konfiguration unter `HypeTek\GameVault` wird weiterhin gelesen.

## Testreihenfolge

1. `Ordner öffnen`
2. vertrauenswürdiges direktes Setup
3. kleine ISO-Datei

Vor jeder Aktion zeigt Mission Control Titel, Aktion und Quelle an. SmartScreen und UAC
sind normale Windows-Sicherheitsabfragen des jeweiligen Installers.

## Deinstallation

Den Windows-Eintrag **HypeTek Mission Control Agent** unter *Installierte Apps* nutzen
oder beim PowerShell-Fallback ausführen:

```powershell
powershell -ExecutionPolicy Bypass -File .\Uninstall-Agent.ps1
```
