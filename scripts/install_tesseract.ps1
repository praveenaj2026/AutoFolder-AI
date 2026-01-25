Param(
    [string]$InstallerPath = ""
)

$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host "Re-launching as Administrator..."
    $argsList = @()
    if ($InstallerPath -ne "") { $argsList += "-InstallerPath"; $argsList += $InstallerPath }
    Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @('-ExecutionPolicy','Bypass','-File', $PSCommandPath) + $argsList
    exit 0
}

$scriptDir = Split-Path -Parent $PSCommandPath

if ($InstallerPath -eq "") {
    $candidates = @(
        Join-Path $scriptDir "..\tesseract-ocr-w64-setup-5.5.0.20241111.exe",
        Join-Path $scriptDir "..\third_party\tesseract-ocr-w64-setup-5.5.0.20241111.exe"
    )

    foreach ($c in $candidates) {
        if (Test-Path $c) { $InstallerPath = (Resolve-Path $c).Path; break }
    }
}

if (-not (Test-Path $InstallerPath)) {
    throw "Tesseract installer not found. Provide -InstallerPath or place the installer next to the app (or in third_party)."
}

Write-Host "Installing Tesseract from: $InstallerPath"
Start-Process -FilePath $InstallerPath -ArgumentList '/S' -Wait

$installed = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $installed) {
    Write-Warning "Install completed, but tesseract.exe was not found in the usual locations."
    Write-Warning "You may have installed to a custom path."
    exit 1
}

Write-Host "Found installed Tesseract at: $installed"

# Set a stable env var the app can use
[Environment]::SetEnvironmentVariable('TESSERACT_CMD', $installed, 'Machine')

Write-Host "Set machine env var TESSERACT_CMD=$installed"
Write-Host "Done. Restart AutoFolder AI (and any open terminals) to pick up env changes."