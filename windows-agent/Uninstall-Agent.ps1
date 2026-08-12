$ErrorActionPreference = "Stop"
Remove-Item -LiteralPath "Registry::HKEY_CURRENT_USER\Software\Classes\hypetek-gamevault" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $env:LOCALAPPDATA "HypeTek\GameVault") -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "HypeTek GameVault Agent entfernt." -ForegroundColor Green
