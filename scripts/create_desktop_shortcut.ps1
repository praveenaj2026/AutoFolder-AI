# AutoFolder AI - Desktop Shortcut Creator
# Run this script to create a shortcut on your desktop

$AppPath = $PSScriptRoot
$LaunchBat = Join-Path $AppPath "launch.bat"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "AutoFolder AI.lnk"

# Check if launch.bat exists
if (-not (Test-Path $LaunchBat)) {
    Write-Host "ERROR: launch.bat not found!" -ForegroundColor Red
    Write-Host "Please make sure you're running this from the AutoFolder AI directory." -ForegroundColor Yellow
    pause
    exit 1
}

# Create shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $LaunchBat
$Shortcut.WorkingDirectory = $AppPath
$Shortcut.Description = "AutoFolder AI - Smart File Organizer"
$Shortcut.IconLocation = "shell32.dll,4"  # Folder icon
$Shortcut.Save()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Desktop Shortcut Created!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now double-click 'AutoFolder AI' on your desktop to launch the app!" -ForegroundColor Yellow
Write-Host ""
pause
