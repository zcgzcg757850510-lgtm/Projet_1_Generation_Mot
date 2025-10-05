param(
    [string]$RepoUrl = "https://github.com/skishore/makemeahanzi.git"
)
$ScriptPath = $MyInvocation.MyCommand.Definition
$ScriptsDir = Split-Path -Parent $ScriptPath
$Root = Split-Path -Parent $ScriptsDir
$RawDir = Join-Path $Root "data\mmh_raw"

New-Item -ItemType Directory -Path $RawDir -Force | Out-Null

if (Test-Path (Join-Path $RawDir ".git")) {
    Write-Host "==> Updating makemeahanzi..."
    git -C $RawDir pull --ff-only
} else {
    Write-Host "==> Cloning makemeahanzi..."
    git clone --depth 1 $RepoUrl $RawDir
}

Write-Host "==> Done. Raw data at: $RawDir"

