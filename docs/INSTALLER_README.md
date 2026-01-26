# 🚀 Ready to Build Your Installer!

Everything is configured and ready. Here's how to get started:

## Quick Start (3 Easy Steps)

### 1️⃣ Run the Setup Wizard
```powershell
.\setup_installer.ps1
```

This will:
- ✅ Check if Inno Setup is installed (install it if not)
- ✅ Verify your PyInstaller build exists
- ✅ Check AI models, config, and Tesseract are bundled
- ✅ Help you customize version/company name
- ✅ Build the installer
- ✅ Optionally launch Windows Sandbox for testing

### 2️⃣ Or Build Manually
```powershell
python build_installer.py
```

Output: `installer_output\AutoFolder-AI-Setup-v1.0.0.exe` (~70-80 MB)

### 3️⃣ Test in Windows Sandbox
```powershell
# Launch Sandbox
WindowsSandbox.exe

# Then drag the installer into Sandbox and test!
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **[INSTALLER_QUICK_START.md](INSTALLER_QUICK_START.md)** | Complete guide from start to finish |
| **[WHATS_INCLUDED.md](WHATS_INCLUDED.md)** | What gets bundled in the installer |
| **[WINDOWS_SANDBOX_GUIDE.md](WINDOWS_SANDBOX_GUIDE.md)** | How to test with Windows Sandbox |
| **[BUILD_GUIDE.md](BUILD_GUIDE.md)** | Full technical documentation |

---

## ✅ What's Already Configured

### Your installer includes:
- ✅ **AI Models** - sentence-transformers model (~90 MB) - works offline!
- ✅ **Configuration** - default_config.yaml
- ✅ **Resources** - folder icons and UI assets
- ✅ **Tesseract Installer** - OCR support (users can install from app)
- ✅ **Start Menu shortcuts** - professional installation
- ✅ **Optional desktop shortcut** - user can choose
- ✅ **Optional startup launch** - launch at Windows startup
- ✅ **Windows uninstaller** - registered in Add/Remove Programs
- ✅ **Clean uninstall** - preserves user data

### No editing needed!
The `.iss` file is pre-configured. Just update:
- Version number (default: 1.0.0)
- Your name/company (default: AutoFolder AI)
- Your website (optional)

**The setup wizard (`setup_installer.ps1`) will help you with this!**

---

## 🎯 Installation Flow

```
User downloads: AutoFolder-AI-Setup-v1.0.0.exe (70-80 MB)
         ↓
Runs installer → Shows license agreement
         ↓
Chooses options → Desktop shortcut? Startup?
         ↓
Installs to: C:\Program Files\AutoFolder AI\
         ↓
Creates shortcuts in Start Menu
         ↓
Registers in Windows Add/Remove Programs
         ↓
User can launch immediately!
```

**Everything works offline** - AI models are bundled!

---

## 🧪 Testing Checklist

Before distributing:

- [ ] Run `setup_installer.ps1` to build
- [ ] Test in Windows Sandbox (see guide)
- [ ] Verify AI grouping works (no internet needed)
- [ ] Test Tesseract installation (Tools menu)
- [ ] Verify all features work
- [ ] Test uninstaller
- [ ] Test on real clean PC (optional but recommended)

---

## 💡 Common Questions

### "Where is the AI model?"
- Bundled in: `_internal\models\` folder
- Automatically included when you build installer
- Works completely offline!

### "Where is Tesseract?"
- The **installer** is bundled (not Tesseract itself)
- Users install it via: `Tools → Install OCR (Tesseract)`
- App works fine without it (OCR is optional)

### "Do I need to edit the .iss file?"
- **No!** The setup wizard handles this
- Or you can manually edit 3 lines (version, name, URL)
- Everything else is pre-configured

### "What is Windows Sandbox?"
- Built-in Windows 10/11 feature for testing
- Creates disposable Windows environment
- Perfect for testing installers safely
- See: [WINDOWS_SANDBOX_GUIDE.md](WINDOWS_SANDBOX_GUIDE.md)

### "Can I sell this?"
- Yes! The installer is professional and ready
- Consider code signing ($200-400/year) to remove "Unknown Publisher" warning
- See [BUILD_GUIDE.md](BUILD_GUIDE.md#code-signing) for details

---

## 🎉 You're Ready!

Run this command to get started:

```powershell
.\setup_installer.ps1
```

The wizard will guide you through everything!

---

## 📞 Need Help?

Check these files:
1. **[INSTALLER_QUICK_START.md](INSTALLER_QUICK_START.md)** - Step-by-step guide
2. **[WHATS_INCLUDED.md](WHATS_INCLUDED.md)** - Understanding what's bundled
3. **[WINDOWS_SANDBOX_GUIDE.md](WINDOWS_SANDBOX_GUIDE.md)** - Testing guide
4. **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Advanced topics

---

**Built with ❤️ for easy Windows distribution!**
