# 🚀 AutoFolder AI Installer - Quick Start Guide

## Prerequisites

1. **Complete PyInstaller Build**
   ```bash
   python build.py
   ```
   Verify: `dist/AutoFolder AI/AutoFolder AI.exe` exists

2. **Install Inno Setup**
   - Download: https://jrsoftware.org/isdl.php
   - Install "Inno Setup 6" with default settings
   - No configuration needed

## Step-by-Step: Building Your Installer

### 1. Customize the Installer Script

Open [autofolder_installer.iss](autofolder_installer.iss) and update these lines:

```pascal
#define MyAppVersion "1.0.0"                    ; Line 8 - Your version
#define MyAppPublisher "Your Company Name"      ; Line 9 - Your name/company
#define MyAppURL "https://yourwebsite.com"      ; Line 10 - Your website
```

### 2. Build the Installer

**Option A: Automated (Recommended)**
```bash
python build_installer.py
```

**Option B: Manual**
1. Open `autofolder_installer.iss` in Inno Setup
2. Press **Ctrl+F9** (or click Build → Compile)
3. Wait for compilation to complete

### 3. Find Your Installer

Location: `installer_output/AutoFolder-AI-Setup-v1.0.0.exe`

**File size:** ~70-80 MB (compressed from ~250MB build)

## What's Included in the Installer?

✅ Everything from your `dist/AutoFolder AI/` folder:
- Main application executable
- Python runtime and dependencies
- AI model (sentence-transformers)
- Tesseract installer
- Icons and resources
- Configuration files

✅ Professional installation features:
- Modern wizard UI
- License agreement display
- Program Files installation
- Start Menu shortcuts
- Optional desktop shortcut
- Optional startup launch
- Windows uninstaller registration

## Testing Your Installer

### Before Distribution:

1. **Test on Clean Windows Machine**
   - Windows Sandbox (quickest method)
   - Fresh Windows VM
   - Friend's computer

2. **Installation Test:**
   ```
   Run: AutoFolder-AI-Setup-v1.0.0.exe
   ✓ Installer launches without errors
   ✓ License agreement shows
   ✓ Installation completes successfully
   ✓ Start Menu shortcuts created
   ✓ Desktop shortcut works (if selected)
   ✓ App launches from shortcuts
   ✓ App functions properly
   ```

3. **Functionality Test:**
   - Organize a test folder
   - Enable AI grouping
   - Create folder icons
   - Check logs are created
   - Test OCR installation (if bundled)

4. **Uninstall Test:**
   ```
   Run uninstaller from:
   - Windows Settings → Apps → AutoFolder AI
   - Or: Start Menu → AutoFolder AI → Uninstall
   
   ✓ Uninstaller shows confirmation
   ✓ All files removed from Program Files
   ✓ Start Menu shortcuts removed
   ✓ Desktop shortcut removed
   ✓ Registry entries cleaned
   ✓ User data preserved in AppData
   ```

## Distribution

### For Free/Open Source:
- Upload to GitHub Releases
- Share direct download link
- No code signing needed (but recommended)

### For Commercial Sale:
1. **Code Sign the Installer** (highly recommended)
   - Cost: $200-400/year for certificate
   - Eliminates "Unknown Publisher" warning
   - Builds customer trust
   - See: [Code Signing Guide](BUILD_GUIDE.md#code-signing)

2. **Distribution Platforms:**
   - **Gumroad**: Easy, takes ~10% commission
   - **Itch.io**: Game/software marketplace
   - **Your Website**: Full control, need payment processor
   - **Microsoft Store**: Requires code signing + review

3. **Create Product Page:**
   - Screenshots of the app
   - Demo video (1-2 minutes)
   - Feature list
   - System requirements
   - Clear pricing
   - Download button

## Common Customizations

### Change Installation Folder
Edit line 23 in `autofolder_installer.iss`:
```pascal
DefaultDirName={autopf}\{#MyAppName}     ; Program Files
; Or:
DefaultDirName={localappdata}\{#MyAppName}  ; AppData\Local
```

### Desktop Shortcut ON by Default
Edit line 49:
```pascal
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked
```

### Require Admin Privileges
Edit line 36:
```pascal
PrivilegesRequired=admin
```

### Change Compression
Edit line 31 for smaller installer (slower compression):
```pascal
Compression=lzma2/ultra64
```

## Support Resources

- **Inno Setup Documentation**: https://jrsoftware.org/ishelp/
- **PyInstaller Docs**: https://pyinstaller.org/
- **Full Build Guide**: [BUILD_GUIDE.md](BUILD_GUIDE.md)

## Troubleshooting

**Problem:** `build_installer.py` says "Inno Setup not found"  
**Solution:** Install Inno Setup and restart your terminal

**Problem:** Installer compilation fails  
**Solution:** Check `dist/AutoFolder AI/` exists and contains `AutoFolder AI.exe`

**Problem:** Installer runs but app doesn't launch  
**Solution:** Test the app directly from `dist/AutoFolder AI/AutoFolder AI.exe` first

**Problem:** Windows Defender blocks the installer  
**Solution:** This is normal for unsigned installers. Code signing eliminates this warning.

**Problem:** Installed app can't find resources  
**Solution:** Check paths in your app code use relative paths or detect install location

## Quick Command Reference

```bash
# Build PyInstaller package
python build.py

# Build installer (automated)
python build_installer.py

# Build installer (manual)
# Open autofolder_installer.iss in Inno Setup, press Ctrl+F9

# Test the built installer
.\installer_output\AutoFolder-AI-Setup-v1.0.0.exe
```

## Final Checklist

Before distributing:
- [ ] Version number updated in installer script
- [ ] Company name and URL customized
- [ ] Tested on clean Windows machine
- [ ] All features work after installation
- [ ] Uninstaller works properly
- [ ] README and LICENSE included
- [ ] Screenshots/videos prepared (if selling)
- [ ] Consider code signing (for commercial)
- [ ] Product page created
- [ ] Pricing decided (if commercial)

---

**Ready to Ship!** 🎉

Your installer is production-ready. Upload it to your distribution platform and start sharing your app!
