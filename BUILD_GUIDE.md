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

## 🚀 Distribution

### For Users

**Installation:**
1. Download `AutoFolder-AI-v1.0.zip`
2. Extract to any folder (recommended: `C:\Users\<Username>\AppData\Local\AutoFolder AI\`)
3. Run `AutoFolder AI.exe`

**Permissions note:**
- Installing under `C:\Program Files\...` can trigger permission prompts when updating files.
- The app can *organize* folders anywhere you have access to, but Windows may block icon writes in protected locations.
- Best default for a portable app is a user-writable folder.

**First Run:**
- The app will create logs in: `C:\Users\<Username>\OneDrive\Documents\AutoFolder_Logs\`
- AI model will be loaded from bundled cache (no internet needed)
- Folder icons will be generated automatically

**OCR (Tesseract) Install:**
- If the build includes the Tesseract installer, users can install it from:
   - `Tools → Install OCR (Tesseract)`
- The installer requires Windows admin approval (UAC prompt).
- After install, restart AutoFolder AI to enable OCR.

**No Installation Needed!**
- Portable application
- No system changes
- No registry modifications
- Just extract and run

---

## 📋 Testing Checklist

Before distributing, test on a **clean Windows machine**:

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

---

## 🐛 Troubleshooting Build Issues

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
