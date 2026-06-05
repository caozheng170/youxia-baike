# Push flipbook to GitHub (caozheng170)
# Run:  .\.venv\Scripts\python.exe is NOT needed — use PowerShell:
#       powershell -ExecutionPolicy Bypass -File .\push_github.ps1

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$Git = 'C:\Program Files\Git\cmd\git.exe'
$Gh  = 'C:\Users\pgrad\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe'
$GitHubUser = 'caozheng170'
$DefaultRepo = 'youxia-baike'

# Prefer the full Git install over broken scoop shims on PATH
$env:PATH = (Split-Path $Git) + ';' + (($env:PATH -split ';') | Where-Object { $_ -notmatch 'scoop\\shims' }) -join ';'

if (-not (Test-Path $Git)) { throw "Git not found at $Git" }
if (-not (Test-Path $Gh))  { throw "GitHub CLI not found at $Gh" }

Write-Host ""
Write-Host "========================================"
Write-Host "  Push to GitHub ($GitHubUser)"
Write-Host "========================================"
Write-Host ""

# Step 1: login (gh writes to stderr when not logged in — don't treat as fatal)
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $Gh auth status *> $null
$loggedIn = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEAP

if (-not $loggedIn) {
    Write-Host "[1/2] Not logged in. Follow prompts: GitHub.com -> HTTPS -> Login with browser"
    Write-Host ""
    & $Gh auth login
    if ($LASTEXITCODE -ne 0) { throw "GitHub login failed" }
}

# Step 2: repo name
Write-Host ""
$input = Read-Host "Repo name [default: $DefaultRepo]"
$RepoName = if ([string]::IsNullOrWhiteSpace($input)) { $DefaultRepo } else { $input.Trim() }
$FullName = "$GitHubUser/$RepoName"

Write-Host ""
Write-Host "[2/2] Creating $FullName and pushing..."

# Remove old origin if pointing elsewhere
$origin = & $Git remote get-url origin 2>$null
if ($origin) {
    Write-Host "Removing existing origin: $origin"
    & $Git remote remove origin
}

& $Gh repo create $FullName --public --source=. --remote=origin --push
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "If repo already exists, try another name, or run manually:"
    Write-Host "  & `"$Git`" remote add origin https://github.com/$FullName.git"
    Write-Host "  & `"$Git`" push -u origin main"
    exit 1
}

$url = & $Gh repo view $FullName --json url -q .url
Write-Host ""
Write-Host "Done! Repo URL:"
Write-Host "  $url"
Write-Host ""
