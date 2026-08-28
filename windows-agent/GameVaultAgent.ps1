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

$AgentLanguage = "auto"

function Resolve-AgentLanguage([string]$Language) {
    if ([string]::IsNullOrWhiteSpace($Language) -or $Language -eq "auto") {
        $Language = [Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName
    }
    if ($Language -eq "zh-CN" -or $Language -eq "zh-Hans") { $Language = "zh" }
    if ($Language -notin @("de", "en", "ru", "it", "fr", "es", "pt", "pl", "nl", "tr", "ar", "zh", "tlh", "sjn")) { return "en" }
    return $Language
}

function Set-AgentLanguage([string]$Language) {
    $script:AgentLanguage = Resolve-AgentLanguage $Language
}

function Get-AgentCopy([string]$Key, [object[]]$Values = @()) {
    $copy = @{
        en = @{ picker="Select a Windows or SMB folder for the Mission Control library"; mappingCaption="Map library"; mapping="Mission Control wants to map the library '{0}' on this PC:`n`n{1}`n`nUse this reachable path and save it locally?"; missingPath="The local library path for '{0}' is not reachable on this Windows PC: {1}"; noMapping="No confirmed path is configured for library '{0}' on this Windows PC. Check the drive and try again."; sourceMissing="The path is not reachable:`n{0}"; sourceInvalid="The expected source is not a regular disk image or installer:`n{0}"; isoDrive="The ISO was mounted, but no drive letter was detected."; isoInstaller="The ISO was mounted, but no unambiguous installer was found. The drive was opened."; unsupported="Unsupported action: {0}" }
        de = @{ picker="Windows- oder SMB-Ordner für die Mission-Control-Bibliothek auswählen"; mappingCaption="Bibliothek zuordnen"; mapping="Mission Control möchte die Bibliothek '{0}' auf diesem PC zuordnen:`n`n{1}`n`nDiesen erreichbaren Pfad verwenden und lokal speichern?"; missingPath="Der lokale Bibliothekspfad für '{0}' ist auf diesem Windows-PC nicht erreichbar: {1}"; noMapping="Für die Bibliothek '{0}' ist auf diesem Windows-PC kein bestätigter Pfad eingerichtet. Laufwerk prüfen und erneut versuchen."; sourceMissing="Der Pfad ist nicht erreichbar:`n{0}"; sourceInvalid="Die erwartete Quelldatei ist kein regulärer Datenträger bzw. Installer:`n{0}"; isoDrive="Das ISO wurde eingebunden, aber kein Laufwerksbuchstabe erkannt."; isoInstaller="ISO eingebunden, aber kein eindeutiger Installer erkannt. Das Laufwerk wurde geöffnet."; unsupported="Nicht unterstützte Aktion: {0}" }
        ru = @{ picker="Выберите папку Windows или SMB для библиотеки Mission Control"; mappingCaption="Подключение библиотеки"; mapping="Mission Control хочет подключить библиотеку '{0}' на этом ПК:`n`n{1}`n`nИспользовать этот доступный путь и сохранить его?"; missingPath="Локальный путь библиотеки '{0}' недоступен на этом ПК: {1}"; noMapping="Для библиотеки '{0}' нет подтверждённого пути. Проверьте диск и повторите попытку."; sourceMissing="Путь недоступен:`n{0}"; sourceInvalid="Источник не является допустимым образом диска или установщиком:`n{0}"; isoDrive="ISO подключён, но буква диска не обнаружена."; isoInstaller="ISO подключён, но установщик не найден. Диск открыт."; unsupported="Неподдерживаемое действие: {0}" }
        it = @{ picker="Seleziona una cartella Windows o SMB per la libreria Mission Control"; mappingCaption="Associa libreria"; mapping="Mission Control vuole associare la libreria '{0}' a questo PC:`n`n{1}`n`nUsare questo percorso raggiungibile e salvarlo?"; missingPath="Il percorso locale della libreria '{0}' non è raggiungibile: {1}"; noMapping="Nessun percorso confermato per la libreria '{0}'. Controlla l'unità e riprova."; sourceMissing="Il percorso non è raggiungibile:`n{0}"; sourceInvalid="La sorgente non è un'immagine disco o un installer valido:`n{0}"; isoDrive="ISO montata, ma nessuna lettera di unità rilevata."; isoInstaller="ISO montata, ma nessun installer univoco trovato. L'unità è stata aperta."; unsupported="Azione non supportata: {0}" }
        fr = @{ picker="Sélectionnez un dossier Windows ou SMB pour la bibliothèque Mission Control"; mappingCaption="Associer la bibliothèque"; mapping="Mission Control veut associer la bibliothèque '{0}' à ce PC :`n`n{1}`n`nUtiliser ce chemin accessible et l'enregistrer ?"; missingPath="Le chemin local de la bibliothèque '{0}' est inaccessible : {1}"; noMapping="Aucun chemin confirmé pour la bibliothèque '{0}'. Vérifiez le lecteur et réessayez."; sourceMissing="Le chemin est inaccessible :`n{0}"; sourceInvalid="La source n'est pas une image disque ou un installateur valide :`n{0}"; isoDrive="L’ISO est montée, mais aucune lettre de lecteur n’a été détectée."; isoInstaller="L’ISO est montée, mais aucun installateur unique n’a été trouvé. Le lecteur a été ouvert."; unsupported="Action non prise en charge : {0}" }
        es = @{ picker="Selecciona una carpeta Windows o SMB para la biblioteca de Mission Control"; mappingCaption="Asignar biblioteca"; mapping="Mission Control quiere asignar la biblioteca '{0}' a este PC:`n`n{1}`n`n¿Usar esta ruta accesible y guardarla?"; missingPath="La ruta local de la biblioteca '{0}' no está accesible: {1}"; noMapping="No hay una ruta confirmada para la biblioteca '{0}'. Comprueba la unidad e inténtalo de nuevo."; sourceMissing="La ruta no está accesible:`n{0}"; sourceInvalid="El origen no es una imagen de disco ni un instalador válido:`n{0}"; isoDrive="La ISO se montó, pero no se detectó una letra de unidad."; isoInstaller="La ISO se montó, pero no se encontró un instalador inequívoco. Se abrió la unidad."; unsupported="Acción no compatible: {0}" }
        pt = @{ picker="Selecione uma pasta Windows ou SMB para a biblioteca Mission Control"; mappingCaption="Associar biblioteca"; mapping="O Mission Control pretende associar a biblioteca '{0}' a este PC:`n`n{1}`n`nUsar este caminho acessível e guardá-lo?"; missingPath="O caminho local da biblioteca '{0}' não está acessível: {1}"; noMapping="Não existe caminho confirmado para a biblioteca '{0}'. Verifique a unidade e tente novamente."; sourceMissing="O caminho não está acessível:`n{0}"; sourceInvalid="A origem não é uma imagem de disco nem um instalador válido:`n{0}"; isoDrive="A ISO foi montada, mas não foi detetada uma letra de unidade."; isoInstaller="A ISO foi montada, mas não foi encontrado um instalador inequívoco. A unidade foi aberta."; unsupported="Ação não suportada: {0}" }
        pl = @{ picker="Wybierz folder Windows lub SMB dla biblioteki Mission Control"; mappingCaption="Mapowanie biblioteki"; mapping="Mission Control chce zmapować bibliotekę '{0}' na tym komputerze:`n`n{1}`n`nUżyć tej dostępnej ścieżki i zapisać ją?"; missingPath="Lokalna ścieżka biblioteki '{0}' jest niedostępna: {1}"; noMapping="Brak potwierdzonej ścieżki dla biblioteki '{0}'. Sprawdź dysk i spróbuj ponownie."; sourceMissing="Ścieżka jest niedostępna:`n{0}"; sourceInvalid="Źródło nie jest prawidłowym obrazem dysku ani instalatorem:`n{0}"; isoDrive="ISO zamontowano, ale nie wykryto litery dysku."; isoInstaller="ISO zamontowano, ale nie znaleziono jednoznacznego instalatora. Dysk został otwarty."; unsupported="Nieobsługiwana akcja: {0}" }
        nl = @{ picker="Selecteer een Windows- of SMB-map voor de Mission Control-bibliotheek"; mappingCaption="Bibliotheek koppelen"; mapping="Mission Control wil bibliotheek '{0}' aan deze pc koppelen:`n`n{1}`n`nDit bereikbare pad gebruiken en lokaal opslaan?"; missingPath="Het lokale pad van bibliotheek '{0}' is niet bereikbaar: {1}"; noMapping="Er is geen bevestigd pad voor bibliotheek '{0}'. Controleer het station en probeer opnieuw."; sourceMissing="Het pad is niet bereikbaar:`n{0}"; sourceInvalid="De bron is geen geldige schijfkopie of installer:`n{0}"; isoDrive="De ISO is gekoppeld, maar er is geen stationsletter gevonden."; isoInstaller="De ISO is gekoppeld, maar er is geen eenduidige installer gevonden. Het station is geopend."; unsupported="Niet-ondersteunde actie: {0}" }
        tr = @{ picker="Mission Control kitaplığı için Windows veya SMB klasörü seçin"; mappingCaption="Kitaplığı eşle"; mapping="Mission Control '{0}' kitaplığını bu bilgisayara eşlemek istiyor:`n`n{1}`n`nBu erişilebilir yol kullanılıp kaydedilsin mi?"; missingPath="'{0}' kitaplığının yerel yolu erişilebilir değil: {1}"; noMapping="'{0}' kitaplığı için onaylanmış yol yok. Sürücüyü kontrol edip yeniden deneyin."; sourceMissing="Yola erişilemiyor:`n{0}"; sourceInvalid="Kaynak geçerli bir disk kalıbı veya kurucu değil:`n{0}"; isoDrive="ISO bağlandı ancak sürücü harfi algılanmadı."; isoInstaller="ISO bağlandı ancak belirgin bir kurucu bulunamadı. Sürücü açıldı."; unsupported="Desteklenmeyen eylem: {0}" }
        ar = @{ picker="حدد مجلد Windows أو SMB لمكتبة Mission Control"; mappingCaption="ربط المكتبة"; mapping="يريد Mission Control ربط المكتبة '{0}' بهذا الكمبيوتر:`n`n{1}`n`nهل تريد استخدام هذا المسار المتاح وحفظه محليًا؟"; missingPath="مسار المكتبة المحلية '{0}' غير متاح على جهاز Windows هذا: {1}"; noMapping="لا يوجد مسار مؤكد للمكتبة '{0}' على هذا الكمبيوتر. تحقق من محرك الأقراص وحاول مجددًا."; sourceMissing="المسار غير متاح:`n{0}"; sourceInvalid="المصدر المتوقع ليس صورة قرص أو برنامج تثبيت صالحًا:`n{0}"; isoDrive="تم تركيب ISO ولكن لم يتم العثور على حرف محرك أقراص."; isoInstaller="تم تركيب ISO، لكن لم يتم العثور على برنامج تثبيت واضح. تم فتح محرك الأقراص."; unsupported="إجراء غير مدعوم: {0}" }
        zh = @{ picker="为 Mission Control 游戏库选择 Windows 或 SMB 文件夹"; mappingCaption="映射游戏库"; mapping="Mission Control 希望将游戏库「{0}」映射到此电脑：`n`n{1}`n`n是否使用此可访问路径并保存到本机？"; missingPath="本地游戏库「{0}」的路径在此 Windows 电脑上不可访问：{1}"; noMapping="此电脑尚未为游戏库「{0}」配置确认路径。请检查驱动器后重试。"; sourceMissing="路径不可访问：`n{0}"; sourceInvalid="预期的源文件不是有效的磁盘映像或安装程序：`n{0}"; isoDrive="ISO 已挂载，但未检测到驱动器号。"; isoInstaller="ISO 已挂载，但未找到明确的安装程序。驱动器已打开。"; unsupported="不支持的操作：{0}" }
        tlh = @{ picker="Mission Control tameyvaD Windows pagh SMB ngaSwi' yIwIv"; mappingCaption="tamey rar"; mapping="Mission Control tamey '{0}' De'wI'vamDaq rar neH:`n`n{1}`n`nHe'vam lo'lu' 'ej polmeH DaneH'a'?"; missingPath="tamey '{0}' He' De'wI'vamDaq pawbe': {1}"; noMapping="tamey '{0}'vaD He' 'ollu'be'. QuQ yInuD 'ej yInIDqa'."; sourceMissing="He' pawlu'be':`n{0}"; sourceInvalid="Doch pIHlu'bogh disk image installer ghap 'oHbe':`n{0}"; isoDrive="ISO rar, 'ach QuQ Degh tu'be'."; isoInstaller="ISO rar, 'ach installer leghlu'be'. QuQ poSmoHlu'."; unsupported="vangmeH mIw Qutlhbe': {0}" }
        sjn = @{ picker="Cilio han Windows egor SMB an i cherdir Mission Control"; mappingCaption="Nautha cherdir"; mapping="Mission Control aníra nautha i cherdir '{0}' na i venn hen:`n`n{1}`n`nMaetha i râd hen a hebin hain?"; missingPath="I râd an i cherdir '{0}' ú-dhanna na i Windows hen: {1}"; noMapping="Ú-chebin râd thand an i cherdir '{0}'. Tirio i rant a caro ad."; sourceMissing="I râd ú-dhanna:`n{0}"; sourceInvalid="I ôn ú-chenir ant dîn disk egor installer:`n{0}"; isoDrive="I ISO nauthant, ach ú-chennir tengw i rant."; isoInstaller="I ISO nauthant, ach ú-chennir installer. I rant edrochant."; unsupported="Carad ú-vrestannen: {0}" }
    }
    $languageCopy = $copy[(Resolve-AgentLanguage $script:AgentLanguage)]
    if (-not $languageCopy -or -not $languageCopy.ContainsKey($Key)) { $languageCopy = $copy.en }
    $value = [string]$languageCopy[$Key]
    if ($Values.Count -gt 0) { return [string]::Format($value, $Values) }
    return $value
}

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
    $message = Get-AgentCopy "mapping" @($LibraryName, $SuggestedPath)
    $answer = [System.Windows.MessageBox]::Show(
        $message,
        "HypeTek Mission Control – $(Get-AgentCopy 'mappingCaption')",
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

function Get-FolderPickerManifest([string]$ServerUrl, [string]$AgentToken, [string]$Token) {
    Invoke-RestMethod -Method Get `
        -Uri "$($ServerUrl.TrimEnd('/'))/api/agent/folder-pickers/$([Uri]::EscapeDataString($Token))/manifest" `
        -Headers @{ Authorization = "Bearer $AgentToken" } `
        -TimeoutSec 15
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

function Get-GameTitleQuality([string]$Title, [bool]$IsFolder) {
    $normalized = ($Title.ToLowerInvariant() -replace '[^a-z0-9]+', '')
    if ([string]::IsNullOrWhiteSpace($normalized)) { return -1000 }
    if ($normalized -in @('game', 'setup', 'install', 'installer', 'autorun', 'disc', 'disk', 'dvd', 'image')) { return -120 }
    if ($normalized -match '^(?:cd|disc|disk|dvd)\d+$') { return -120 }
    $words = @([regex]::Matches($Title, '[\p{L}\p{N}_]+'))
    $score = [Math]::Min($Title.Length, 40)
    if ($words.Count -ge 2) { $score += 42 + [Math]::Min($words.Count, 5) * 3 }
    if ($Title -cmatch '[a-z]' -and $Title -cmatch '[A-Z]') { $score += 12 }
    if ($Title -match "[-'’:]" ) { $score += 5 }
    if ($IsFolder) { $score += 5 }
    if ($words.Count -eq 1 -and $Title -cmatch '^[^a-z]*$' -and $normalized.Length -ge 5) { $score -= 38 }
    return $score
}

function Get-BestGameTitle($Entry, [object[]]$Files) {
    $folderTitle = Get-CleanGameTitle $Entry.Name
    $bestTitle = $folderTitle
    $bestScore = Get-GameTitleQuality $folderTitle $true
    foreach ($file in @($Files)) {
        if ($file.Extension -notin @('.iso', '.exe', '.msi')) { continue }
        $title = Get-CleanGameTitle $file.Name
        $relative = $file.FullName.Substring($Entry.FullName.Length).TrimStart('\')
        $depth = [Math]::Max(0, @($relative.Split('\')).Count - 1)
        $score = (Get-GameTitleQuality $title $false) - [Math]::Min($depth, 8) * 3
        if ($score -gt $bestScore -or ($score -eq $bestScore -and $title.Length -gt $bestTitle.Length)) {
            $bestTitle = $title
            $bestScore = $score
        }
    }
    return $bestTitle
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
                title = Get-BestGameTitle $entry $files
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
    Set-AgentLanguage ([string]$config.installer_language)
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
        $pickerManifest = Get-FolderPickerManifest $config.server_url $config.agent_token $pickerToken
        Set-AgentLanguage ([string]$pickerManifest.ui_language)
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = Get-AgentCopy "picker"
        $dialog.ShowNewFolderButton = $false
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Complete-FolderPicker $config.server_url $config.agent_token $pickerToken $dialog.SelectedPath $false
        } else {
            Complete-FolderPicker $config.server_url $config.agent_token $pickerToken "" $true
        }
        exit 0
    }
    if ($uri.Host -eq "scan") {
        $scanTokens = New-Object System.Collections.Generic.List[string]
        foreach ($pair in $uri.Query.TrimStart('?').Split('&')) {
            if ([string]::IsNullOrWhiteSpace($pair)) { continue }
            $parts = $pair -split '=', 2
            $parameterName = [Uri]::UnescapeDataString($parts[0])
            if ($parameterName -in @("token", "tokens") -and $parts.Count -eq 2) {
                foreach ($tokenValue in ([Uri]::UnescapeDataString($parts[1]) -split ',')) {
                    if (-not [string]::IsNullOrWhiteSpace($tokenValue)) { $scanTokens.Add($tokenValue) }
                }
            }
        }
        if ($scanTokens.Count -eq 0) { throw "Scan-Token fehlt im Mission-Control-Link." }
        $scanErrors = New-Object System.Collections.Generic.List[string]
        foreach ($scanToken in $scanTokens) {
            $ActiveScanToken = $scanToken
            $ActiveScanConfig = $config
            try {
                Start-AgentScan $config.server_url $config.agent_token $scanToken
                $scanManifest = Get-ScanManifest $config.server_url $config.agent_token $scanToken
                Set-AgentLanguage ([string]$scanManifest.ui_language)
                $libraryId = [string]$scanManifest.library_id
                # The path stored with the current server library is authoritative for
                # scans. This prevents an older agent mapping from silently scanning the
                # previous folder after the user edits the library path in Settings.
                $scanRoot = [string]$scanManifest.windows_path_hint
                if ([string]::IsNullOrWhiteSpace($scanRoot) -or -not (Test-Path -LiteralPath $scanRoot -PathType Container)) {
                    throw (Get-AgentCopy "missingPath" @([string]$scanManifest.library_name, $scanRoot))
                }
                if (-not $config.libraries) {
                    $config | Add-Member -NotePropertyName libraries -NotePropertyValue ([PSCustomObject]@{}) -Force
                }
                $config.libraries | Add-Member -NotePropertyName $libraryId -NotePropertyValue $scanRoot -Force
                Save-AgentConfig $config
                $scanResults = Get-LocalLibraryResults $scanRoot @($scanManifest.scan_exclusions)
                Complete-AgentScan $config.server_url $config.agent_token $scanToken $scanResults
                $ActiveScanToken = $null
            }
            catch {
                $scanMessage = $_.Exception.Message
                try { Fail-AgentScan $config.server_url $config.agent_token $scanToken $scanMessage } catch { }
                $scanErrors.Add($scanMessage)
                $ActiveScanToken = $null
            }
        }
        $ActiveScanToken = $null
        if ($scanErrors.Count -gt 0) {
            Show-Error ($scanErrors -join "`n`n")
            exit 1
        }
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
    Set-AgentLanguage ([string]$manifest.ui_language)
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
        throw (Get-AgentCopy "noMapping" @($libraryId))
    }
    $source = Assert-PathInsideRoot $gameRoot $manifest.launcher
    if (-not (Test-Path -LiteralPath $source)) {
        throw (Get-AgentCopy "sourceMissing" @($source))
    }
    if ($manifest.action -ne "open_folder" -and -not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw (Get-AgentCopy "sourceInvalid" @($source))
    }

    $language = Resolve-AgentLanguage ([string]$manifest.ui_language)
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
        ar = @{ direct_setup = "تثبيت مباشر"; iso = "تركيب ISO والتثبيت"; open_folder = "فتح المجلد" }
        zh = @{ direct_setup = "直接安装"; iso = "挂载 ISO 并安装"; open_folder = "打开文件夹" }
        tlh = @{ direct_setup = "installer yIchu'"; iso = "ISO yIrar 'ej yIjom"; open_folder = "ngaSwi' yIpoSmoH" }
        sjn = @{ direct_setup = "Pada ben"; iso = "Nautha ISO a bado"; open_folder = "Edro i cherdir" }
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
        ar = @{ title = "العنوان"; action = "الإجراء"; source = "المصدر"; question = "هل تريد المتابعة؟"; caption = "تأكيد" }
        zh = @{ title = "标题"; action = "操作"; source = "来源"; question = "是否继续？"; caption = "确认" }
        tlh = @{ title = "pong"; action = "vangmeH mIw"; source = "Doch"; question = "taH'a'?"; caption = "'ol" }
        sjn = @{ title = "Eneth"; action = "Carad"; source = "Ôn"; question = "Maetho?"; caption = "Tanc" }
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
            if (-not $volume) { throw (Get-AgentCopy "isoDrive") }
            $installer = Find-InstallerOnMountedIso $volume.DriveLetter
            if (-not $installer) {
                Start-Process explorer.exe "$($volume.DriveLetter):\"
                throw (Get-AgentCopy "isoInstaller")
            }
            Start-Process -FilePath $installer -WorkingDirectory ([IO.Path]::GetDirectoryName($installer))
        }
        default { throw (Get-AgentCopy "unsupported" @([string]$manifest.action)) }
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
