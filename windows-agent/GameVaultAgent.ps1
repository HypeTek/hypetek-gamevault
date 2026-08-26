param(
    [Parameter(Position = 0)]
    [string]$ProtocolUrl
)

$ErrorActionPreference = "Stop"
$ActiveScanToken = $null
$ActiveScanConfig = $null
$ConfigPath = Join-Path $env:LOCALAPPDATA "HypeTek\MissionControl\agent.json"
$LegacyConfigPath = Join-Path $env:LOCALAPPDATA "HypeTek\GameVault\agent.json"
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf) -and (Test-Path -LiteralPath $LegacyConfigPath -PathType Leaf)) {
    $ConfigPath = $LegacyConfigPath
}

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

function Show-Error([string]$Message) {
    [System.Windows.MessageBox]::Show(
        $Message,
        "HypeTek Mission Control",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
}

function Save-AgentConfig($Config) {
    $json = $Config | ConvertTo-Json -Depth 8
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($ConfigPath, $json + [Environment]::NewLine, $utf8WithoutBom)
}

function Confirm-LibraryMapping($Config, [string]$LibraryId, [string]$LibraryName, [string]$SuggestedPath) {
    if ([string]::IsNullOrWhiteSpace($SuggestedPath) -or -not (Test-Path -LiteralPath $SuggestedPath -PathType Container)) {
        return $null
    }
    $message = "Mission Control möchte die Bibliothek '$LibraryName' auf diesem PC zuordnen:`n`n$SuggestedPath`n`nDiesen erreichbaren Pfad verwenden und lokal speichern?"
    $answer = [System.Windows.MessageBox]::Show(
        $message,
        "HypeTek Mission Control – Bibliothek zuordnen",
        [System.Windows.MessageBoxButton]::YesNo,
        [System.Windows.MessageBoxImage]::Question
    )
    if ($answer -ne [System.Windows.MessageBoxResult]::Yes) { return $null }
    if (-not $Config.libraries) {
        $Config | Add-Member -NotePropertyName libraries -NotePropertyValue ([PSCustomObject]@{}) -Force
    }
    $Config.libraries | Add-Member -NotePropertyName $LibraryId -NotePropertyValue $SuggestedPath -Force
    Save-AgentConfig $Config
    return $SuggestedPath
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

function Complete-FolderPicker([string]$ServerUrl, [string]$AgentToken, [string]$Token, [string]$SelectedPath, [bool]$Cancelled) {
    $headers = @{ Authorization = "Bearer $AgentToken" }
    $body = @{ selected_path = $SelectedPath; cancelled = $Cancelled } | ConvertTo-Json -Compress
    Invoke-RestMethod -Method Post `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/folder-pickers/$([Uri]::EscapeDataString($Token))/complete" `
        -Headers $headers `
        -ContentType "application/json; charset=utf-8" `
        -Body $body `
        -TimeoutSec 15 | Out-Null
}

function Get-ScanManifest([string]$ServerUrl, [string]$AgentToken, [string]$Token) {
    Invoke-RestMethod -Method Get `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/scans/$([Uri]::EscapeDataString($Token))" `
        -Headers @{ Authorization = "Bearer $AgentToken" } `
        -TimeoutSec 30
}

function Start-AgentScan([string]$ServerUrl, [string]$AgentToken, [string]$Token) {
    Invoke-RestMethod -Method Post `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/scans/$([Uri]::EscapeDataString($Token))/start" `
        -Headers @{ Authorization = "Bearer $AgentToken" } `
        -TimeoutSec 15 | Out-Null
}

function Complete-AgentScan([string]$ServerUrl, [string]$AgentToken, [string]$Token, $Results) {
    $body = @{ results = @($Results) } | ConvertTo-Json -Depth 8 -Compress
    Invoke-RestMethod -Method Post `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/scans/$([Uri]::EscapeDataString($Token))/complete" `
        -Headers @{ Authorization = "Bearer $AgentToken" } `
        -ContentType "application/json; charset=utf-8" `
        -Body $body `
        -TimeoutSec 900 | Out-Null
}

function Fail-AgentScan([string]$ServerUrl, [string]$AgentToken, [string]$Token, [string]$Message) {
    $body = @{ error = $Message } | ConvertTo-Json -Compress
    Invoke-RestMethod -Method Post `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/scans/$([Uri]::EscapeDataString($Token))/fail" `
        -Headers @{ Authorization = "Bearer $AgentToken" } `
        -ContentType "application/json; charset=utf-8" `
        -Body $body `
        -TimeoutSec 15 | Out-Null
}

function Get-CleanGameTitle([string]$Name) {
    $title = [IO.Path]::GetFileNameWithoutExtension($Name)
    $title = $title -replace '(?i)\s*\[(?:fitgirl(?: repack)?|repack)\]\s*', ' '
    $title = $title -replace '(?i)\s*--[_ ]*fitgirl-repacks(?:\.site)?[_ ]*--\s*', ' '
    $title = ($title -replace '[._]+', ' ' -replace '\s+', ' ').Trim(' ', '-', '_')
    if ([string]::IsNullOrWhiteSpace($title)) { return $Name }
    return $title
}

function Get-LocalLibraryResults([string]$Root, [string[]]$ExcludedNames) {
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $excluded = @{}
    foreach ($name in @($ExcludedNames)) { if ($name) { $excluded[[string]$name.ToLowerInvariant()] = $true } }
    $results = New-Object System.Collections.Generic.List[object]
    foreach ($entry in Get-ChildItem -LiteralPath $Root -Force -ErrorAction SilentlyContinue | Sort-Object Name) {
        if ($excluded.ContainsKey($entry.Name.ToLowerInvariant())) { continue }
        try {
            $files = if ($entry.PSIsContainer) {
                @(Get-ChildItem -LiteralPath $entry.FullName -File -Recurse -Force -ErrorAction SilentlyContinue)
            } else { @($entry) }
            $installer = $files | Where-Object { $_.Name -match '(?i)^(setup(?:[-_. ].*)?|install(?:er)?(?:[-_. ].*)?|autorun)\.exe$' } | Sort-Object @{Expression={$_.FullName.Split('\').Count}}, FullName | Select-Object -First 1
            $iso = $files | Where-Object { $_.Extension -ieq '.iso' } | Sort-Object FullName | Select-Object -First 1
            $type = 'manual'; $launcher = $null; $note = 'Keine sichere Installationsaktion erkannt'
            if ($installer) { $type = 'direct_setup'; $launcher = $installer; $note = 'Setup-Programm vom Windows-Agent erkannt' }
            elseif ($iso) { $type = 'iso'; $launcher = $iso; $note = 'ISO-Abbild vom Windows-Agent erkannt' }
            $relative = $entry.FullName.Substring($rootFull.Length).Replace('\', '/')
            $launcherRelative = if ($launcher) { $launcher.FullName.Substring($rootFull.Length).Replace('\', '/') } else { $null }
            $size = [Int64]0
            foreach ($file in $files) { $size += [Int64]$file.Length }
            $results.Add([PSCustomObject]@{
                relative_path = $relative
                title = Get-CleanGameTitle $entry.Name
                detected_type = $type
                launcher_relative_path = $launcherRelative
                file_count = $files.Count
                logical_size = $size
                detection_note = $note
            })
        } catch { continue }
    }
    return $results
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
    foreach ($required in @("server_url", "agent_token")) {
        if ([string]::IsNullOrWhiteSpace($config.$required)) { throw "Konfigurationswert fehlt: $required" }
    }
    if (-not $config.libraries -and [string]::IsNullOrWhiteSpace($config.game_root)) {
        throw "Konfigurationswert fehlt: libraries"
    }
    if ([string]::IsNullOrWhiteSpace($ProtocolUrl)) { throw "Kein Mission-Control-Auftrag empfangen." }
    $uri = [Uri]$ProtocolUrl
    if ($uri.Scheme -ne "hypetek-gamevault" -or $uri.Host -notin @("launch", "probe", "browse", "scan")) {
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
    if ($uri.Host -eq "browse") {
        $pickerToken = $null
        foreach ($pair in $uri.Query.TrimStart('?').Split('&')) {
            if ([string]::IsNullOrWhiteSpace($pair)) { continue }
            $parts = $pair -split '=', 2
            if ([Uri]::UnescapeDataString($parts[0]) -eq "token" -and $parts.Count -eq 2) {
                $pickerToken = [Uri]::UnescapeDataString($parts[1])
                break
            }
        }
        if ([string]::IsNullOrWhiteSpace($pickerToken)) { throw "Auswahltoken fehlt im Mission-Control-Link." }
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "Windows- oder SMB-Ordner für die Mission-Control-Bibliothek auswählen"
        $dialog.ShowNewFolderButton = $false
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Complete-FolderPicker $config.server_url $config.agent_token $pickerToken $dialog.SelectedPath $false
        } else {
            Complete-FolderPicker $config.server_url $config.agent_token $pickerToken "" $true
        }
        exit 0
    }
    if ($uri.Host -eq "scan") {
        $scanToken = $null
        foreach ($pair in $uri.Query.TrimStart('?').Split('&')) {
            if ([string]::IsNullOrWhiteSpace($pair)) { continue }
            $parts = $pair -split '=', 2
            if ([Uri]::UnescapeDataString($parts[0]) -eq "token" -and $parts.Count -eq 2) {
                $scanToken = [Uri]::UnescapeDataString($parts[1]); break
            }
        }
        if ([string]::IsNullOrWhiteSpace($scanToken)) { throw "Scan-Token fehlt im Mission-Control-Link." }
        $ActiveScanToken = $scanToken
        $ActiveScanConfig = $config
        Start-AgentScan $config.server_url $config.agent_token $scanToken
        $scanManifest = Get-ScanManifest $config.server_url $config.agent_token $scanToken
        $libraryId = [string]$scanManifest.library_id
        $scanRoot = $null
        if ($config.libraries) {
            $mapping = $config.libraries.PSObject.Properties[$libraryId]
            if ($mapping) { $scanRoot = [string]$mapping.Value }
        }
        if ([string]::IsNullOrWhiteSpace($scanRoot)) {
            $scanRoot = Confirm-LibraryMapping $config $libraryId ([string]$scanManifest.library_name) ([string]$scanManifest.windows_path_hint)
        }
        if ([string]::IsNullOrWhiteSpace($scanRoot) -or -not (Test-Path -LiteralPath $scanRoot -PathType Container)) {
            throw "Der lokale Bibliothekspfad ist auf diesem Windows-PC nicht erreichbar."
        }
        $scanResults = Get-LocalLibraryResults $scanRoot @($scanManifest.scan_exclusions)
        Complete-AgentScan $config.server_url $config.agent_token $scanToken $scanResults
        $ActiveScanToken = $null
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
    $libraryId = if ([string]::IsNullOrWhiteSpace([string]$manifest.library_id)) { "primary" } else { [string]$manifest.library_id }
    $gameRoot = $null
    if ($config.libraries) {
        $mapping = $config.libraries.PSObject.Properties[$libraryId]
        if ($mapping) { $gameRoot = [string]$mapping.Value }
    }
    if ([string]::IsNullOrWhiteSpace($gameRoot) -and $libraryId -eq "primary") {
        $gameRoot = [string]$config.game_root
    }
    if ([string]::IsNullOrWhiteSpace($gameRoot)) {
        $gameRoot = Confirm-LibraryMapping $config $libraryId ([string]$manifest.library_name) ([string]$manifest.windows_path_hint)
    }
    if ([string]::IsNullOrWhiteSpace($gameRoot)) {
        throw "Für die Bibliothek '$libraryId' ist auf diesem Windows-PC kein bestätigter Pfad eingerichtet. Prüfe das SMB-Laufwerk und starte die Aktion erneut."
    }
    $source = Assert-PathInsideRoot $gameRoot $manifest.launcher
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Der Pfad ist über SMB nicht erreichbar:`n$source"
    }
    if ($manifest.action -ne "open_folder" -and -not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Die erwartete Quelldatei ist kein regulärer Datenträger bzw. Installer:`n$source"
    }

    $language = [string]$manifest.ui_language
    if ($language -eq "auto") {
        $language = [Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName
    }
    if ($language -notin @("de", "en", "ru", "it", "fr", "es", "pt", "pl", "nl", "tr")) { $language = "en" }
    $actionLabels = @{
        de = @{ direct_setup = "Direktes Setup"; iso = "ISO einbinden und installieren"; open_folder = "Ordner öffnen" }
        en = @{ direct_setup = "Direct setup"; iso = "Mount ISO and install"; open_folder = "Open folder" }
        ru = @{ direct_setup = "Прямая установка"; iso = "Подключить ISO и установить"; open_folder = "Открыть папку" }
        it = @{ direct_setup = "Installazione diretta"; iso = "Monta ISO e installa"; open_folder = "Apri cartella" }
        fr = @{ direct_setup = "Installation directe"; iso = "Monter l’ISO et installer"; open_folder = "Ouvrir le dossier" }
        es = @{ direct_setup = "Instalación directa"; iso = "Montar ISO e instalar"; open_folder = "Abrir carpeta" }
        pt = @{ direct_setup = "Instalação direta"; iso = "Montar ISO e instalar"; open_folder = "Abrir pasta" }
        pl = @{ direct_setup = "Instalacja bezpośrednia"; iso = "Zamontuj ISO i zainstaluj"; open_folder = "Otwórz folder" }
        nl = @{ direct_setup = "Directe installatie"; iso = "ISO koppelen en installeren"; open_folder = "Map openen" }
        tr = @{ direct_setup = "Doğrudan kurulum"; iso = "ISO bağla ve kur"; open_folder = "Klasörü aç" }
    }
    $actionLabel = $actionLabels[$language][$manifest.action]
    if ([string]::IsNullOrWhiteSpace($actionLabel)) { $actionLabel = $manifest.action }
    $dialogText = @{
        de = @{ title = "Titel"; action = "Aktion"; source = "Quelle"; question = "Fortfahren?"; caption = "Bestätigung" }
        en = @{ title = "Title"; action = "Action"; source = "Source"; question = "Continue?"; caption = "Confirmation" }
        ru = @{ title = "Название"; action = "Действие"; source = "Источник"; question = "Продолжить?"; caption = "Подтверждение" }
        it = @{ title = "Titolo"; action = "Azione"; source = "Origine"; question = "Continuare?"; caption = "Conferma" }
        fr = @{ title = "Titre"; action = "Action"; source = "Source"; question = "Continuer ?"; caption = "Confirmation" }
        es = @{ title = "Título"; action = "Acción"; source = "Origen"; question = "¿Continuar?"; caption = "Confirmación" }
        pt = @{ title = "Título"; action = "Ação"; source = "Origem"; question = "Continuar?"; caption = "Confirmação" }
        pl = @{ title = "Tytuł"; action = "Akcja"; source = "Źródło"; question = "Kontynuować?"; caption = "Potwierdzenie" }
        nl = @{ title = "Titel"; action = "Actie"; source = "Bron"; question = "Doorgaan?"; caption = "Bevestiging" }
        tr = @{ title = "Başlık"; action = "Eylem"; source = "Kaynak"; question = "Devam edilsin mi?"; caption = "Onay" }
    }
    $copy = $dialogText[$language]
    $message = "$($copy.title): $($manifest.title)`n`n$($copy.action): $actionLabel`n$($copy.source): $source`n`n$($copy.question)"
    $confirmationTitle = "HypeTek Mission Control – $($copy.caption)"
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
    $failureMessage = $_.Exception.Message
    if ($ActiveScanToken -and $ActiveScanConfig) {
        try { Fail-AgentScan $ActiveScanConfig.server_url $ActiveScanConfig.agent_token $ActiveScanToken $failureMessage } catch { }
    }
    Show-Error $failureMessage
    exit 1
}
