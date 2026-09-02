param(
    [string]$AgentPath = (Join-Path $PSScriptRoot "..\windows-agent\GameVaultAgent.ps1")
)

$ErrorActionPreference = "Stop"
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path -LiteralPath $AgentPath),
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count) { throw "Agent source did not parse." }

$functionAst = $ast.Find({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -eq "Convert-MappedDrivePathToUnc"
}, $true)
if (-not $functionAst) { throw "Convert-MappedDrivePathToUnc was not found." }

. ([ScriptBlock]::Create($functionAst.Extent.Text))

function Get-SmbMapping {
    param([string]$LocalPath)
    if ($LocalPath -ieq "Z:") {
        return [PSCustomObject]@{ RemotePath = "\\truenas\Game" }
    }
    return $null
}

$specialPath = "Z:\Age of Empires II - Definitive Edition [FitGirl Repack]\setup.exe"
$resolved = Convert-MappedDrivePathToUnc $specialPath
$expected = "\\truenas\Game\Age of Empires II - Definitive Edition [FitGirl Repack]\setup.exe"
if ($resolved -cne $expected) {
    throw "Mapped path was not resolved literally. Expected '$expected', got '$resolved'."
}

$uncPath = "\\server\share\Apostrophe's Game [2026]\setup.exe"
if ((Convert-MappedDrivePathToUnc $uncPath) -cne $uncPath) {
    throw "An existing UNC path must remain unchanged."
}

Write-Host "Agent mapped-drive path resolution passed."
