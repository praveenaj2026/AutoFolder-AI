# AutoFolder AI v1.0 — Distribution & Testing Plan

**Status:** Current Release (In Testing)  
**Release Date:** January 2026  
**Target:** Internal validation & VM testing

---

## Release Strategy

### v1.0 Purpose
- ✅ Engineering validation build
- ✅ Packaging stability verification
- ✅ Real-world behavior observation
- ❌ **NOT for public sale**
- ❌ **NOT for mass distribution**

### Acceptable Limitations in v1.0
- Some nested structures may flatten
- Some rare misplacements possible
- AI grouping may be imperfect
- Aggressive folder creation in some cases

### Must-Have Stability
- ✅ No data loss
- ✅ Undo always works
- ✅ No crashes in frozen EXE
- ✅ No permission corruption
- ✅ No overwrites

---

## Build Instructions

### Prerequisites
- Python 3.10+
- ~500MB disk space
- All dependencies installed

### Building EXE

**Automated Build (Recommended):**
```powershell
python build.py
```

This will:
1. Install/update requirements
2. Download AI model to `./models/`
3. Clean previous builds
4. Run PyInstaller with `autofolder.spec`
5. Create `dist/AutoFolder AI/AutoFolder AI.exe`

**Manual Build:**
```powershell
# Clean
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Build
python -m PyInstaller autofolder.spec --clean --noconfirm
```

### Build Output
- **Location:** `dist/AutoFolder AI/`
- **Main EXE:** `AutoFolder AI.exe`
- **Size:** ~500-800 MB (includes PyTorch + AI model)
- **Bundled:**
  - Python runtime
  - PySide6 (Qt GUI)
  - PyTorch + sentence-transformers
  - AI model cache
  - Config files
  - Folder icons

---

## Testing Protocol

### Phase 1: Local Smoke Test (Dev Machine)

**Quick Validation:**
1. Run `dist/AutoFolder AI/AutoFolder AI.exe`
2. Organize small test folder (10-20 files)
3. Verify:
   - ✅ GUI launches without errors
   - ✅ Progress overlay shows status
   - ✅ Files move correctly
   - ✅ Undo works
   - ✅ Icons apply (check in Explorer)
4. Check logs: `logs/autofolder.log`

**Test Scenarios:**
- Mixed file types (docs, images, code)
- Date-stamped files
- Duplicate detection
- AI grouping (unknown extensions)

### Phase 2: VirtualBox Testing (CRITICAL)

**Why VM Testing?**
- Catches missing DLLs
- Validates on clean Windows
- Tests without Python installed
- Verifies AI model bundling
- Tests Explorer integration

**Setup:**
1. Create fresh Windows 10/11 VM
2. **Do NOT install Python**
3. **Do NOT install dependencies**
4. Copy `dist/AutoFolder AI/` folder to VM
5. Run `AutoFolder AI.exe`

**VM Test Cases:**

**Test 1: Downloads Folder**
```
Input: Typical Downloads clutter
- PDFs, images, installers
- Random files with bad names
- Some compressed archives

Expected:
- Documents sorted
- Images grouped
- Installers categorized
- No crashes
```

**Test 2: Photo Archive**
```
Input: Camera dump
- JPG, PNG, raw photos
- Date-stamped filenames
- Some duplicates

Expected:
- AI groups by content
- Date preservation
- Duplicates detected
- Icons applied
```

**Test 3: Code Project**
```
Input: Dev folder with mixed structure
- Python scripts
- Config files
- Random CSVs

Expected:
- Project roots protected (if .git present)
- Scripts organized
- Undo available
```

**Test 4: Stress Test**
```
Input: Large folder
- 500+ files
- Mixed types
- Deep nesting

Expected:
- Completes without crash
- Performance acceptable (<2 min)
- Memory stable
```

### Phase 3: Real-World Testing

**Beta Testers (Friends/Power Users):**
- Provide ZIP of `dist/AutoFolder AI/`
- Instruct: "Test on copy of your data, not originals"
- Collect feedback:
  - What broke?
  - What moved wrong?
  - What confused you?
  - Performance issues?

**Feedback Log:**
Create `docs/v1.0/FEEDBACK.md` and record:
- Wrong placements
- Flattened structures
- AI grouping mistakes
- Root-breaking incidents
- Performance problems

**This feedback becomes gold for v2.0 design**

---

## Known Issues (v1.0)

### Architectural Limitations
1. **Shallow scanning** - Multi-pass instead of single deep scan
2. **No root protection** - May move files out of project folders
3. **Context-blind AI** - Doesn't use folder names for grouping
4. **Aggressive folders** - Creates folders for 1-2 files sometimes
5. **Tree flattening** - May lose original folder structure

### Workarounds
- Use undo if wrong moves occur
- Test on copies first
- Avoid organizing active project folders
- Review preview carefully

### Not Bugs (Expected Behavior)
- Date subfolders may appear (configurable)
- Some files stay "Uncategorized" (AI needs ≥3 similar files)
- Icons may take a few seconds to appear

---

## Distribution Checklist

### Before Packaging
- [ ] Clean build (`build.py`)
- [ ] Test EXE on dev machine
- [ ] Check logs for errors
- [ ] Verify AI model bundled
- [ ] Test undo functionality

### VM Testing
- [ ] Fresh Windows VM ready
- [ ] No Python installed in VM
- [ ] Test 4 scenarios above
- [ ] Document any crashes/errors
- [ ] Verify Explorer icons work

### Beta Distribution
- [ ] Create ZIP of `dist/AutoFolder AI/`
- [ ] Write usage instructions
- [ ] Set up feedback collection
- [ ] Warn: "Test on copies only"
- [ ] Provide direct contact for issues

### Post-Testing
- [ ] Analyze feedback
- [ ] Update known issues list
- [ ] Record v2.0 improvement ideas
- [ ] Decide on public release readiness

---

## When to Consider Public Release

### v1.x Must Be Stable:
- ✅ 10+ successful VM tests
- ✅ 5+ beta users with no data loss
- ✅ All critical bugs fixed
- ✅ Undo verified in all scenarios
- ✅ Performance acceptable

### v2.0 Should Be Complete:
- ✅ Root protection implemented
- ✅ Context-aware AI working
- ✅ Single-pass deep scan
- ✅ Side-by-side testing passed
- ✅ No regressions from v1

**Recommendation:** Wait for v2.0 before paid distribution

---

## Installer (Optional for v1.0)

**Inno Setup Available:**
- `innosetup-6.7.0.exe` in project root
- Can create proper Windows installer
- Adds Start Menu shortcuts
- Uninstaller included

**For v1.0 Internal Testing:**
- ZIP distribution is fine
- No installer needed
- Easier to update
- Simpler to test

**For v2.0 Public Release:**
- Create proper installer
- Sign with certificate (optional)
- Add auto-update check
- Include license agreement

---

## Success Metrics

### v1.0 Validation Goals:
- [ ] 20+ organize operations without data loss
- [ ] 0 crashes in VM testing
- [ ] Undo success rate: 100%
- [ ] User satisfaction: "It works, some quirks"

### Data to Collect:
- Average organize time
- Most common file types
- Most common misplacements
- AI grouping accuracy
- User confusion points

---

## Next Steps

1. **Build v1.0 EXE** → `python build.py`
2. **Test locally** → Smoke test on small folder
3. **VM testing** → Fresh Windows, 4 test scenarios
4. **Beta distribution** → 3-5 trusted users
5. **Collect feedback** → Log issues and improvements
6. **Plan v2.0** → Based on real-world data

---

**Current Status:** Ready for build and VM testing  
**Blocker:** None  
**Risk Level:** Low (internal testing only)
