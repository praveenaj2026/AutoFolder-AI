# Testing AutoFolder AI Installer with VirtualBox (Windows Home)

Since Windows Sandbox is not available on Windows Home, use VirtualBox instead.

## Quick Setup Guide

### Step 1: Download VirtualBox
- URL: https://www.virtualbox.org/wiki/Downloads
- Download: "Windows hosts" (latest version)
- Install with default settings

### Step 2: Download Windows 11 ISO (Free & Legal)
- URL: https://www.microsoft.com/software-download/windows11
- Click "Download Windows 11 Disk Image (ISO)"
- Select "Windows 11 (multi-edition ISO)"
- Download the ISO file (~5-6 GB)
- **💡 Tip:** You can save/use the ISO from an external HDD to save space on your main drive!

### Step 3: Create a Virtual Machine

1. Open VirtualBox
2. Click "New" button
3. Configure:
   - **Name:** Installer Test
   - **Type:** Microsoft Windows
   - **Version:** Windows 11 (64-bit)
   - **Memory:** 2048 MB (2 GB) - minimum, or 4096 MB (4 GB) - recommended
   - **Hard Disk:** Create virtual hard disk now
   - **Disk Size:** 50 GB
   - **Disk Type:** VDI (VirtualBox Disk Image)
   - **Storage:** Dynamically allocated
   - **Location:** Internal SSD (fast) or External HDD (saves space) - see guide below
4. Click "Create"

#### VM Storage Location Options:

**Option A: Internal SSD (Default - Recommended)**
- ✅ **Fast** - VM runs smoothly
- ✅ **Always available** - no need to connect external drive
- ❌ Uses 20-30GB on your C: drive (starts small, grows to ~30GB)
- **Best for:** Regular testing, daily use

**Option B: External HDD**
- ✅ **Saves internal space** - keeps your SSD free
- ✅ **Portable** - can move VM to another PC
- ❌ **Slower** - VM will be sluggish, especially boot time
- ❌ **Must stay connected** - external HDD must be plugged in when using VM
- ❌ **USB speed matters** - USB 2.0 = very slow, USB 3.0 = acceptable
- **Best for:** One-time testing, limited internal storage

**How to change VM location:**
- When creating VM, before clicking "Create", click the folder icon next to hard disk location
- Browse to your external drive (e.g., `E:\VirtualBox\Installer Test`)
- VirtualBox will create the VM files there

### Step 4: Install Windows 11

1. Select your new VM
2. Click "Settings"
3. Go to "Storage"
4. Click the empty CD icon
5. Click "Choose a disk file"
6. Select your Windows 11 ISO (can be on external HDD - just browse to it)
7. Click OK
8. Click "Start" to boot the VM
9. Install Windows 11:
   - Skip product key (can test for 30 days)
   - Choose "Windows 11 Home"
   - Select "Custom Install"
   - Install to the virtual drive
   - Wait 10-15 minutes
10. Complete Windows setup (create account, etc.)

### Step 5: Install Guest Additions (Important!)

After Windows is installed in the VM:

1. In the VM window menu: **Devices** → **Insert Guest Additions CD Image**
2. In the VM, open File Explorer
3. Open the CD drive
4. Run `VBoxWindowsAdditions.exe`
5. Install with default settings
6. Restart the VM

**This enables:**
- Drag & drop files between host and VM
- Shared clipboard
- Better screen resolution
- Better performance

### Step 6: Test Your Installer

1. **Build your installer** on your main PC:
   ```powershell
   python build_installer.py
   ```

2. **Copy installer to VM:**
   - Method A: Drag & drop into VM window (after Guest Additions)
   - Method B: Use Shared Folder (see below)
   - Method C: Upload to cloud, download in VM

3. **Run installer in VM:**
   - Install AutoFolder AI
   - Test all features
   - Test uninstaller

4. **Take a snapshot** (optional but recommended):
   - In VirtualBox: **Machine** → **Take Snapshot**
   - Name it "Clean Windows"
   - You can restore to this state anytime!

### Using Shared Folders (Advanced)

1. In VirtualBox: Select VM → **Settings** → **Shared Folders**
2. Click the folder+ icon
3. **Folder Path:** `C:\Users\Praveen\Downloads\Python Scripts\AutoFolder AI\installer_output`
4. **Folder Name:** `installer`
5. Check: ☑️ Auto-mount
6. Click OK
7. In the VM, access: `\\VBOXSVR\installer`

## Quick Test Workflow

```
1. Make changes to your app
2. Build installer: python build_installer.py
3. Copy to VM (drag & drop or shared folder)
4. Test in VM
5. If issues, restore snapshot to clean state
6. Fix issues and repeat
```

## Snapshot Strategy

**Create snapshots at key points:**
- "Clean Windows" - Right after installing Windows
- "Pre-test" - Before each installer test
- "Installed" - After successful installation

**To restore:** Right-click snapshot → "Restore"

## VirtualBox vs Windows Sandbox Comparison

| Feature | Windows Sandbox | VirtualBox |
|---------|----------------|------------|
| Cost | Free (Pro/Enterprise) | Free (any Windows) |
| Setup Time | 0 min | 30 min first time |
| Speed | Very fast | Good |
| Persistence | None (deleted on close) | Persistent (unless restored) |
| Snapshots | No | Yes |
| Storage | No disk space used | ~20-30 GB used |

## Tips for Faster Testing

1. **Keep the VM running** between tests (don't shut down)
2. **Use snapshots** to quickly restore clean state
3. **Allocate more RAM** if your PC has >8GB (give VM 6-8GB)
4. **Enable 3D acceleration** in VM settings for better performance

## System Requirements

Your PC needs:
- **RAM:** 
  - Minimum: 6GB total (2GB for VM + 4GB for your PC)
  - Recommended: 8GB+ total (4GB for VM + 4GB for your PC)
- **Storage (Internal SSD):** 
  - Option A (Internal): 50GB free space
  - Option B (External): 10GB free (VM on external HDD)
- **CPU:** Intel VT-x or AMD-V enabled in BIOS (usually enabled by default)
- **External HDD (if using):** USB 3.0 or faster recommended for decent performance

## RAM Allocation Guide

| Your PC RAM | Give to VM | Your PC Gets | Performance |
|-------------|-----------|--------------|-------------|
| 4GB | 2GB | 2GB | Slow but works |
| 8GB | 2-3GB | 5-6GB | Good |
| 8GB | 4GB | 4GB | Better for VM |
| 16GB+ | 4-6GB | 10-12GB | Excellent |

**For 2GB VM:**
- ✅ Can install Windows 11
- ✅ Can test your installer
- ⚠️ Will be slower
- ⚠️ Windows may show low memory warnings
- ⚠️ Close other programs on your PC

---

**VirtualBox is the best free alternative to Windows Sandbox!**
