param(
    [Parameter(Mandatory = $true)][string]$ServerUrl,
    [Parameter(Mandatory = $true)][string]$AgentToken,
    [string]$GameRoot = "Z:\Game"
)

$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "HypeTek\MissionControl"
$ConfigDir = $InstallDir
$AgentSource = Join-Path $PSScriptRoot "GameVaultAgent.ps1"
$AgentTarget = Join-Path $InstallDir "GameVaultAgent.ps1"

if (-not (Test-Path -LiteralPath $AgentSource -PathType Leaf)) {
    throw "GameVaultAgent.ps1 wurde neben dem Installer nicht gefunden."
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
Copy-Item -LiteralPath $AgentSource -Destination $AgentTarget -Force

$config = [ordered]@{
    server_url = $ServerUrl.TrimEnd('/')
    agent_token = $AgentToken
    game_root = [IO.Path]::GetFullPath($GameRoot)
}
$config | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $ConfigDir "agent.json") -Encoding UTF8

$PowerShellCommand = Get-Command "pwsh.exe" -ErrorAction SilentlyContinue
if ($PowerShellCommand) {
    $PowerShellExecutable = $PowerShellCommand.Source
} else {
    $PowerShellExecutable = (Get-Command "powershell.exe" -ErrorAction Stop).Source
}

$command = '"' + $PowerShellExecutable + '" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $AgentTarget + '" "%1"'
$protocol = "Registry::HKEY_CURRENT_USER\Software\Classes\hypetek-gamevault"
New-Item -Path $protocol -Force | Out-Null
Set-Item -Path $protocol -Value "URL:HypeTek Mission Control Protocol"
New-ItemProperty -Path $protocol -Name "URL Protocol" -Value "" -PropertyType String -Force | Out-Null
New-Item -Path "$protocol\DefaultIcon" -Force | Out-Null
Set-Item -Path "$protocol\DefaultIcon" -Value "powershell.exe,0"
New-Item -Path "$protocol\shell\open\command" -Force | Out-Null
Set-Item -Path "$protocol\shell\open\command" -Value $command

Write-Host "HypeTek Mission Control Agent installiert." -ForegroundColor Green
Write-Host "Server:    $($config.server_url)"
Write-Host "Games:     $($config.game_root)"
Write-Host "PowerShell: $PowerShellExecutable"
Write-Host "Protokoll: hypetek-gamevault://"
