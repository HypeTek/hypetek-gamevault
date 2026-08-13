#define MyAppName "HypeTek Mission Control Agent"
#define MyAppVersion "0.2.0"
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
VersionInfoVersion=0.2.0.0
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
    'Agent-Key',
    'Sichere Verbindung zum Server',
    'Kopiere den Agent-Key aus der TrueNAS-Konfiguration. Er wird nur lokal gespeichert.');
  TokenPage.Add('Agent-Key:', True);
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
      MsgBox('Der Agent-Key ist zu kurz oder fehlt.', mbError, MB_OK);
      Result := False;
    end;
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
