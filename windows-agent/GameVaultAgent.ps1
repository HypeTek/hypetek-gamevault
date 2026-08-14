param(
    [Parameter(Position = 0)]
    [string]$ProtocolUrl
)

$ErrorActionPreference = "Stop"
$ConfigPath = Join-Path $env:LOCALAPPDATA "HypeTek\MissionControl\agent.json"
$LegacyConfigPath = Join-Path $env:LOCALAPPDATA "HypeTek\GameVault\agent.json"
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf) -and (Test-Path -LiteralPath $LegacyConfigPath -PathType Leaf)) {
    $ConfigPath = $LegacyConfigPath
}

Add-Type -AssemblyName PresentationFramework

function Show-Error([string]$Message) {
    [System.Windows.MessageBox]::Show(
        $Message,
        "HypeTek Mission Control",
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
    try {
        return Invoke-RestMethod -Method Get `
            -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/tickets/$([Uri]::EscapeDataString($Ticket))" `
            -Headers $headers `
            -TimeoutSec 15
    }
    catch {
        $status = 0
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        if ($status -eq 404) {
            throw "Der Startauftrag ist ungültig oder abgelaufen. Bitte in Mission Control erneut anklicken."
        }
        if ($status -eq 401) {
            throw "Der Agent-Token stimmt nicht mit dem Mission-Control-Server überein."
        }
        throw "Mission Control ist nicht erreichbar: $($_.Exception.Message)"
    }
}

function Confirm-Probe([string]$ServerUrl, [string]$AgentToken, [string]$Token) {
    $headers = @{ Authorization = "Bearer $AgentToken" }
    try {
        Invoke-RestMethod -Method Post `
            -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/probes/$([Uri]::EscapeDataString($Token))/confirm" `
            -Headers $headers `
            -TimeoutSec 15 | Out-Null
    }
    catch {
        $status = 0
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        if ($status -eq 401) { throw "Der Agent-Token stimmt nicht mit dem Mission-Control-Server überein." }
        if ($status -eq 404) { throw "Die Agent-Prüfung ist ungültig oder abgelaufen." }
        throw "Mission Control ist nicht erreichbar: $($_.Exception.Message)"
    }
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
    if ([string]::IsNullOrWhiteSpace($ProtocolUrl)) { throw "Kein Mission-Control-Auftrag empfangen." }
    $uri = [Uri]$ProtocolUrl
    if ($uri.Scheme -ne "hypetek-gamevault" -or $uri.Host -notin @("launch", "probe")) {
        throw "Ungültiger Mission-Control-Link."
    }

    if ($uri.Host -eq "probe") {
        $probeToken = $null
        foreach ($pair in $uri.Query.TrimStart('?').Split('&')) {
            if ([string]::IsNullOrWhiteSpace($pair)) { continue }
            $parts = $pair -split '=', 2
            if ([Uri]::UnescapeDataString($parts[0]) -eq "token" -and $parts.Count -eq 2) {
                $probeToken = [Uri]::UnescapeDataString($parts[1])
                break
            }
        }
        if ([string]::IsNullOrWhiteSpace($probeToken)) { throw "Prüftoken fehlt im Mission-Control-Link." }
        Confirm-Probe $config.server_url $config.agent_token $probeToken
        exit 0
    }
    $ticket = $null
    foreach ($pair in $uri.Query.TrimStart('?').Split('&')) {
        if ([string]::IsNullOrWhiteSpace($pair)) { continue }
        $parts = $pair -split '=', 2
        $name = [Uri]::UnescapeDataString($parts[0])
        if ($name -eq "ticket" -and $parts.Count -eq 2) {
            $ticket = [Uri]::UnescapeDataString($parts[1])
            break
        }
    }
    if ([string]::IsNullOrWhiteSpace($ticket)) { throw "Ticket fehlt im Mission-Control-Link." }

    $manifest = Get-Ticket $config.server_url $config.agent_token $ticket
    $source = Assert-PathInsideRoot $config.game_root $manifest.launcher
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Der Pfad ist über SMB nicht erreichbar:`n$source"
    }
    if ($manifest.action -ne "open_folder" -and -not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Die erwartete Quelldatei ist kein regulärer Datenträger bzw. Installer:`n$source"
    }

    $language = if ($manifest.ui_language -in @("en", "ru")) { $manifest.ui_language } else { "de" }
    $actionLabels = @{
        de = @{ direct_setup = "Direktes Setup"; iso = "ISO einbinden und installieren"; open_folder = "Ordner öffnen" }
        en = @{ direct_setup = "Direct setup"; iso = "Mount ISO and install"; open_folder = "Open folder" }
        ru = @{ direct_setup = "Прямая установка"; iso = "Подключить ISO и установить"; open_folder = "Открыть папку" }
    }
    $actionLabel = $actionLabels[$language][$manifest.action]
    if ([string]::IsNullOrWhiteSpace($actionLabel)) { $actionLabel = $manifest.action }
    if ($language -eq "en") {
        $message = "Title: $($manifest.title)`n`nAction: $actionLabel`nSource: $source`n`nContinue?"
        $confirmationTitle = "HypeTek Mission Control – Confirmation"
    }
    elseif ($language -eq "ru") {
        $message = "Название: $($manifest.title)`n`nДействие: $actionLabel`nИсточник: $source`n`nПродолжить?"
        $confirmationTitle = "HypeTek Mission Control – Подтверждение"
    }
    else {
        $message = "Titel: $($manifest.title)`n`nAktion: $actionLabel`nQuelle: $source`n`nFortfahren?"
        $confirmationTitle = "HypeTek Mission Control – Bestätigung"
    }
    $answer = [System.Windows.MessageBox]::Show(
        $message,
        $confirmationTitle,
        [System.Windows.MessageBoxButton]::YesNo,
        [System.Windows.MessageBoxImage]::Question
    )
    if ($answer -ne [System.Windows.MessageBoxResult]::Yes) { exit 0 }

    switch ($manifest.action) {
        "open_folder" {
            $folder = if (Test-Path -LiteralPath $source -PathType Container) {
                $source
            } else {
                [IO.Path]::GetDirectoryName($source)
            }
            Start-Process explorer.exe -ArgumentList @($folder)
        }
        "direct_setup" {
            Start-Process -FilePath $source -WorkingDirectory ([IO.Path]::GetDirectoryName($source))
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
            Start-Process -FilePath $installer -WorkingDirectory ([IO.Path]::GetDirectoryName($installer))
        }
        default { throw "Nicht unterstützte Aktion: $($manifest.action)" }
    }
}
catch {
    Show-Error $_.Exception.Message
    exit 1
}
