# AutoFolder AI - Distribution Guide

## 📦 Building the EXE

### Prerequisites
1. Python 3.10+ installed
2. All requirements installed: `pip install -r requirements.txt`
3. ~500MB free disk space

### Build Steps

#### Option 1: Automated Build (Recommended)
```bash
python build.py
```
This will:
- ✅ Check requirements
- ✅ Download AI model
- ✅ Clean previous builds
- ✅ Bundle all resources
- ✅ Create standalone EXE

#### Option 2: Manual Build
```bash
# Clean previous builds
rmdir /s /q build dist

# Build with PyInstaller
python -m PyInstaller autofolder.spec --clean --noconfirm
```

### What Gets Bundled?

**✅ Automatically Included:**
- Python interpreter
- All Python dependencies (PySide6, torch, sentence-transformers, etc.)
- Configuration files (config/default_config.yaml)
- Folder icons (.ico files from resources/folder_icons/)
- AI model cache (sentence-transformers/all-MiniLM-L6-v2)
- Tesseract installer (for OCR) if present in project root

**📦 Distribution Package:**
```
dist/AutoFolder AI/
├── AutoFolder AI.exe      # Main executable (~200-300MB)
├── config/                # Configuration
├── resources/             # Icons and assets
├── models/                # AI model (if bundled)
├── third_party/            # Optional installers (e.g., Tesseract)
└── _internal/             # PyInstaller runtime files
```

---

## 🎁 Creating Professional Installer

### Prerequisites for Installer
1. Completed PyInstaller build in `dist/AutoFolder AI/`
2. Download and install **Inno Setup 6**: https://jrsoftware.org/isdl.php
3. Install with default settings

### Building the Installer

#### Option 1: Automated Installer Build (Recommended)
```bash
python build_installer.py
```

This will:
- ✅ Verify all prerequisites
- ✅ Find Inno Setup installation
- ✅ Compile the installer script
- ✅ Create professional setup.exe in `installer_output/`

#### Option 2: Manual Installer Build
1. Open `autofolder_installer.iss` in Inno Setup
2. Update these values at the top:
   ```pascal
   #define MyAppPublisher "Your Company Name"
   #define MyAppURL "https://yourwebsite.com"
   ```
3. Click **Build → Compile** (or press Ctrl+F9)
4. Find the setup.exe in `installer_output/`

### Installer Features

**✅ Professional Installation:**
- Installs to `C:\Program Files\AutoFolder AI\`
- Creates Start Menu folder with shortcuts
- Optional desktop shortcut (unchecked by default)
- Optional startup launch (unchecked by default)
- Registers in Windows Add/Remove Programs
- Modern wizard-style UI

**✅ Smart Uninstallation:**
- Removes all program files
- Cleans up registry entries
- Preserves user data in `%APPDATA%\AutoFolder AI\`
- Preserves logs in user's Documents folder
- Shows confirmation dialog

**✅ User Experience:**
- Shows license agreement (if LICENSE file exists)
- Checks if app is running before install
- Option to launch app after installation
- Clean, modern installation wizard

### Customizing the Installer

Edit `autofolder_installer.iss` to customize:

**Company/Product Info (lines 7-11):**
```pascal
#define MyAppVersion "1.0.0"        ; Update version number
#define MyAppPublisher "Your Name"  ; Your company/name
#define MyAppURL "https://..."      ; Your website
```

**Installation Options:**
- Change default installation folder (line 23)
- Require admin privileges (line 36): Change `lowest` to `admin`
- Change compression level (line 31)
- Add/remove desktop shortcut default (line 49)

**Bundled Files:**
The installer automatically includes:
- Everything from `dist/AutoFolder AI/`
- Config folder
- Resources (icons)
- AI models
- Documentation (README.md, LICENSE)

**Advanced Customization:**
- Custom welcome message: Edit `[Code]` section (line 100+)
- Dependency checks: Add to `DependenciesInstalled()` function
- Post-install actions: Edit `CurStepChanged()` function
- Custom uninstall logic: Edit `InitializeUninstall()` function

### Testing the Installer

**Before Distribution:**
1. **Test on Clean Machine:**
   - Use Windows Sandbox or fresh VM
   - Install with default options
   - Verify app launches and works
   - Test all features
   - Uninstall and verify clean removal

2. **Test Different Scenarios:**
   - [ ] Install to default location (Program Files)
   - [ ] Install to custom location
   - [ ] With/without desktop shortcut
   - [ ] With/without startup option
   - [ ] Install over previous version (upgrade)
   - [ ] Uninstall with app running (should warn)

3. **Verify Registry Entries:**
   - Open Registry Editor (regedit)
   - Check `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\`
   - Verify uninstaller is registered properly

### Distribution Package

**Final Output:**
```
installer_output/
└── AutoFolder-AI-Setup-v1.0.0.exe   (~70-80 MB compressed)
```

**This single file includes:**
- Main application executable
- All Python dependencies
- AI model (sentence-transformers)
- Tesseract installer
- Icons and resources
- Configuration files
- Documentation

---

## 🚀 Distribution

### Installation Methods

**Method 1: Professional Installer (Recommended for Sale)**
1. Download `AutoFolder-AI-Setup-v1.0.0.exe` (~70-80 MB)
2. Run the installer (no admin required)
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

**Method 2: Portable Version (Alternative)**
1. Download `AutoFolder-AI-Portable-v1.0.zip`
2. Extract to any folder
3. Run `AutoFolder AI.exe`
4. No installation required

### After Installation

**First Run:**
- Configuration stored in: `%APPDATA%\AutoFolder AI\`
- Logs created in: `%USERPROFILE%\Documents\AutoFolder_Logs\`
- AI model loads from installed location (no internet needed)
- Folder icons generated automatically

**OCR (Tesseract) Support:**
- If bundled: `Tools → Install OCR (Tesseract)`
- Requires admin approval (UAC prompt)
- Restart app after installation

**Uninstall:**
- Windows Settings → Apps → AutoFolder AI → Uninstall
- Or: Start Menu → AutoFolder AI → Uninstall
- User settings and logs are preserved

---

## 📋 Pre-Distribution Checklist

### Before Building Installer
- [ ] PyInstaller build completed successfully
- [ ] App tested and working from `dist/AutoFolder AI/`
- [ ] All files under 100MB (or adjust compression)
- [ ] Version number updated in `autofolder_installer.iss`
- [ ] Company name and URL updated in script
- [ ] LICENSE file present (or remove from script)

### Testing Checklist

**Test on a clean Windows machine:**

### Basic Functionality
- [ ] App launches without errors
- [ ] UI displays correctly
- [ ] Preview organization works
- [ ] Actual organization works
- [ ] Undo works
- [ ] Settings persist

### AI Features
- [ ] AI grouping works (no internet needed)
- [ ] Model loads from bundled cache
- [ ] Content analysis works

### Folder Icons
- [ ] Icons generate correctly
- [ ] Custom colors display
- [ ] desktop.ini files created
- [ ] Icons persist after restart

### Edge Cases
- [ ] Works without internet connection
- [ ] Handles locked files gracefully
- [ ] Works with OneDrive folders
- [ ] Large folders (1000+ files) work
- [ ] Special characters in filenames

### Installer Testing
- [ ] Installer runs without errors
- [ ] Start Menu shortcuts created
- [ ] Desktop shortcut works (if selected)
- [ ] App appears in Windows Add/Remove Programs
- [ ] Uninstaller removes all files properly
- [ ] Can reinstall after uninstall
- [ ] Upgrade from previous version works

---

## 🔐 Code Signing (Optional but Recommended)

For commercial distribution, code signing eliminates Windows security warnings.

### Why Code Sign?
- ✅ Eliminates "Unknown Publisher" warnings
- ✅ Builds trust with customers
- ✅ Reduces antivirus false positives
- ✅ Professional appearance

### Getting a Code Signing Certificate

**Option 1: Commercial Certificate (~$200-400/year)**
- **Sectigo (Comodo)**: https://sectigo.com/ssl-certificates-tls/code-signing
- **DigiCert**: https://www.digicert.com/signing/code-signing-certificates
- **SSL.com**: https://www.ssl.com/certificates/code-signing/

**Option 2: Open Source Projects (Free)**
- SignPath Foundation: https://signpath.org/ (for open-source projects)

### Signing the Installer

After obtaining your certificate:

```powershell
# Using Windows SDK SignTool
"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" sign /f "YourCertificate.pfx" /p "password" /tr "http://timestamp.digicert.com" /td SHA256 /fd SHA256 "installer_output\AutoFolder-AI-Setup-v1.0.0.exe"
```

**Or add to build_installer.py:**
```python
def sign_installer(installer_path, cert_path, cert_password):
    """Sign the installer with code signing certificate"""
    signtool = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
    
    cmd = [
        signtool, "sign",
        "/f", cert_path,
        "/p", cert_password,
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        "/fd", "SHA256",
        str(installer_path)
    ]
    
    subprocess.run(cmd, check=True)
```

---

## 🐛 Troubleshooting

### PyInstaller Build Issues

### Issue: "Module not found" during build
**Solution:** Ensure all dependencies installed:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: Build is too large (>500MB)
**Solution:** Exclude unnecessary packages in `autofolder.spec`:
```python
excludes=[
    'matplotlib', 'pandas', 'IPython', 
    'notebook', 'jupyter', 'tkinter',
]
```

### Issue: AI model not bundled
**Solution:** Pre-download model before building:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

### Issue: Antivirus flags EXE
**Solution:** 
- This is normal for PyInstaller EXEs
- Users should add to antivirus exclusions
- Sign the EXE with a code signing certificate (optional)

### Issue: "VCRUNTIME140.dll not found"
**Solution:** Include Visual C++ Redistributable:
- Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Include in distribution package
- Or use `--onefile` in PyInstaller (but slower startup)

### Installer Build Issues

### Issue: "Inno Setup not found"
**Solution:** 
- Download from: https://jrsoftware.org/isdl.php
- Install with default settings
- Restart terminal after installation

### Issue: "File not found" during compilation
**Solution:** 
- Verify `dist/AutoFolder AI/` exists
- Run `python build.py` first to create PyInstaller build
- Check all paths in `autofolder_installer.iss` are correct

### Issue: Installer is too large
**Solution:** 
- Use higher compression: Change `Compression=lzma2/max` to `lzma2/ultra64`
- Remove unnecessary files from build
- Exclude test folders and __pycache__ directories

### Issue: "Access denied" during install
**Solution:** 
- Change `PrivilegesRequired=lowest` to `admin` if needed
- Or install to user folder instead of Program Files
- Check antivirus isn't blocking the installer

---

## 📝 Release Notes Template

### AutoFolder AI v1.0 - Release Notes

**What's New:**
- 🎨 **Visual Organization**: 35 category folders with custom icons
- 📁 **100+ File Types**: Comprehensive file type recognition
- 🤖 **AI Grouping**: Local AI-powered semantic grouping
- ⚡ **Live Progress**: Real-time progress tracking
- 📅 **Date Folders**: Automatic date-based organization
- 🔄 **Undo Support**: Safely revert any organization
- 🎯 **Duplicate Detection**: Find and manage duplicates
- 🔍 **Smart Search**: Fast file search across folders
- 📊 **Statistics**: Detailed organization insights

**System Requirements:**
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- 500MB disk space

**No Installation Required:**
- Portable application
- No internet connection needed
- Works offline completely

**Download:**
- AutoFolder-AI-v1.0.zip (250MB)

---

## 🎯 Next Steps

1. **Build the EXE:**
   ```bash
   python build.py
   ```

2. **Test on clean machine:**
   - Use Windows Sandbox or VM
   - Test all features
   - Check for missing DLLs

3. **Create installer (optional):**
   - Use Inno Setup or NSIS
   - Add desktop shortcut
   - Add to Start Menu

4. **Sign the EXE (optional but recommended):**
   - Prevents antivirus warnings
   - Costs ~$200/year for certificate
   - Use SignTool from Windows SDK

5. **Distribute:**
   - Upload to Gumroad / itch.io
   - Create product page
   - Add screenshots and demo video

---

## 📧 Support

For build issues:
- Check PyInstaller documentation
- Review build logs in `build/AutoFolder AI/`
- Enable console mode for debugging: `console=True` in spec file
