$ErrorActionPreference = "SilentlyContinue"
$documentsPath = "$env:OneDrive\Documents"

$legacyFolders = @(
    "$documentsPath\TEST_ORGANIZE",
    "$documentsPath\Torrents\1080P",
    "$documentsPath\Torrents\Jan-26",
    "$documentsPath\Documents\Test"
)

Write-Host "Cleaning up v1.0 legacy folders..." -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0

foreach ($folder in $legacyFolders) {
    if (Test-Path $folder) {
        Write-Host "Deleting: $folder" -ForegroundColor Yellow
        Remove-Item $folder -Recurse -Force
        
        if (-not (Test-Path $folder)) {
            Write-Host "  OK deleted" -ForegroundColor Green
            $deletedCount = $deletedCount + 1
        } else {
            Write-Host "  FAILED" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host ("Cleanup complete! Deleted " + $deletedCount + " folders.") -ForegroundColor Green
