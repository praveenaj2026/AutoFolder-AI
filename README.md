# AutoFolder AI

**Smart File Organization for Windows**

AutoFolder AI is a powerful, AI-assisted file organizer that helps you automatically clean and organize your folders with intelligent categorization.

## ✨ Key Features

### Phase 3.7 - Current Version
- ✅ **Content-Based AI**: Analyze PDF contents to detect document types (Resume, Invoice, Contract, etc.)
- ✅ **Smart Compression**: Compress old/large files to save storage space
- ✅ **AI Learning**: Track corrections to improve accuracy over time
- ✅ **21 File Categories**: Extended support for Spreadsheets, Databases, Ebooks, Fonts, CAD, 3D Models, and more
- ✅ **Smart Preview Table**: Organized by filename first with intelligent column sizing
- ✅ **Duplicate Scanner**: Find and handle duplicate files with OneDrive error reporting
- ✅ **Search Engine**: Find files by name or folder path with 4-column results
- ✅ **Statistics Dashboard**: 5-card summary with category and file type breakdowns
- ✅ **Undo Support**: Safely revert your last organization
- ✅ **Profiles**: Pre-built templates (Downloads, Media, Work Files, etc.)
- ✅ **100% Offline**: No data leaves your PC

### Removed Features (Simplified)
- ❌ Edit AI Groups - Removed for simplicity (complex UI, rarely used)
- ❌ Auto Schedule - Removed due to Windows Task Scheduler complexity

## 🎯 Target Use Cases

1. **Downloads Cleanup**: Automatically organize messy download folders
2. **Media Organization**: Sort photos, videos, and screenshots
3. **Game Files**: Organize recordings, mods, saves, and screenshots
4. **Developer Workspace**: Clean up logs, builds, and project files

## 🛡️ Safety First

- **Preview Before Apply**: Always see what will happen
- **Dry Run Mode**: Test without moving files
- **Undo Journal**: Revert any operation
- **Conflict Detection**: Never overwrite files accidentally
- **No Deletion**: Files are moved, never deleted

## 🏗️ Architecture

```
AutoFolder AI/
├── src/
│   ├── core/           # File organization engine
│   ├── ai/             # Local AI models integration
│   ├── ui/             # PySide6 interface
│   ├── profiles/       # Predefined organization profiles
│   └── utils/          # Helper functions
├── models/             # Local AI model files (optional)
├── tests/              # Unit and integration tests
└── docs/               # Documentation
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

## 💰 Business Model

- **Base Version**: ₹499 - Rule-based organization
- **Pro Version**: ₹1,299 - AI-powered features
- **One-time purchase** - No subscription
- **No support obligation** - Self-service documentation

## 🔒 Privacy

- All processing happens locally
- No cloud services required
- No data collection
- No analytics or telemetry

## 📦 Distribution

- Portable EXE (no installation required)
- Windows 10/11 compatible
- Single file distribution via PyInstaller

### Optional OCR (Tesseract)

- OCR requires the Tesseract engine.
- The Windows build can bundle the Tesseract installer; users can run it from `Tools → Install OCR (Tesseract)`.
- PowerShell alternative: run [scripts/install_tesseract.ps1](scripts/install_tesseract.ps1) as Administrator.

---

**Current Status**: Development Phase
**Target Release**: Q1 2026
**Developer**: Praveen
