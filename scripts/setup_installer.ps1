# AutoFolder AI - First-Time Installer Setup
# This script helps you prepare everything for building the installer

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  AutoFolder AI - Installer Setup Wizard" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Inno Setup installer exists
$innoSetupInstaller = "innosetup-6.7.0.exe"
$tesseractInstaller = "tesseract-ocr-w64-setup-5.5.0.20241111.exe"

# Step 1: Check for Inno Setup
Write-Host "Step 1: Checking for Inno Setup..." -ForegroundColor Yellow

$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoSetupPath) {
    Write-Host "  ✓ Inno Setup is already installed!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Inno Setup not found" -ForegroundColor Red
    
    if (Test-Path $innoSetupInstaller) {
        Write-Host ""
        Write-Host "  Found installer: $innoSetupInstaller" -ForegroundColor Cyan
        $install = Read-Host "  Do you want to install Inno Setup now? (Y/N)"
        
        if ($install -eq "Y" -or $install -eq "y") {
            Write-Host "  Installing Inno Setup..." -ForegroundColor Yellow
            Start-Process -FilePath $innoSetupInstaller -Wait
            Write-Host "  ✓ Installation complete! Please restart this script." -ForegroundColor Green
            exit 0
        }
    } else {
        Write-Host ""
        Write-Host "  Please download Inno Setup from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
        Write-Host "  Or move innosetup-6.7.0.exe to the project folder" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# Step 2: Check for PyInstaller build
Write-Host "Step 2: Checking PyInstaller build..." -ForegroundColor Yellow

$distFolder = "dist\AutoFolder AI"
$exePath = "$distFolder\AutoFolder AI.exe"

if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    Write-Host "  ✓ Build found: $exePath ($([math]::Round($size, 1)) MB)" -ForegroundColor Green
} else {
    Write-Host "  ✗ PyInstaller build not found" -ForegroundColor Red
    Write-Host ""
    $build = Read-Host "  Do you want to build now? (Y/N)"
    
    if ($build -eq "Y" -or $build -eq "y") {
        Write-Host "  Building application..." -ForegroundColor Yellow
        python build.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Build complete!" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Build failed! Please check errors above." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  Please run: python build.py" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# Step 3: Check bundled content
Write-Host "Step 3: Verifying bundled content..." -ForegroundColor Yellow

# Check for AI models
$modelsPath = "$distFolder\_internal\models"
if (Test-Path $modelsPath) {
    Write-Host "  ✓ AI models bundled" -ForegroundColor Green
} else {
    Write-Host "  ✗ AI models not found (may cause issues)" -ForegroundColor Red
}

# Check for config
$configPath = "$distFolder\_internal\config"
if (Test-Path $configPath) {
    Write-Host "  ✓ Config bundled" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Config not bundled (will use defaults)" -ForegroundColor Yellow
}

# Check for resources
$resourcesPath = "$distFolder\_internal\resources"
if (Test-Path $resourcesPath) {
    Write-Host "  ✓ Resources bundled" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Resources not bundled" -ForegroundColor Yellow
}

# Check for Tesseract installer
if (Test-Path $tesseractInstaller) {
    Write-Host "  ✓ Tesseract installer ready to bundle" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Tesseract installer not found (optional)" -ForegroundColor Yellow
    Write-Host "    Users won't be able to install OCR from the app" -ForegroundColor Gray
}

Write-Host ""

# Step 4: Customize installer script
Write-Host "Step 4: Customizing installer script..." -ForegroundColor Yellow

$issFile = "autofolder_installer.iss"
if (Test-Path $issFile) {
    Write-Host "  ✓ Installer script found: $issFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Current settings:" -ForegroundColor Cyan
    
    # Read current values
    $content = Get-Content $issFile -Raw
    if ($content -match '#define MyAppVersion "([^"]+)"') {
        Write-Host "    Version: $($Matches[1])" -ForegroundColor White
    }
    if ($content -match '#define MyAppPublisher "([^"]+)"') {
        Write-Host "    Publisher: $($Matches[1])" -ForegroundColor White
    }
    if ($content -match '#define MyAppURL "([^"]+)"') {
        Write-Host "    URL: $($Matches[1])" -ForegroundColor White
    }
    
    Write-Host ""
    $customize = Read-Host "  Do you want to customize these now? (Y/N)"
    
    if ($customize -eq "Y" -or $customize -eq "y") {
        Write-Host ""
        $version = Read-Host "  Enter version (press Enter for 1.0.0)"
        if ([string]::IsNullOrWhiteSpace($version)) { $version = "1.0.0" }
        
        $publisher = Read-Host "  Enter your name/company"
        if ([string]::IsNullOrWhiteSpace($publisher)) { $publisher = "AutoFolder AI" }
        
        $url = Read-Host "  Enter your website (optional)"
        if ([string]::IsNullOrWhiteSpace($url)) { $url = "https://github.com/yourusername/autofolder-ai" }
        
        # Update the file
        $content = $content -replace '#define MyAppVersion "[^"]+"', "#define MyAppVersion `"$version`""
        $content = $content -replace '#define MyAppPublisher "[^"]+"', "#define MyAppPublisher `"$publisher`""
        $content = $content -replace '#define MyAppURL "[^"]+"', "#define MyAppURL `"$url`""
        
        Set-Content -Path $issFile -Value $content
        Write-Host "  ✓ Settings updated!" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ Installer script not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete! Ready to build installer." -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 5: Build installer
Write-Host "Do you want to build the installer now? (Y/N)" -ForegroundColor Yellow
$buildNow = Read-Host

if ($buildNow -eq "Y" -or $buildNow -eq "y") {
    Write-Host ""
    Write-Host "Building installer..." -ForegroundColor Cyan
    python build_installer.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host "  SUCCESS! Installer created." -ForegroundColor Green
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Location: installer_output\AutoFolder-AI-Setup-v$version.exe" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Test in Windows Sandbox (see WINDOWS_SANDBOX_GUIDE.md)" -ForegroundColor White
        Write-Host "  2. Test on a real clean PC" -ForegroundColor White
        Write-Host "  3. Consider code signing for commercial use" -ForegroundColor White
        Write-Host "  4. Upload to your distribution platform" -ForegroundColor White
        Write-Host ""
        
        # Ask about testing
        Write-Host "Do you want to open Windows Sandbox for testing? (Y/N)" -ForegroundColor Yellow
        $sandbox = Read-Host
        
        if ($sandbox -eq "Y" -or $sandbox -eq "y") {
            Write-Host ""
            Write-Host "Launching Windows Sandbox..." -ForegroundColor Cyan
            Write-Host "Drag the installer from 'installer_output' folder into Sandbox to test!" -ForegroundColor Yellow
            Start-Process "WindowsSandbox.exe"
        }
    }
} else {
    Write-Host ""
    Write-Host "To build the installer later, run:" -ForegroundColor Yellow
    Write-Host "  python build_installer.py" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
