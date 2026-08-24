#define MyAppName "HypeTek Mission Control Agent"
#define MyAppVersion "0.4.2"
#define MyAppPublisher "HypeTek"
#define MyAppExeName "GameVaultAgent.ps1"

[Setup]
AppId={{8C1DC445-68F0-48A5-85B4-C9839461A74E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\HypeTek\MissionControl
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist
OutputBaseFilename=HypeTek-Mission-Control-Agent-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=mission-control.ico
UninstallDisplayIcon={app}\mission-control.ico
VersionInfoVersion=0.4.2.0
VersionInfoDescription=HypeTek Mission Control Windows Agent Setup

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "pl"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "nl"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "tr"; MessagesFile: "compiler:Languages\Turkish.isl"

[CustomMessages]
de.ServerTitle=Mission-Control-Server
de.ServerSubtitle=Adresse der Weboberfläche
de.ServerDescription=Trage die vollständige HTTP- oder HTTPS-Adresse deines Servers ein.
de.ServerField=Serveradresse:
de.LibraryTitle=Spielebibliothek
de.LibrarySubtitle=SMB- oder lokaler Pfad auf diesem Windows-PC
de.LibraryDescription=Wichtig: Verbinde das SMB-Netzlaufwerk zuerst im Windows-Explorer. Der Pfad muss auf denselben Games-Ordner zeigen, den Mission Control scannt. Mit Durchsuchen kannst du anschließend das erreichbare Netzlaufwerk wählen.
de.LibraryField=Games-Pfad:
de.TokenTitle=Agent-Token
de.TokenSubtitle=Sichere Verbindung zum Server
de.TokenDescription=Kopiere GAMEVAULT_AGENT_TOKEN aus der TrueNAS-Konfiguration. Der Wert wird vor der Installation geprüft.
de.TokenField=Agent-Token:
de.TokenHelp=Hilfe zum Agent-Token
de.InvalidServer=Die Serveradresse muss mit http:// oder https:// beginnen.
de.InvalidPath=Der Games-Pfad ist für den aktuellen Windows-Benutzer nicht erreichbar.
de.ShortToken=Der Agent-Token ist zu kurz oder fehlt. Es wurde noch nichts gespeichert.
de.TokenRejected=Der Agent-Token stimmt nicht mit GAMEVAULT_AGENT_TOKEN auf dem Server überein.%n%nEs wurde noch nichts gespeichert.
de.TokenUnknown=Der Server konnte den Agent-Token nicht eindeutig bestätigen.%nHTTP-Status: %1%n%nBitte zuerst das aktuelle Mission-Control-Server-Image installieren.%n%nEs wurde noch nichts gespeichert.
de.TokenCheckFailed=Der Agent-Token konnte nicht geprüft werden.%nServeradresse, Netzwerkverbindung und Port kontrollieren.%n%nEs wurde noch nichts gespeichert.%n%n%1
de.ConfigWriteFailed=Die Agent-Konfiguration konnte nicht gespeichert werden.
de.TokenHelpText=Agent-Token und Agent-Key meinen in älteren Versionen denselben Wert.%n%nVerwende ausschließlich GAMEVAULT_AGENT_TOKEN.%nGAMEVAULT_SECRET_KEY gehört nicht in den Windows-Agenten.%n%nFalls noch kein Agent-Token existiert:%n%n1. TrueNAS-Shell öffnen.%n2. Ausführen: python3 -c "import secrets; print(secrets.token_urlsafe(32))"%n3. Den ausgegebenen Wert kopieren.%n4. Apps > gamevault > Edit öffnen.%n5. GAMEVAULT_AGENT_TOKEN ersetzen.%n6. Speichern und auf Running warten.%n7. Denselben Wert hier eintragen.%n%nDen Token niemals veröffentlichen.

en.ServerTitle=Mission Control server
en.ServerSubtitle=Web interface address
en.ServerDescription=Enter the complete HTTP or HTTPS address of your server.
en.ServerField=Server address:
en.LibraryTitle=Game library
en.LibrarySubtitle=SMB or local path on this Windows PC
en.LibraryDescription=Important: Connect the SMB network drive in File Explorer first. Select the same games folder that Mission Control scans. Browse can then select the reachable drive.
en.LibraryField=Games path:
en.TokenTitle=Agent token
en.TokenSubtitle=Secure server connection
en.TokenDescription=Copy GAMEVAULT_AGENT_TOKEN from the TrueNAS configuration. It is validated before installation.
en.TokenField=Agent token:
en.TokenHelp=Agent-token help
en.InvalidServer=The server address must begin with http:// or https://.
en.InvalidPath=The games path is not reachable for the current Windows user.
en.ShortToken=The agent token is missing or too short. Nothing has been saved.
en.TokenRejected=The agent token does not match GAMEVAULT_AGENT_TOKEN on the server.%n%nNothing has been saved.
en.TokenUnknown=The server could not confirm the agent token unambiguously.%nHTTP status: %1%n%nInstall the current Mission Control server image first.%n%nNothing has been saved.
en.TokenCheckFailed=The agent token could not be checked.%nCheck the server address, network connection and port.%n%nNothing has been saved.%n%n%1
en.ConfigWriteFailed=The agent configuration could not be saved.
en.TokenHelpText=Agent token and Agent key referred to the same value in older releases.%n%nUse only GAMEVAULT_AGENT_TOKEN.%nGAMEVAULT_SECRET_KEY does not belong in the Windows Agent.%n%nIf no token exists yet:%n%n1. Open the TrueNAS shell.%n2. Run: python3 -c "import secrets; print(secrets.token_urlsafe(32))"%n3. Copy the value.%n4. Open Apps > gamevault > Edit.%n5. Replace GAMEVAULT_AGENT_TOKEN.%n6. Save and wait for Running.%n7. Enter the same value here.%n%nNever publish the token.

ru.ServerTitle=Сервер Mission Control
ru.ServerSubtitle=Адрес веб-интерфейса
ru.ServerDescription=Введите полный HTTP- или HTTPS-адрес сервера.
ru.ServerField=Адрес сервера:
ru.LibraryTitle=Библиотека игр
ru.LibrarySubtitle=SMB- или локальный путь на этом ПК
ru.LibraryDescription=Сначала подключите сетевой SMB-диск в Проводнике Windows. Выберите ту же папку игр, которую сканирует Mission Control.
ru.LibraryField=Путь к играм:
ru.TokenTitle=Токен агента
ru.TokenSubtitle=Безопасное соединение с сервером
ru.TokenDescription=Скопируйте GAMEVAULT_AGENT_TOKEN из конфигурации TrueNAS. Перед установкой токен будет проверен.
ru.TokenField=Токен агента:
ru.TokenHelp=Справка по токену
ru.InvalidServer=Адрес сервера должен начинаться с http:// или https://.
ru.InvalidPath=Путь к играм недоступен текущему пользователю Windows.
ru.ShortToken=Токен отсутствует или слишком короткий. Ничего не сохранено.
ru.TokenRejected=Токен не совпадает с GAMEVAULT_AGENT_TOKEN на сервере.%n%nНичего не сохранено.
ru.TokenUnknown=Сервер не смог однозначно подтвердить токен.%nHTTP-статус: %1%n%nСначала установите актуальный образ Mission Control.%n%nНичего не сохранено.
ru.TokenCheckFailed=Не удалось проверить токен.%nПроверьте адрес сервера, сеть и порт.%n%nНичего не сохранено.%n%n%1
ru.ConfigWriteFailed=Не удалось сохранить конфигурацию агента.
ru.TokenHelpText=Используйте только GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY не предназначен для Windows Agent.%n%nСоздайте токен в оболочке TrueNAS, сохраните его в Apps > gamevault > Edit и введите то же значение здесь. Никогда не публикуйте токен.

it.ServerTitle=Server Mission Control
it.ServerSubtitle=Indirizzo dell'interfaccia web
it.ServerDescription=Inserisci l'indirizzo HTTP o HTTPS completo del server.
it.ServerField=Indirizzo server:
it.LibraryTitle=Libreria giochi
it.LibrarySubtitle=Percorso SMB o locale su questo PC Windows
it.LibraryDescription=Collega prima l'unità di rete SMB in Esplora file. Seleziona la stessa cartella giochi analizzata da Mission Control.
it.LibraryField=Percorso giochi:
it.TokenTitle=Token agente
it.TokenSubtitle=Connessione sicura al server
it.TokenDescription=Copia GAMEVAULT_AGENT_TOKEN dalla configurazione TrueNAS. Verrà verificato prima dell'installazione.
it.TokenField=Token agente:
it.TokenHelp=Guida al token
it.InvalidServer=L'indirizzo deve iniziare con http:// o https://.
it.InvalidPath=Il percorso giochi non è raggiungibile dall'utente Windows corrente.
it.ShortToken=Il token manca o è troppo corto. Non è stato salvato nulla.
it.TokenRejected=Il token non corrisponde a GAMEVAULT_AGENT_TOKEN sul server.%n%nNon è stato salvato nulla.
it.TokenUnknown=Il server non ha potuto confermare il token.%nStato HTTP: %1%n%nInstalla prima l'immagine aggiornata di Mission Control.%n%nNon è stato salvato nulla.
it.TokenCheckFailed=Impossibile verificare il token.%nControlla indirizzo, rete e porta.%n%nNon è stato salvato nulla.%n%n%1
it.ConfigWriteFailed=Impossibile salvare la configurazione dell'agente.
it.TokenHelpText=Usa esclusivamente GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY non appartiene al Windows Agent. Crea il token nella shell TrueNAS, salvalo in Apps > gamevault > Edit e inserisci qui lo stesso valore. Non pubblicarlo mai.

fr.ServerTitle=Serveur Mission Control
fr.ServerSubtitle=Adresse de l'interface web
fr.ServerDescription=Saisissez l'adresse HTTP ou HTTPS complète du serveur.
fr.ServerField=Adresse du serveur :
fr.LibraryTitle=Bibliothèque de jeux
fr.LibrarySubtitle=Chemin SMB ou local sur ce PC Windows
fr.LibraryDescription=Connectez d'abord le lecteur réseau SMB dans l'Explorateur. Choisissez le même dossier de jeux que Mission Control analyse.
fr.LibraryField=Chemin des jeux :
fr.TokenTitle=Jeton de l'agent
fr.TokenSubtitle=Connexion sécurisée au serveur
fr.TokenDescription=Copiez GAMEVAULT_AGENT_TOKEN depuis TrueNAS. Il sera vérifié avant l'installation.
fr.TokenField=Jeton de l'agent :
fr.TokenHelp=Aide sur le jeton
fr.InvalidServer=L'adresse doit commencer par http:// ou https://.
fr.InvalidPath=Le chemin des jeux n'est pas accessible à l'utilisateur Windows actuel.
fr.ShortToken=Le jeton manque ou est trop court. Rien n'a été enregistré.
fr.TokenRejected=Le jeton ne correspond pas à GAMEVAULT_AGENT_TOKEN sur le serveur.%n%nRien n'a été enregistré.
fr.TokenUnknown=Le serveur n'a pas pu confirmer le jeton.%nÉtat HTTP : %1%n%nInstallez d'abord l'image actuelle de Mission Control.%n%nRien n'a été enregistré.
fr.TokenCheckFailed=Impossible de vérifier le jeton.%nVérifiez l'adresse, le réseau et le port.%n%nRien n'a été enregistré.%n%n%1
fr.ConfigWriteFailed=Impossible d'enregistrer la configuration de l'agent.
fr.TokenHelpText=Utilisez uniquement GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY ne doit pas être saisi dans Windows Agent. Créez le jeton dans le shell TrueNAS, enregistrez-le sous Apps > gamevault > Edit et saisissez la même valeur ici. Ne le publiez jamais.

es.ServerTitle=Servidor Mission Control
es.ServerSubtitle=Dirección de la interfaz web
es.ServerDescription=Introduce la dirección HTTP o HTTPS completa del servidor.
es.ServerField=Dirección del servidor:
es.LibraryTitle=Biblioteca de juegos
es.LibrarySubtitle=Ruta SMB o local en este PC Windows
es.LibraryDescription=Conecta primero la unidad SMB en el Explorador. Elige la misma carpeta de juegos que analiza Mission Control.
es.LibraryField=Ruta de juegos:
es.TokenTitle=Token del agente
es.TokenSubtitle=Conexión segura con el servidor
es.TokenDescription=Copia GAMEVAULT_AGENT_TOKEN desde TrueNAS. Se validará antes de instalar.
es.TokenField=Token del agente:
es.TokenHelp=Ayuda del token
es.InvalidServer=La dirección debe comenzar con http:// o https://.
es.InvalidPath=La ruta de juegos no es accesible para el usuario actual.
es.ShortToken=Falta el token o es demasiado corto. No se ha guardado nada.
es.TokenRejected=El token no coincide con GAMEVAULT_AGENT_TOKEN del servidor.%n%nNo se ha guardado nada.
es.TokenUnknown=El servidor no pudo confirmar el token.%nEstado HTTP: %1%n%nInstala primero la imagen actual de Mission Control.%n%nNo se ha guardado nada.
es.TokenCheckFailed=No se pudo comprobar el token.%nComprueba dirección, red y puerto.%n%nNo se ha guardado nada.%n%n%1
es.ConfigWriteFailed=No se pudo guardar la configuración del agente.
es.TokenHelpText=Usa solo GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY no pertenece al Windows Agent. Crea el token en la consola TrueNAS, guárdalo en Apps > gamevault > Edit e introduce aquí el mismo valor. Nunca lo publiques.

pt.ServerTitle=Servidor Mission Control
pt.ServerSubtitle=Endereço da interface web
pt.ServerDescription=Introduza o endereço HTTP ou HTTPS completo do servidor.
pt.ServerField=Endereço do servidor:
pt.LibraryTitle=Biblioteca de jogos
pt.LibrarySubtitle=Caminho SMB ou local neste PC Windows
pt.LibraryDescription=Ligue primeiro a unidade SMB no Explorador. Selecione a mesma pasta de jogos analisada pelo Mission Control.
pt.LibraryField=Caminho dos jogos:
pt.TokenTitle=Token do agente
pt.TokenSubtitle=Ligação segura ao servidor
pt.TokenDescription=Copie GAMEVAULT_AGENT_TOKEN do TrueNAS. Será validado antes da instalação.
pt.TokenField=Token do agente:
pt.TokenHelp=Ajuda do token
pt.InvalidServer=O endereço deve começar com http:// ou https://.
pt.InvalidPath=O caminho dos jogos não está acessível ao utilizador atual.
pt.ShortToken=O token está ausente ou é demasiado curto. Nada foi guardado.
pt.TokenRejected=O token não corresponde ao GAMEVAULT_AGENT_TOKEN no servidor.%n%nNada foi guardado.
pt.TokenUnknown=O servidor não confirmou o token.%nEstado HTTP: %1%n%nInstale primeiro a imagem atual do Mission Control.%n%nNada foi guardado.
pt.TokenCheckFailed=Não foi possível verificar o token.%nVerifique endereço, rede e porta.%n%nNada foi guardado.%n%n%1
pt.ConfigWriteFailed=Não foi possível guardar a configuração do agente.
pt.TokenHelpText=Use apenas GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY não pertence ao Windows Agent. Crie o token no shell TrueNAS, guarde-o em Apps > gamevault > Edit e introduza aqui o mesmo valor. Nunca o publique.

pl.ServerTitle=Serwer Mission Control
pl.ServerSubtitle=Adres interfejsu WWW
pl.ServerDescription=Wprowadź pełny adres HTTP lub HTTPS serwera.
pl.ServerField=Adres serwera:
pl.LibraryTitle=Biblioteka gier
pl.LibrarySubtitle=Ścieżka SMB lub lokalna na tym komputerze
pl.LibraryDescription=Najpierw podłącz dysk SMB w Eksploratorze. Wybierz ten sam folder gier, który skanuje Mission Control.
pl.LibraryField=Ścieżka gier:
pl.TokenTitle=Token agenta
pl.TokenSubtitle=Bezpieczne połączenie z serwerem
pl.TokenDescription=Skopiuj GAMEVAULT_AGENT_TOKEN z TrueNAS. Zostanie sprawdzony przed instalacją.
pl.TokenField=Token agenta:
pl.TokenHelp=Pomoc dotycząca tokenu
pl.InvalidServer=Adres musi zaczynać się od http:// lub https://.
pl.InvalidPath=Ścieżka gier jest niedostępna dla bieżącego użytkownika.
pl.ShortToken=Brak tokenu lub jest za krótki. Nic nie zapisano.
pl.TokenRejected=Token nie pasuje do GAMEVAULT_AGENT_TOKEN na serwerze.%n%nNic nie zapisano.
pl.TokenUnknown=Serwer nie potwierdził tokenu.%nStatus HTTP: %1%n%nNajpierw zainstaluj aktualny obraz Mission Control.%n%nNic nie zapisano.
pl.TokenCheckFailed=Nie można sprawdzić tokenu.%nSprawdź adres, sieć i port.%n%nNic nie zapisano.%n%n%1
pl.ConfigWriteFailed=Nie można zapisać konfiguracji agenta.
pl.TokenHelpText=Używaj wyłącznie GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY nie jest przeznaczony dla Windows Agent. Utwórz token w powłoce TrueNAS, zapisz go w Apps > gamevault > Edit i wpisz tę samą wartość tutaj. Nigdy go nie publikuj.

nl.ServerTitle=Mission Control-server
nl.ServerSubtitle=Adres van de webinterface
nl.ServerDescription=Voer het volledige HTTP- of HTTPS-adres van de server in.
nl.ServerField=Serveradres:
nl.LibraryTitle=Gamebibliotheek
nl.LibrarySubtitle=SMB- of lokaal pad op deze Windows-pc
nl.LibraryDescription=Koppel eerst het SMB-station in Verkenner. Kies dezelfde gamemap die Mission Control scant.
nl.LibraryField=Games-pad:
nl.TokenTitle=Agenttoken
nl.TokenSubtitle=Veilige serververbinding
nl.TokenDescription=Kopieer GAMEVAULT_AGENT_TOKEN uit TrueNAS. Het token wordt vóór installatie gecontroleerd.
nl.TokenField=Agenttoken:
nl.TokenHelp=Hulp bij agenttoken
nl.InvalidServer=Het adres moet beginnen met http:// of https://.
nl.InvalidPath=Het games-pad is niet bereikbaar voor de huidige gebruiker.
nl.ShortToken=Het token ontbreekt of is te kort. Er is niets opgeslagen.
nl.TokenRejected=Het token komt niet overeen met GAMEVAULT_AGENT_TOKEN op de server.%n%nEr is niets opgeslagen.
nl.TokenUnknown=De server kon het token niet bevestigen.%nHTTP-status: %1%n%nInstalleer eerst de huidige Mission Control-image.%n%nEr is niets opgeslagen.
nl.TokenCheckFailed=Het token kon niet worden gecontroleerd.%nControleer adres, netwerk en poort.%n%nEr is niets opgeslagen.%n%n%1
nl.ConfigWriteFailed=De agentconfiguratie kon niet worden opgeslagen.
nl.TokenHelpText=Gebruik uitsluitend GAMEVAULT_AGENT_TOKEN. GAMEVAULT_SECRET_KEY hoort niet in Windows Agent. Maak het token in de TrueNAS-shell, sla het op via Apps > gamevault > Edit en voer hier dezelfde waarde in. Publiceer het nooit.

tr.ServerTitle=Mission Control sunucusu
tr.ServerSubtitle=Web arayüzü adresi
tr.ServerDescription=Sunucunun tam HTTP veya HTTPS adresini girin.
tr.ServerField=Sunucu adresi:
tr.LibraryTitle=Oyun kitaplığı
tr.LibrarySubtitle=Bu Windows bilgisayardaki SMB veya yerel yol
tr.LibraryDescription=Önce SMB ağ sürücüsünü Dosya Gezgini'nde bağlayın. Mission Control'ün taradığı aynı oyun klasörünü seçin.
tr.LibraryField=Oyun yolu:
tr.TokenTitle=Ajan belirteci
tr.TokenSubtitle=Güvenli sunucu bağlantısı
tr.TokenDescription=TrueNAS yapılandırmasındaki GAMEVAULT_AGENT_TOKEN değerini kopyalayın. Kurulumdan önce doğrulanır.
tr.TokenField=Ajan belirteci:
tr.TokenHelp=Belirteç yardımı
tr.InvalidServer=Adres http:// veya https:// ile başlamalıdır.
tr.InvalidPath=Oyun yolu geçerli Windows kullanıcısı tarafından erişilemiyor.
tr.ShortToken=Belirteç yok veya çok kısa. Hiçbir şey kaydedilmedi.
tr.TokenRejected=Belirteç sunucudaki GAMEVAULT_AGENT_TOKEN ile eşleşmiyor.%n%nHiçbir şey kaydedilmedi.
tr.TokenUnknown=Sunucu belirteci doğrulayamadı.%nHTTP durumu: %1%n%nÖnce güncel Mission Control imajını kurun.%n%nHiçbir şey kaydedilmedi.
tr.TokenCheckFailed=Belirteç denetlenemedi.%nAdres, ağ ve portu kontrol edin.%n%nHiçbir şey kaydedilmedi.%n%n%1
tr.ConfigWriteFailed=Ajan yapılandırması kaydedilemedi.
tr.TokenHelpText=Yalnızca GAMEVAULT_AGENT_TOKEN kullanın. GAMEVAULT_SECRET_KEY Windows Agent için değildir. TrueNAS kabuğunda belirteç oluşturun, Apps > gamevault > Edit içinde kaydedin ve aynı değeri buraya girin. Asla yayımlamayın.

[Files]
Source: "..\windows-agent\GameVaultAgent.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\windows-agent\Uninstall-Agent.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "mission-control.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[UninstallDelete]
Type: files; Name: "{app}\agent.json"
Type: dirifempty; Name: "{app}"

[Code]
var
  ServerPage: TInputQueryWizardPage;
  PathPage: TInputDirWizardPage;
  TokenPage: TInputQueryWizardPage;
  TokenHelpButton: TNewButton;

procedure ShowTokenHelp(Sender: TObject);
begin
  MsgBox(CustomMessage('TokenHelpText'), mbInformation, MB_OK);
end;

function ValidateAgentToken: Boolean;
var
  Request: Variant;
  StatusCode: Integer;
  ValidationHeader: String;
  ValidationUrl: String;
begin
  Result := False;
  ValidationUrl := RemoveBackslashUnlessRoot(Trim(ServerPage.Values[0])) +
    '/api/agent/validate';
  try
    Request := CreateOleObject('WinHttp.WinHttpRequest.5.1');
    Request.Open('POST', ValidationUrl, False);
    Request.SetTimeouts(5000, 5000, 5000, 10000);
    Request.SetRequestHeader('Authorization', 'Bearer ' + Trim(TokenPage.Values[0]));
    Request.SetRequestHeader('Cache-Control', 'no-cache, no-store');
    Request.SetRequestHeader('Pragma', 'no-cache');
    Request.SetRequestHeader('X-Mission-Control-Validation', 'installer-0.4.2');
    Request.Send('');
    StatusCode := Request.Status;

    ValidationHeader := '';
    try
      ValidationHeader := Request.GetResponseHeader('X-Mission-Control-Agent');
    except
      ValidationHeader := '';
    end;

    { Only the dedicated validation endpoint can produce both signals.
      A generic 204/404 page or an older server version must never pass. }
    if (StatusCode = 204) and (ValidationHeader = 'authenticated') then
      Result := True
    else if StatusCode = 401 then
      MsgBox(CustomMessage('TokenRejected'), mbError, MB_OK)
    else
      MsgBox(FmtMessage(CustomMessage('TokenUnknown'), [IntToStr(StatusCode)]), mbError, MB_OK);
  except
    MsgBox(FmtMessage(CustomMessage('TokenCheckFailed'), [GetExceptionMessage]), mbError, MB_OK);
  end;
end;

function JsonEscape(Value: String): String;
begin
  StringChangeEx(Value, '\', '\\', True);
  StringChangeEx(Value, '"', '\"', True);
  StringChangeEx(Value, #13#10, '\n', True);
  Result := Value;
end;

procedure InitializeWizard;
begin
  ServerPage := CreateInputQueryPage(
    wpSelectDir,
    CustomMessage('ServerTitle'),
    CustomMessage('ServerSubtitle'),
    CustomMessage('ServerDescription'));
  ServerPage.Add(CustomMessage('ServerField'), False);
  ServerPage.Values[0] := 'http://10.69.78.143:9998';

  PathPage := CreateInputDirPage(
    ServerPage.ID,
    CustomMessage('LibraryTitle'),
    CustomMessage('LibrarySubtitle'),
    CustomMessage('LibraryDescription'),
    False,
    '');
  PathPage.Add(CustomMessage('LibraryField'));
  PathPage.Values[0] := 'Z:\Game';

  TokenPage := CreateInputQueryPage(
    PathPage.ID,
    CustomMessage('TokenTitle'),
    CustomMessage('TokenSubtitle'),
    CustomMessage('TokenDescription'));
  TokenPage.Add(CustomMessage('TokenField'), True);

  TokenHelpButton := TNewButton.Create(WizardForm);
  TokenHelpButton.Parent := TokenPage.Surface;
  TokenHelpButton.Caption := CustomMessage('TokenHelp');
  TokenHelpButton.SetBounds(
    0,
    TokenPage.Edits[0].Top + TokenPage.Edits[0].Height + ScaleY(12),
    ScaleX(160),
    ScaleY(28));
  TokenHelpButton.OnClick := @ShowTokenHelp;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ServerValue: String;
begin
  Result := True;
  if CurPageID = ServerPage.ID then
  begin
    ServerValue := Lowercase(Trim(ServerPage.Values[0]));
    if (Pos('http://', ServerValue) <> 1) and (Pos('https://', ServerValue) <> 1) then
    begin
      MsgBox(CustomMessage('InvalidServer'), mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = PathPage.ID then
  begin
    if not DirExists(Trim(PathPage.Values[0])) then
    begin
      MsgBox(CustomMessage('InvalidPath'), mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = TokenPage.ID then
  begin
    if Length(Trim(TokenPage.Values[0])) < 20 then
    begin
      MsgBox(CustomMessage('ShortToken'), mbError, MB_OK);
      Result := False;
    end
    else
      Result := ValidateAgentToken;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: String;
  ConfigLines: TArrayOfString;
  PowerShellExecutable: String;
  ProtocolCommand: String;
begin
  if CurStep <> ssPostInstall then
    Exit;

  ConfigPath := ExpandConstant('{app}\agent.json');
  SetArrayLength(ConfigLines, 6);
  ConfigLines[0] := '{';
  ConfigLines[1] := '  "server_url": "' + JsonEscape(RemoveBackslashUnlessRoot(Trim(ServerPage.Values[0]))) + '",';
  ConfigLines[2] := '  "agent_token": "' + JsonEscape(Trim(TokenPage.Values[0])) + '",';
  ConfigLines[3] := '  "game_root": "' + JsonEscape(Trim(PathPage.Values[0])) + '",';
  ConfigLines[4] := '  "installer_language": "' + JsonEscape(ActiveLanguage) + '"';
  ConfigLines[5] := '}';
  if not SaveStringsToUTF8File(ConfigPath, ConfigLines, False) then
    RaiseException(CustomMessage('ConfigWriteFailed'));

  PowerShellExecutable := ExpandConstant('{pf}\PowerShell\7\pwsh.exe');
  if not FileExists(PowerShellExecutable) then
    PowerShellExecutable := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');

  ProtocolCommand :=
    '"' + PowerShellExecutable + '" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{app}\{#MyAppExeName}') + '" "%1"';

  RegWriteStringValue(HKCU, 'Software\Classes\hypetek-gamevault', '', 'URL:HypeTek Mission Control Protocol');
  RegWriteStringValue(HKCU, 'Software\Classes\hypetek-gamevault', 'URL Protocol', '');
  RegWriteStringValue(HKCU, 'Software\Classes\hypetek-gamevault\DefaultIcon', '', ExpandConstant('{app}\mission-control.ico'));
  RegWriteStringValue(HKCU, 'Software\Classes\hypetek-gamevault\shell\open\command', '', ProtocolCommand);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\hypetek-gamevault');
end;
