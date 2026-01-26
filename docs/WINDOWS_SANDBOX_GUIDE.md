# 🧪 Testing Your Installer with Windows Sandbox

## What is Windows Sandbox?

**Windows Sandbox** is a free, built-in Windows 10/11 feature that creates a **temporary, disposable Windows environment** for testing. It's perfect for testing installers because:

✅ **Clean environment** - Fresh Windows installation every time  
✅ **Safe** - Completely isolated from your main system  
✅ **Fast** - Starts in seconds, no VM setup needed  
✅ **Free** - Built into Windows 10/11 Pro, Enterprise, Education  
✅ **Disposable** - Everything is deleted when you close it  

## 🚀 Quick Start Guide

### Step 1: Enable Windows Sandbox

**Check if you have it:**
1. Press `Win + R`
2. Type: `optionalfeatures`
3. Press Enter
4. Look for "Windows Sandbox" in the list

**Enable it (if not enabled):**
1. In the Optional Features window, check ☑️ "Windows Sandbox"
2. Click OK
3. Restart your computer

**If you don't see "Windows Sandbox":**
- You need Windows 10/11 **Pro**, **Enterprise**, or **Education**
- Windows Home does NOT include Sandbox
- Alternative: Use VirtualBox (see end of this guide)

### Step 2: Build Your Installer

```powershell
# Make sure you're in the project folder
cd "C:\Users\Praveen\Downloads\Python Scripts\AutoFolder AI"

# Build the installer
python build_installer.py
```

This creates: `installer_output\AutoFolder-AI-Setup-v1.0.0.exe`

### Step 3: Launch Windows Sandbox

**Method 1: Start Menu**
1. Click Start
2. Type "Windows Sandbox"
3. Click to launch

**Method 2: Run Dialog**
1. Press `Win + R`
2. Type: `WindowsSandbox`
3. Press Enter

A new window opens - this is a completely clean Windows installation!

### Step 4: Copy Installer to Sandbox

**Option A: Drag and Drop (Easiest)**
1. Open File Explorer on your main PC
2. Navigate to: `C:\Users\Praveen\Downloads\Python Scripts\AutoFolder AI\installer_output\`
3. Drag `AutoFolder-AI-Setup-v1.0.0.exe` into the Sandbox window
4. It appears on the Sandbox desktop

**Option B: Copy-Paste**
1. Right-click the installer file → Copy
2. Click inside the Sandbox window
3. Right-click on Sandbox desktop → Paste

**Option C: Share a Folder (Advanced)**
- See "Advanced: Auto-Copy Files" section below

### Step 5: Test the Installer

**Inside the Sandbox:**

1. **Run the installer**
   - Double-click `AutoFolder-AI-Setup-v1.0.0.exe`
   - You might see a security warning (normal for unsigned installers)
   - Click "More info" → "Run anyway"

2. **Go through installation**
   - ✅ Check: License agreement shows
   - ✅ Check: Installation location is correct
   - ✅ Check: Options (desktop shortcut, startup) work
   - ✅ Check: Installation completes without errors

3. **Test the installed app**
   - Click "Launch AutoFolder AI" (or find it in Start Menu)
   - ✅ Check: App launches successfully
   - ✅ Check: UI displays properly
   - ✅ Check: Create a test folder on the Sandbox desktop
   - ✅ Check: Add some test files
   - ✅ Check: Try organizing the folder
   - ✅ Check: Check if AI features work
   - ✅ Check: Try Tesseract installation (if bundled)

4. **Test the uninstaller**
   - Open Start Menu → AutoFolder AI → Uninstall
   - Or: Settings → Apps → AutoFolder AI → Uninstall
   - ✅ Check: Uninstaller shows confirmation
   - ✅ Check: App is removed from Start Menu
   - ✅ Check: Desktop shortcut removed
   - ✅ Check: Files removed from Program Files

5. **Close Sandbox**
   - Close the Sandbox window
   - All changes are discarded automatically

### Step 6: Fix Issues and Retest

If you found issues:
1. Fix them in your main system
2. Rebuild the installer: `python build_installer.py`
3. Open a fresh Sandbox (previous one is gone)
4. Test again

## ✅ Testing Checklist

Use this checklist inside the Sandbox:

### Installation Phase
- [ ] Installer launches without errors
- [ ] No missing DLL errors
- [ ] License agreement displays (if you have LICENSE file)
- [ ] Can choose installation location
- [ ] Desktop shortcut option works
- [ ] Startup option works
- [ ] Installation progress shows
- [ ] Installation completes successfully
- [ ] Start Menu shortcuts created
- [ ] Desktop shortcut created (if selected)

### Application Testing
- [ ] App launches from Start Menu
- [ ] App launches from Desktop shortcut
- [ ] Main window displays correctly
- [ ] No crash on startup
- [ ] Can select a folder to organize
- [ ] Preview organization works
- [ ] Actual organization works
- [ ] AI grouping works (no internet in Sandbox by default)
- [ ] Folder icons are created
- [ ] Settings can be changed
- [ ] Logs are created in correct location

### Advanced Features
- [ ] Tesseract installer is bundled (check app → Tools menu)
- [ ] Can install Tesseract from bundled installer
- [ ] OCR works after Tesseract installation
- [ ] Undo feature works
- [ ] Duplicate detection works
- [ ] Search works

### Uninstallation
- [ ] Can launch uninstaller from Start Menu
- [ ] Can launch uninstaller from Windows Settings
- [ ] Uninstaller asks for confirmation
- [ ] Shows what will be preserved (user data)
- [ ] Uninstall completes successfully
- [ ] Start Menu shortcuts removed
- [ ] Desktop shortcut removed
- [ ] Program Files folder removed
- [ ] Windows Add/Remove Programs entry removed

## 🎯 Advanced: Auto-Copy Files to Sandbox

Create a configuration file to automatically mount folders:

1. **Create a config file**: `AutoFolder-Test.wsb`

```xml
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>C:\Users\Praveen\Downloads\Python Scripts\AutoFolder AI\installer_output</HostFolder>
      <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\Installer</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>explorer C:\Users\WDAGUtilityAccount\Desktop\Installer</Command>
  </LogonCommand>
</Configuration>
```

2. **Save this file** in your project folder

3. **Double-click** `AutoFolder-Test.wsb` to launch Sandbox with your installer already available!

## 🔧 Troubleshooting

### "Windows Sandbox is not available"
**Cause:** You have Windows Home edition  
**Solution:** 
- Upgrade to Windows Pro ($99)
- Or use VirtualBox (free) - see below

### "Virtualization is not enabled"
**Solution:**
1. Restart computer
2. Enter BIOS/UEFI (usually press F2, Del, or F12 during startup)
3. Find "Virtualization" or "Intel VT-x" or "AMD-V"
4. Enable it
5. Save and exit

### Installer shows "Unknown Publisher" warning
**Normal!** Your installer is not code-signed yet. In Sandbox:
- Click "More info"
- Click "Run anyway"

This warning won't appear if you code-sign your installer ($200-400/year).

### App crashes in Sandbox
**Check:**
- Does it work on your main PC first?
- Check for hardcoded paths (use relative paths)
- Check logs in Sandbox: `%APPDATA%\AutoFolder AI\`

## 🖥️ Alternative: Using VirtualBox (If No Sandbox)

If you have Windows Home:

1. **Download VirtualBox**: https://www.virtualbox.org/
2. **Download Windows 10 ISO**: https://www.microsoft.com/software-download/windows10
3. **Create a VM**:
   - Click "New"
   - Name: "Installer Test"
   - Type: Windows 10 (64-bit)
   - RAM: 4GB
   - Disk: 50GB (dynamic)
4. **Install Windows** in the VM
5. **Test your installer** in the VM

**Pros:** Works on any Windows version  
**Cons:** Slower, takes up disk space, requires Windows license

## 📊 Testing Schedule

**Before releasing:**
- Test in Sandbox at least **3 times**
- Test on a real clean PC (friend's computer)
- Test on both Windows 10 and Windows 11 (if possible)

**After each change:**
- Quick test in Sandbox to verify the fix
- Full test before releasing update

## 🎓 Summary

```
1. Enable Windows Sandbox (one-time setup)
2. Build installer: python build_installer.py
3. Launch Sandbox from Start Menu
4. Drag installer into Sandbox
5. Install and test thoroughly
6. Close Sandbox (everything is deleted)
7. Fix issues and repeat
```

**Benefits:**
- ✅ Test in a truly clean environment
- ✅ No risk to your main system
- ✅ Fast and free
- ✅ Perfect for installer testing
- ✅ Can test unlimited times

## 🚀 Quick Test Script

Save this as `quick-sandbox-test.ps1`:

```powershell
# Quick Sandbox Test Script
Write-Host "Building installer..." -ForegroundColor Cyan
python build_installer.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstaller built successfully!" -ForegroundColor Green
    Write-Host "Location: installer_output\AutoFolder-AI-Setup-v1.0.0.exe" -ForegroundColor Yellow
    Write-Host "`nLaunching Windows Sandbox..." -ForegroundColor Cyan
    Start-Process "WindowsSandbox.exe"
    Write-Host "`nDrag the installer from 'installer_output' folder into Sandbox to test!" -ForegroundColor Green
} else {
    Write-Host "`nBuild failed! Check errors above." -ForegroundColor Red
}
```

Run: `.\quick-sandbox-test.ps1`

---

**You're now ready to test like a pro!** 🎉
