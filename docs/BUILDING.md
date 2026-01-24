# Building AutoFolder AI for Distribution

## Option 1: Simple One-File EXE (Recommended for Start)

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Create Build Spec

Create `build_autofolder.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get the base path
base_path = Path.cwd()

a = Analysis(
    ['src/main.py'],
    pathex=[str(base_path)],
    binaries=[],
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'sentence_transformers',
        'torch',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyo = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyo,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoFolder_AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # Add your icon file
)
```

### Step 3: Build

```bash
# Build using spec file
pyinstaller build_autofolder.spec

# Output will be in dist/AutoFolder_AI.exe
```

### Step 4: Test

```bash
# Run the built EXE
dist\AutoFolder_AI.exe
```

---

## Option 2: Directory-Based Build (Smaller size)

```bash
# Create directory build instead of single file
pyinstaller --onedir --windowed --name="AutoFolder_AI" src/main.py
```

This creates a folder with the EXE and dependencies (smaller EXE, but needs the folder).

---

## Version Management

### Creating Base vs Pro Versions

#### Option A: Separate Builds

**Base Version:**
```yaml
# config/default_config.yaml
ai:
  enabled: false
```

Build:
```bash
pyinstaller --onefile --windowed --name="AutoFolder_AI_Base" src/main.py
```

**Pro Version:**
```yaml
# config/default_config.yaml
ai:
  enabled: true
```

Build:
```bash
pyinstaller --onefile --windowed --name="AutoFolder_AI_Pro" src/main.py
```

#### Option B: License Key System (Better)

1. Both versions have AI code
2. Pro features unlock with license key
3. Single build, controlled by license

This is more professional but requires license validation system.

---

## Reducing File Size

### Problem: EXE might be 200-500 MB with AI dependencies

### Solutions:

#### 1. Exclude Unnecessary Packages

In `.spec` file:
```python
excludes=[
    'matplotlib',
    'scipy',
    'pandas',
    'tkinter',
    'unittest',
    'test',
    'email',
    'html',
    'http',
    'xml',
    'xmlrpc',
]
```

#### 2. Use Smaller AI Model

In config:
```yaml
ai:
  embedding_model: "all-MiniLM-L6-v2"  # Only 90 MB
  # Instead of larger models like "all-mpnet-base-v2" (420 MB)
```

#### 3. Download AI Model Separately (Best for distribution)

**Strategy:**
- Base version: No AI (50-80 MB EXE)
- Pro version: Downloads AI model on first run (100 MB EXE + 90 MB model)

Implementation:
```python
# In classifier.py
def _load_model(self):
    model_name = self.ai_config.get('embedding_model', 'all-MiniLM-L6-v2')
    cache_dir = Path(self.ai_config.get('model_path', '../AI Model'))
    
    if not (cache_dir / model_name).exists():
        # Show download dialog
        reply = QMessageBox.question(
            None,
            "Download AI Model",
            f"Pro version requires AI model (~90 MB).\nDownload now?",
        )
        if reply == QMessageBox.Yes:
            # Download with progress bar
            self.model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
```

---

## Creating Installer (Optional, but professional)

### Using Inno Setup (Free, Windows)

1. Download Inno Setup: https://jrsoftware.org/isinfo.php

2. Create `installer.iss`:

```ini
[Setup]
AppName=AutoFolder AI
AppVersion=1.0.0
DefaultDirName={autopf}\AutoFolder AI
DefaultGroupName=AutoFolder AI
OutputDir=release
OutputBaseFilename=AutoFolder_AI_Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\AutoFolder_AI.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\AutoFolder AI"; Filename: "{app}\AutoFolder_AI.exe"
Name: "{autodesktop}\AutoFolder AI"; Filename: "{app}\AutoFolder_AI.exe"

[Run]
Filename: "{app}\AutoFolder_AI.exe"; Description: "Launch AutoFolder AI"; Flags: nowait postinstall skipifsilent
```

3. Compile with Inno Setup to create installer

---

## Portable Version (No Installation)

Users prefer portable apps. Just distribute the EXE with:

```
AutoFolder_AI_Portable/
├── AutoFolder_AI.exe
├── config/
│   └── default_config.yaml
└── README.txt
```

Zip this folder and distribute.

---

## Code Signing (Optional, but professional)

### Why?
- Windows SmartScreen won't block it
- Looks more professional
- Builds trust

### How?
1. Get code signing certificate (~$50-200/year)
2. Sign EXE:
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com AutoFolder_AI.exe
```

**Reality Check:** For first product, skip code signing. Users can click "More info" → "Run anyway" on SmartScreen.

---

## Testing Checklist Before Release

### Functional Tests
- [ ] Launches without errors
- [ ] Folder selection works
- [ ] Analysis completes successfully
- [ ] Organization works correctly
- [ ] Undo works properly
- [ ] All profiles work
- [ ] AI features work (Pro version)
- [ ] Closes cleanly

### Compatibility Tests
- [ ] Windows 10 (version 1809+)
- [ ] Windows 11
- [ ] Different user accounts (non-admin)
- [ ] Different folder locations
- [ ] Network drives (optional)

### Error Handling
- [ ] Invalid folder path
- [ ] Permission denied errors
- [ ] Disk full scenario
- [ ] Files in use
- [ ] Large folders (10,000+ files)

### Performance
- [ ] Startup time < 3 seconds
- [ ] Analysis time < 10 seconds for 1000 files
- [ ] Organization time < 30 seconds for 1000 files
- [ ] UI responsive during operations

---

## Distribution Checklist

### Files to Include
- [ ] AutoFolder_AI.exe
- [ ] README.txt (quick start)
- [ ] LICENSE.txt
- [ ] User Guide (PDF or link)

### Gumroad Upload
- [ ] Create product page
- [ ] Upload EXE (or ZIP)
- [ ] Set price (₹499 or ₹1299)
- [ ] Add product images
- [ ] Write description
- [ ] Set up license key (optional)

### Version Control
```
AutoFolder_AI_v1.0.0_Base.exe
AutoFolder_AI_v1.0.0_Pro.exe
```

Always version your releases!

---

## Quick Build Commands

### For Testing:
```bash
# Quick build for testing (with console for debugging)
pyinstaller --onefile --name="AutoFolder_AI_Test" src/main.py
```

### For Release:
```bash
# Production build (no console)
pyinstaller --onefile --windowed --name="AutoFolder_AI" --icon=icon.ico src/main.py
```

### With Spec File (Recommended):
```bash
# Build both versions
pyinstaller build_autofolder_base.spec
pyinstaller build_autofolder_pro.spec
```

---

## File Sizes to Expect

| Version | Expected Size | Notes |
|---------|--------------|-------|
| Base | 50-80 MB | No AI dependencies |
| Pro | 150-200 MB | With AI model embedded |
| Pro (Model separate) | 100 MB + 90 MB | Better distribution |

**Recommendation:** Keep model separate for Pro version. Download on first run.

---

## Next Steps

1. ✅ Complete code
2. ✅ Test thoroughly
3. ⬜ Create icon.ico (256x256 PNG → ICO)
4. ⬜ Build EXE
5. ⬜ Test on clean Windows machine
6. ⬜ Create Gumroad account
7. ⬜ Upload and set price
8. ⬜ Launch! 🚀
