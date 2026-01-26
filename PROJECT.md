# AutoFolder AI - Project Overview

**Version:** 1.0 (Release Candidate)  
**Status:** Ready for build and VM testing  
**Last Updated:** January 26, 2026

---

## Quick Links

### Essential Documentation
- **[README.md](README.md)** - Project overview and features
- **[QUICKSTART.md](QUICKSTART.md)** - Get started quickly
- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - How to build the EXE
- **[LICENSE](LICENSE)** - MIT License

### Testing & Distribution
- **[docs/v1.0/DISTRIBUTION.md](docs/v1.0/DISTRIBUTION.md)** - v1.0 testing plan and release strategy
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures
- **[docs/VIRTUALBOX_TESTING_GUIDE.md](docs/VIRTUALBOX_TESTING_GUIDE.md)** - VM testing instructions
- **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** - Quick validation tests

### Future Development
- **[docs/v2.0/ARCHITECTURE.md](docs/v2.0/ARCHITECTURE.md)** - v2.0 core redesign architecture
- **[TODO.md](TODO.md)** - Current task list

### Developer Guides
- **[docs/BUILDING.md](docs/BUILDING.md)** - Detailed build instructions
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development setup
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - End-user documentation

### Archived Documentation
- **[docs/archive/](docs/archive/)** - Historical progress docs and phase notes
- **[docs/reference/](docs/reference/)** - Reference materials and analysis files

---

## Project Structure

```
AutoFolder AI/
├── src/                    # Source code
│   ├── main.py            # Entry point
│   ├── ai/                # AI classifier
│   ├── core/              # Core organizer logic
│   ├── profiles/          # Organization profiles
│   ├── ui/                # PySide6 GUI
│   └── utils/             # Utilities
├── config/                 # Configuration files
├── docs/                   # Documentation
│   ├── v1.0/              # v1.0 distribution docs
│   ├── v2.0/              # v2.0 architecture
│   ├── archive/           # Historical docs
│   └── reference/         # Reference materials
├── scripts/                # Utility scripts
│   ├── cleanup/           # File cleanup utilities
│   └── *.py               # Build and setup scripts
├── tests/                  # Test suite
├── resources/              # Icons and assets
├── models/                 # AI model cache (gitignored)
├── build.py               # Automated build script
├── autofolder.spec        # PyInstaller spec
└── requirements.txt       # Python dependencies
```

---

## Current Status

### ✅ Completed (v1.0)
- Multi-pass file scanning and analysis
- Rule-based classification (extensions + content)
- AI-powered semantic grouping (offline model)
- Duplicate detection
- PySide6 GUI with progress feedback
- Undo/redo system with persistent history
- Windows folder icon customization
- Archive compression support
- PyInstaller EXE bundling
- Configuration system

### 🏗️ In Progress
- VM testing (VirtualBox/Windows Sandbox)
- Beta testing with real users
- Performance optimization
- Documentation refinement

### 📋 Planned (v2.0)
- Unified deep scan (single-pass)
- Root detection and protection
- Context-aware AI (uses folder names)
- Rule-first pipeline
- Smart placement resolver
- Improved safety invariants
- See [docs/v2.0/ARCHITECTURE.md](docs/v2.0/ARCHITECTURE.md) for full plan

---

## Quick Start

### For Users
1. Download `AutoFolder AI.exe` from releases
2. Run the EXE (no installation needed)
3. Select folder to organize
4. Review preview
5. Click "Organize"
6. Use undo if needed

### For Developers
```powershell
# Clone repository
git clone <repository-url>
cd "AutoFolder AI"

# Install dependencies
pip install -r requirements.txt

# Run from source
python src/main.py

# Build EXE
python build.py
```

---

## Key Features

### 🎯 Smart Organization
- **Rule-based:** Fast classification by extension and content
- **AI-powered:** Semantic grouping for unknown file types
- **Context-aware:** Understands folder relationships
- **Duplicate detection:** Finds and groups identical files

### 🛡️ Safety First
- **Undo system:** Every operation reversible
- **Preview mode:** See changes before applying
- **No overwrites:** Safe file handling
- **Atomic moves:** All-or-nothing operations

### 🎨 User Experience
- **Modern GUI:** Clean PySide6 interface
- **Progress feedback:** Real-time status updates
- **Custom icons:** Beautiful folder icons in Explorer
- **Offline mode:** No internet required

### ⚡ Performance
- **Offline AI:** Bundled sentence-transformers model
- **Fast scanning:** Optimized file traversal
- **Compression:** Archive old files to save space
- **Configurable:** Tune behavior via YAML config

---

## Technology Stack

- **Language:** Python 3.10+
- **GUI:** PySide6 (Qt6)
- **AI:** sentence-transformers (all-MiniLM-L6-v2)
- **ML:** PyTorch, scikit-learn
- **Packaging:** PyInstaller
- **Config:** PyYAML
- **Testing:** pytest

---

## Distribution Strategy

### v1.0 - Internal Validation
- ✅ Build standalone EXE
- ✅ Test in clean VM
- ✅ Beta test with 5-10 users
- ❌ **NOT for public sale**
- Purpose: Verify stability, collect feedback

### v2.0 - Public Release
- ✅ Implement core architecture redesign
- ✅ Root protection system
- ✅ Context-aware AI
- ✅ Full safety invariants
- ✅ Consider paid distribution (₹399-₹699)

See [docs/v1.0/DISTRIBUTION.md](docs/v1.0/DISTRIBUTION.md) for details.

---

## Contributing

This is currently a personal project by Praveen with AI assistance from GitHub Copilot (Claude Sonnet 4.5).

Future collaboration welcome after v1.0 validation.

---

## Known Issues (v1.0)

### Architectural Limitations
1. **Shallow scanning** - Uses multi-pass instead of single deep scan
2. **No root protection** - May move files out of project folders
3. **Context-blind AI** - Doesn't use folder names for grouping
4. **Aggressive folders** - Sometimes creates folders for 1-2 files
5. **Tree flattening** - May lose original folder structure in some cases

**Workaround:** Use undo if incorrect moves occur. Test on copies first.

**Fix:** v2.0 architecture addresses all these issues. See [docs/v2.0/ARCHITECTURE.md](docs/v2.0/ARCHITECTURE.md).

---

## Support

- **Issues:** Document in GitHub Issues (after repository setup)
- **Bugs:** Report with logs from `logs/autofolder.log`
- **Feature Requests:** Add to [TODO.md](TODO.md)
- **Questions:** Contact Praveen directly

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Developed with GitHub Copilot (Claude Sonnet 4.5)
- Built with open-source Python ecosystem
- Icons and UI inspired by Windows 11 design

---

**Next Action:** Build v1.0 EXE and start VM testing!

```powershell
python build.py
```
