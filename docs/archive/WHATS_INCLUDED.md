# 🎯 AutoFolder AI Installer - What's Included?

## ✅ What Gets Bundled in the Installer

### Your Installer Includes:

#### 1. **Main Application** (~62 MB)
- `AutoFolder AI.exe` - Main executable
- All Python runtime and dependencies

#### 2. **AI Model** (Automatic from dist/_internal/models/)
- **sentence-transformers/all-MiniLM-L6-v2** model
- Size: ~80-90 MB
- Location: `_internal/models/`
- **Works completely offline** - no internet needed!
- Used for: AI-powered file grouping and content analysis

#### 3. **Configuration** (from dist/_internal/config/)
- `default_config.yaml` - Default app settings
- Users' custom settings stored in: `%APPDATA%\AutoFolder AI\`
- Logs stored in: `%USERPROFILE%\Documents\AutoFolder_Logs\`

#### 4. **Resources** (from dist/_internal/resources/)
- Folder icons (.ico files)
- UI assets
- Category icons for organized folders

#### 5. **Tesseract OCR Installer** (Optional)
- File: `tesseract-ocr-w64-setup-5.5.0.20241111.exe`
- Size: ~32 MB
- Location: `third_party/` folder after installation
- Users can install via: `Tools → Install OCR (Tesseract)` menu
- **Optional feature** - app works without it

#### 6. **Documentation**
- `README.md` - User guide
- `LICENSE` - License file

### Total Installed Size: ~250-300 MB
### Installer File Size: ~70-80 MB (compressed)

---

## 📦 How It's Bundled

Your `autofolder_installer.iss` script includes these lines:

```pascal
; All files from PyInstaller build (includes everything in _internal/)
Source: "dist\AutoFolder AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Tesseract installer (optional)
Source: "tesseract-ocr-w64-setup-5.5.0.20241111.exe"; DestDir: "{app}\third_party"; Flags: ignoreversion
```

This means:
- ✅ **All AI models** are bundled automatically
- ✅ **All configs** are bundled automatically  
- ✅ **All resources** are bundled automatically
- ✅ **Tesseract installer** is bundled if present in project folder

---

## 🔍 Verifying What's Included

### Before Building Installer

Check your dist folder has everything:

```powershell
# Check AI models
Test-Path "dist\AutoFolder AI\_internal\models"

# Check config
Test-Path "dist\AutoFolder AI\_internal\config"

# Check resources  
Test-Path "dist\AutoFolder AI\_internal\resources"

# List all contents
Get-ChildItem "dist\AutoFolder AI\_internal" -Directory
```

### After Installing (on test machine)

1. Install the app
2. Navigate to: `C:\Program Files\AutoFolder AI\`
3. Check folders:
   - `_internal\models\` - Should have AI model files
   - `_internal\config\` - Should have default_config.yaml
   - `_internal\resources\` - Should have icons
   - `third_party\` - Should have tesseract installer (if bundled)

---

## 🎯 What Happens When User Installs

### Installation Process:

1. **Installer Launches**
   - Shows license agreement (from LICENSE file)
   - User chooses installation location (default: Program Files)
   - User can select optional shortcuts

2. **Files Are Copied**
   - All files from `dist\AutoFolder AI\` → `C:\Program Files\AutoFolder AI\`
   - This includes the `_internal\` folder with:
     - AI models
     - Config files
     - Resources
     - All Python dependencies

3. **Shortcuts Created**
   - Start Menu: `AutoFolder AI` folder with app shortcut
   - Desktop: `AutoFolder AI` shortcut (if user selected)
   - Startup: Launch at boot (if user selected)

4. **Registry Entries**
   - App registered in Windows Add/Remove Programs
   - Install path stored for app to find resources

5. **First Launch**
   - App creates user config in: `%APPDATA%\AutoFolder AI\`
   - App loads AI model from: `C:\Program Files\AutoFolder AI\_internal\models\`
   - App creates logs in: `%USERPROFILE%\Documents\AutoFolder_Logs\`
   - **No internet required** - everything works offline!

---

## 🧪 Testing AI Model is Bundled

After installing in Windows Sandbox or test PC:

1. **Launch the app**
2. **Go to a folder with files**
3. **Enable "AI Grouping"** option
4. **Click "Preview Organization"**

**Expected Result:**
- AI grouping works immediately
- No "downloading model" message
- No internet connection needed
- Files are grouped by semantic similarity

**If AI doesn't work:**
- Check: `C:\Program Files\AutoFolder AI\_internal\models\` exists
- Check: Model files are present (should be ~80-90 MB)
- Check logs: `%USERPROFILE%\Documents\AutoFolder_Logs\`

---

## 🧪 Testing Tesseract is Bundled

After installing:

1. **Launch the app**
2. **Go to: Tools → Install OCR (Tesseract)**

**Expected Result:**
- Menu option is enabled (not grayed out)
- Clicking it launches Tesseract installer
- Installer is located at: `C:\Program Files\AutoFolder AI\third_party\tesseract-ocr-w64-setup-5.5.0.20241111.exe`

**If menu is disabled:**
- Tesseract installer wasn't bundled
- Check project folder has: `tesseract-ocr-w64-setup-5.5.0.20241111.exe`
- Rebuild installer

---

## 📝 What's NOT Bundled (Stored Separately)

These are created at runtime, not bundled:

### User Settings
- Location: `%APPDATA%\AutoFolder AI\config\user_config.yaml`
- Created on first run
- Preserved during uninstall

### User Logs
- Location: `%USERPROFILE%\Documents\AutoFolder_Logs\`
- Created during app usage
- Preserved during uninstall

### Tesseract Installation
- Only the **installer** is bundled
- User must run it to install Tesseract
- Tesseract installs to: `C:\Program Files\Tesseract-OCR\`

---

## 🎯 Customizing What's Bundled

### To Remove Tesseract Installer

If you don't want to bundle Tesseract, comment out this line in `autofolder_installer.iss`:

```pascal
; Source: "tesseract-ocr-w64-setup-5.5.0.20241111.exe"; DestDir: "{app}\third_party"; Flags: ignoreversion
```

### To Add Additional Files

Add to `autofolder_installer.iss`:

```pascal
; Example: Add user manual PDF
Source: "docs\UserManual.pdf"; DestDir: "{app}\docs"; Flags: ignoreversion
```

### To Exclude Large Files

If you need a smaller installer, you can exclude certain PyInstaller outputs, but be careful not to break functionality.

---

## 📊 Size Breakdown

| Component | Size | Required? |
|-----------|------|-----------|
| Main EXE | ~1 MB | ✅ Yes |
| Python runtime | ~15 MB | ✅ Yes |
| PySide6 (UI) | ~50 MB | ✅ Yes |
| PyTorch (AI) | ~100 MB | ✅ Yes |
| AI Model | ~90 MB | ✅ Yes (for AI features) |
| Other dependencies | ~30 MB | ✅ Yes |
| Tesseract installer | ~32 MB | ⚠️ Optional |
| **Total** | **~320 MB** | |
| **Compressed installer** | **~70-80 MB** | |

The Inno Setup compressor reduces the size by ~75%!

---

## ✅ Final Checklist

Before distributing, verify:

- [ ] AI models are in `_internal\models\` folder
- [ ] Config files are in `_internal\config\` folder
- [ ] Resources are in `_internal\resources\` folder
- [ ] Tesseract installer is bundled (if desired)
- [ ] README.md and LICENSE are included
- [ ] Installer size is reasonable (~70-80 MB)
- [ ] Tested in clean environment (Sandbox)
- [ ] AI features work offline
- [ ] Tesseract installation works (if bundled)

---

## 🚀 Quick Verification Commands

```powershell
# Check what's in your dist folder before building installer
Get-ChildItem "dist\AutoFolder AI\_internal" -Recurse | Measure-Object -Property Length -Sum

# Verify AI models
Get-ChildItem "dist\AutoFolder AI\_internal\models" -Recurse

# Check installer size after building
Get-Item "installer_output\AutoFolder-AI-Setup-*.exe" | Select Name, @{Name="Size (MB)";Expression={[math]::Round($_.Length / 1MB, 1)}}
```

---

**Everything is already configured correctly!** 

The installer script automatically includes:
- ✅ AI models (from `_internal\models\`)
- ✅ Config (from `_internal\config\`)
- ✅ Resources (from `_internal\resources\`)
- ✅ Tesseract installer (from project root)

Just run: `python build_installer.py` 🎉
