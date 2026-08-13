#define MyAppName "HypeTek Mission Control Agent"
#define MyAppVersion "0.2.0.1"
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
VersionInfoVersion=0.2.0.1
VersionInfoDescription=HypeTek Mission Control Windows Agent Setup

[Files]
Source: "..\windows-agent\GameVaultAgent.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\windows-agent\Uninstall-Agent.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "mission-control.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\HypeTek Mission Control Agent entfernen"; Filename: "{uninstallexe}"

[UninstallDelete]
Type: files; Name: "{app}\agent.json"
Type: dirifempty; Name: "{app}"

[Code]
var
  ServerPage: TInputQueryWizardPage;
  PathPage: TInputQueryWizardPage;
  TokenPage: TInputQueryWizardPage;
  TokenHelpButton: TNewButton;

procedure ShowTokenHelp(Sender: TObject);
begin
  MsgBox(
    'Agent-Token und Agent-Key meinen in älteren Versionen denselben Wert.' + #13#10 + #13#10 +
    'Verwende ausschließlich GAMEVAULT_AGENT_TOKEN.' + #13#10 +
    'GAMEVAULT_SECRET_KEY gehört nicht in den Windows-Agenten.' + #13#10 + #13#10 +
    'Falls noch kein Agent-Token existiert:' + #13#10 + #13#10 +
    '1. TrueNAS-Shell öffnen.' + #13#10 +
    '2. Ausführen:' + #13#10 +
    'python3 -c "import secrets; print(secrets.token_urlsafe(32))"' + #13#10 +
    '3. Den ausgegebenen Wert kopieren.' + #13#10 +
    '4. Apps > gamevault > Edit öffnen.' + #13#10 +
    '5. GAMEVAULT_AGENT_TOKEN durch den neuen Wert ersetzen.' + #13#10 +
    '6. Speichern und warten, bis die App wieder Running zeigt.' + #13#10 +
    '7. Denselben Wert hier eintragen.' + #13#10 + #13#10 +
    'Den Token niemals in GitHub oder einen öffentlichen Chat kopieren.',
    mbInformation,
    MB_OK);
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
    Request.SetRequestHeader('X-Mission-Control-Validation', 'installer-0.2.0.1');
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
      MsgBox(
        'Der Agent-Token stimmt nicht mit GAMEVAULT_AGENT_TOKEN auf dem Server überein.' + #13#10 + #13#10 + 'Es wurde noch nichts gespeichert.',
        mbError,
        MB_OK)
    else
      MsgBox(
        'Der Server konnte den Agent-Token nicht eindeutig bestätigen.' + #13#10 +
        'HTTP-Status: ' + IntToStr(StatusCode) + #13#10 + #13#10 +
        'Bitte zuerst das aktuelle Mission-Control-Server-Image installieren.' + #13#10 + #13#10 +
        'Es wurde noch nichts gespeichert.',
        mbError,
        MB_OK);
  except
    MsgBox(
      'Der Agent-Token konnte nicht geprüft werden.' + #13#10 +
      'Serveradresse, Netzwerkverbindung und Port kontrollieren.' + #13#10 + #13#10 +
      'Es wurde noch nichts gespeichert.' + #13#10 + #13#10 +
      GetExceptionMessage,
      mbError,
      MB_OK);
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
    'Mission-Control-Server',
    'Adresse der Weboberfläche',
    'Trage die vollständige HTTP- oder HTTPS-Adresse deines Servers ein.');
  ServerPage.Add('Serveradresse:', False);
  ServerPage.Values[0] := 'http://10.69.78.143:9998';

  PathPage := CreateInputQueryPage(
    ServerPage.ID,
    'Spielebibliothek',
    'SMB-Pfad auf diesem Windows-PC',
    'Der Pfad muss auf denselben Games-Ordner zeigen, den Mission Control scannt.');
  PathPage.Add('Games-Pfad:', False);
  PathPage.Values[0] := 'Z:\Game';

  TokenPage := CreateInputQueryPage(
    PathPage.ID,
    'Agent-Token',
    'Sichere Verbindung zum Server',
    'Kopiere GAMEVAULT_AGENT_TOKEN aus der TrueNAS-Konfiguration. Der Wert wird vor der Installation geprüft.');
  TokenPage.Add('Agent-Token:', True);

  TokenHelpButton := TNewButton.Create(WizardForm);
  TokenHelpButton.Parent := TokenPage.Surface;
  TokenHelpButton.Caption := 'Hilfe zum Agent-Token';
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
      MsgBox('Die Serveradresse muss mit http:// oder https:// beginnen.', mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = PathPage.ID then
  begin
    if not DirExists(Trim(PathPage.Values[0])) then
    begin
      MsgBox('Der Games-Pfad ist für den aktuellen Windows-Benutzer nicht erreichbar.', mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = TokenPage.ID then
  begin
    if Length(Trim(TokenPage.Values[0])) < 20 then
    begin
      MsgBox('Der Agent-Token ist zu kurz oder fehlt. Es wurde noch nichts gespeichert.', mbError, MB_OK);
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
  SetArrayLength(ConfigLines, 5);
  ConfigLines[0] := '{';
  ConfigLines[1] := '  "server_url": "' + JsonEscape(RemoveBackslashUnlessRoot(Trim(ServerPage.Values[0]))) + '",';
  ConfigLines[2] := '  "agent_token": "' + JsonEscape(Trim(TokenPage.Values[0])) + '",';
  ConfigLines[3] := '  "game_root": "' + JsonEscape(Trim(PathPage.Values[0])) + '"';
  ConfigLines[4] := '}';
  if not SaveStringsToUTF8File(ConfigPath, ConfigLines, False) then
    RaiseException('Die Agent-Konfiguration konnte nicht gespeichert werden.');

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
