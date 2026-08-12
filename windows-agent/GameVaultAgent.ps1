param(
    [Parameter(Position = 0)]
    [string]$ProtocolUrl
)

$ErrorActionPreference = "Stop"
$ConfigPath = Join-Path $env:LOCALAPPDATA "HypeTek\GameVault\agent.json"

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Web

function Show-Error([string]$Message) {
    [System.Windows.MessageBox]::Show(
        $Message,
        "HypeTek GameVault",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
}

function Assert-PathInsideRoot([string]$Root, [string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        throw "Der Server hat keinen Startpfad geliefert."
    }
    if ([IO.Path]::IsPathRooted($RelativePath) -or $RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Der Server hat einen unzulässigen Pfad geliefert."
    }
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $candidate = [IO.Path]::GetFullPath((Join-Path $rootFull ($RelativePath -replace '/', '\')))
    if (-not $candidate.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Der Startpfad liegt außerhalb des freigegebenen Games-Ordners."
    }
    return $candidate
}

function Get-Ticket([string]$ServerUrl, [string]$AgentToken, [string]$Ticket) {
    $headers = @{ Authorization = "Bearer $AgentToken" }
    return Invoke-RestMethod -Method Get `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/tickets/$([Uri]::EscapeDataString($Ticket))" `
        -Headers $headers `
        -TimeoutSec 15
}

function Find-InstallerOnMountedIso([string]$DriveLetter) {
    $root = "$($DriveLetter):\"
    $autorun = Join-Path $root "autorun.inf"
    if (Test-Path -LiteralPath $autorun) {
        foreach ($line in Get-Content -LiteralPath $autorun -ErrorAction SilentlyContinue) {
            if ($line -match '^\s*(?:open|shellexecute)\s*=\s*(?:"([^"]+)"|([^\s]+))') {
                $relative = if ($Matches[1]) { $Matches[1] } else { $Matches[2] }
                $relative = ($relative -split '\s+/')[0].Trim('"')
                $candidate = Join-Path $root $relative
                if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
            }
        }
    }
    foreach ($name in @("setup.exe", "install.exe", "installer.exe", "autorun.exe")) {
        $candidate = Join-Path $root $name
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    $fallback = Get-ChildItem -LiteralPath $root -Filter *.msi -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($fallback) { return $fallback.FullName }
    return $null
}

try {
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        throw "Agent-Konfiguration fehlt: $ConfigPath"
    }
    $config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
    foreach ($required in @("server_url", "agent_token", "game_root")) {
        if ([string]::IsNullOrWhiteSpace($config.$required)) { throw "Konfigurationswert fehlt: $required" }
    }
    if ([string]::IsNullOrWhiteSpace($ProtocolUrl)) { throw "Kein GameVault-Auftrag empfangen." }
    $uri = [Uri]$ProtocolUrl
    if ($uri.Scheme -ne "hypetek-gamevault" -or $uri.Host -ne "launch") {
        throw "Ungültiger GameVault-Link."
    }
    $ticket = [System.Web.HttpUtility]::ParseQueryString($uri.Query).Get("ticket")
    if ([string]::IsNullOrWhiteSpace($ticket)) { throw "Ticket fehlt im GameVault-Link." }

    $manifest = Get-Ticket $config.server_url $config.agent_token $ticket
    $source = Assert-PathInsideRoot $config.game_root $manifest.launcher
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Der Pfad ist über SMB nicht erreichbar:`n$source"
    }
    if ($manifest.action -ne "open_folder" -and -not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Die erwartete Quelldatei ist kein regulärer Datenträger bzw. Installer:`n$source"
    }

    $message = "Titel: $($manifest.title)`n`nAktion: $($manifest.action)`nQuelle: $source`n`nFortfahren?"
    $answer = [System.Windows.MessageBox]::Show(
        $message,
        "HypeTek GameVault – Bestätigung",
        [System.Windows.MessageBoxButton]::YesNo,
        [System.Windows.MessageBoxImage]::Question
    )
    if ($answer -ne [System.Windows.MessageBoxResult]::Yes) { exit 0 }

    switch ($manifest.action) {
        "open_folder" {
            $folder = if (Test-Path -LiteralPath $source -PathType Container) {
                $source
            } else {
                Split-Path -LiteralPath $source -Parent
            }
            Start-Process explorer.exe -ArgumentList @($folder)
        }
        "direct_setup" {
            Start-Process -FilePath $source -WorkingDirectory (Split-Path -LiteralPath $source -Parent)
        }
        "iso" {
            $image = Mount-DiskImage -ImagePath $source -PassThru
            $volume = $image | Get-Volume | Where-Object DriveLetter | Select-Object -First 1
            if (-not $volume) { throw "Das ISO wurde eingebunden, aber kein Laufwerksbuchstabe erkannt." }
            $installer = Find-InstallerOnMountedIso $volume.DriveLetter
            if (-not $installer) {
                Start-Process explorer.exe "$($volume.DriveLetter):\"
                throw "ISO eingebunden, aber kein eindeutiger Installer erkannt. Das Laufwerk wurde geöffnet."
            }
            Start-Process -FilePath $installer -WorkingDirectory (Split-Path -LiteralPath $installer -Parent)
        }
        default { throw "Nicht unterstützte Aktion: $($manifest.action)" }
    }
}
catch {
    Show-Error $_.Exception.Message
    exit 1
}
