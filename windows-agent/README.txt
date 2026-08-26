HYPETEK MISSION CONTROL – WINDOWS-AGENT
Version 0.6.4

Mehrere Bibliotheken
--------------------
Der Installer richtet die primäre Bibliothek ein. Wird später in Mission
Control eine weitere Bibliothek geöffnet, fragt der Agent einmalig nach der
Bestätigung des vorgeschlagenen Windows-/SMB-Pfads. Erst nach deiner
Bestätigung wird diese Zuordnung ausschließlich lokal gespeichert. Stimmen
Serverpfad und Windows-Laufwerk nicht überein, verbinde zuerst das passende
SMB-Netzlaufwerk und versuche die Aktion danach erneut.

© 2026 Michael Härtwig · HypeTek

EMPFOHLENE INSTALLATION

Nutze in Mission Control die Schaltfläche „Windows-Agent herunterladen“.
Der EXE-Installer führt dich durch Serveradresse, SMB-Spielepfad und Agent-Token.
Direkt beim Start kannst du Deutsch, Englisch, Russisch, Italienisch,
Französisch, Spanisch, Portugiesisch, Polnisch, Niederländisch oder Türkisch wählen.

EN: Choose the setup language first. Connect the SMB network drive in File
Explorer, then enter the server address, games path and GAMEVAULT_AGENT_TOKEN.

RU: Сначала выберите язык установки. Подключите сетевой SMB-диск в Проводнике,
затем укажите адрес сервера, путь к играм и GAMEVAULT_AGENT_TOKEN.

IT: Scegli prima la lingua. Collega l'unità SMB in Esplora file, quindi inserisci
indirizzo del server, percorso giochi e GAMEVAULT_AGENT_TOKEN.

FR: Choisissez d'abord la langue. Connectez le lecteur SMB dans l'Explorateur,
puis saisissez l'adresse du serveur, le chemin des jeux et le jeton.

ES: Elige primero el idioma. Conecta la unidad SMB en el Explorador e introduce
la dirección del servidor, la ruta de juegos y el token.

PT: Escolha primeiro o idioma. Ligue a unidade SMB no Explorador e introduza o
endereço do servidor, o caminho dos jogos e o token.

PL: Najpierw wybierz język. Podłącz dysk SMB w Eksploratorze, a następnie podaj
adres serwera, ścieżkę gier i token.

NL: Kies eerst de taal. Koppel het SMB-station in Verkenner en voer daarna het
serveradres, games-pad en token in.

TR: Önce dili seçin. SMB sürücüsünü Dosya Gezgini'nde bağlayın ve ardından
sunucu adresini, oyun yolunu ve belirteci girin.

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
