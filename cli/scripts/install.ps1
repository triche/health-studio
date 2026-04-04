# Health Studio CLI — Install Script (Windows PowerShell)
# Installs the `hs` command via pipx or pip install --user.
# Idempotent: safe to re-run.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CliDir = Split-Path -Parent $ScriptDir
$ConfigDir = Join-Path $env:USERPROFILE ".health-studio"
$MinPythonVersion = [version]"3.11"

function Write-Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Blue }
function Write-Ok($msg)    { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]   $msg" -ForegroundColor Red; exit 1 }

# --- Check Python >= 3.11 ---
$Python = $null
foreach ($candidate in @("python3", "python")) {
    try {
        $version = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($version) {
            $parsed = [version]$version
            if ($parsed -ge $MinPythonVersion) {
                $Python = $candidate
                break
            }
        }
    } catch {
        continue
    }
}

if (-not $Python) {
    Write-Err "Python >= $MinPythonVersion is required but not found on PATH."
}
$pyVer = & $Python --version
Write-Info "Using $Python ($pyVer)"

# --- Install via pipx or pip --user ---
$pipxPath = Get-Command pipx -ErrorAction SilentlyContinue
if ($pipxPath) {
    Write-Info "Installing via pipx..."
    & pipx install $CliDir --force
} else {
    $pipPath = Get-Command pip3 -ErrorAction SilentlyContinue
    if (-not $pipPath) { $pipPath = Get-Command pip -ErrorAction SilentlyContinue }
    if ($pipPath) {
        Write-Info "pipx not found. Installing via pip install --user..."
        & $pipPath.Source install --user $CliDir
    } else {
        Write-Err "Neither pipx nor pip found. Please install Python packaging tools."
    }
}

# --- Verify hs is on PATH ---
$hsPath = Get-Command hs -ErrorAction SilentlyContinue
if ($hsPath) {
    Write-Ok "hs command is available: $($hsPath.Source)"
} else {
    Write-Warn "hs is installed but not on your PATH."
    Write-Warn "You may need to add the Python Scripts directory to your PATH."
}

# --- Create config directory ---
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    Write-Ok "Created config directory: $ConfigDir"
} else {
    Write-Ok "Config directory already exists: $ConfigDir"
}

Write-Host ""
Write-Ok "Installation complete!"
Write-Info "Run 'hs config init' to connect to your Health Studio instance."
