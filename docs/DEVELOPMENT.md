# AutoFolder AI - Development Guide

## Project Structure

```
AutoFolder AI/
├── config/              # Configuration files
│   └── default_config.yaml
├── src/
│   ├── main.py          # Application entry point
│   ├── core/            # Core file organization engine
│   │   ├── organizer.py      # Main organizer logic
│   │   ├── rules.py          # Rule engine and profiles
│   │   ├── file_analyzer.py  # File metadata extraction
│   │   └── undo_manager.py   # Undo/redo functionality
│   ├── ai/              # AI classification (local models)
│   │   └── classifier.py
│   ├── ui/              # PySide6 user interface
│   │   └── main_window.py
│   ├── profiles/        # Profile management
│   │   └── profile_manager.py
│   └── utils/           # Utilities
│       ├── config_manager.py
│       └── logger.py
├── tests/               # Unit tests
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure the Application

Edit `config/default_config.yaml` to customize:
- Default folder locations
- Safety settings
- AI model preferences
- UI preferences

### 3. Run the Application

```bash
python src/main.py
```

## Development Workflow

### Adding a New Organization Rule

1. Edit `src/core/rules.py`
2. Add rule to appropriate profile in `_load_profiles()`
3. Example:

```python
{
    'name': 'Videos',
    'type': 'extension',
    'patterns': ['.mp4', '.avi', '.mkv'],
    'target_folder': 'Videos'
}
```

### Creating Custom Profiles

Profiles define how files are categorized. Available rule types:

- **extension**: Match by file extension
- **name_pattern**: Match by regex pattern in filename
- **date_range**: Match by file modification date
- **size_range**: Match by file size

### Enabling AI Features (Pro Version)

1. Set `ai.enabled: true` in config
2. Ensure sentence-transformers is installed
3. First run will download the model (~90MB)
4. Model is cached locally for offline use

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_organizer.py
```

### Manual Testing Workflow

1. Create a test folder with sample files
2. Run AutoFolder AI
3. Select test folder
4. Click "Analyze" to preview
5. Click "Organize" to execute
6. Test "Undo" functionality

## Building for Distribution

### Create Standalone EXE

```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Build EXE (one-file bundle)
pyinstaller --onefile --windowed --name="AutoFolder_AI" --icon=icon.ico src/main.py

# Output will be in dist/AutoFolder_AI.exe
```

### Build Configuration

For custom build, create `autofolder.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config')],
    hiddenimports=['sentence_transformers', 'torch'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
```

## Architecture Details

### Core Organizer Flow

1. **Analyze Folder**: Scan and categorize files
2. **Preview**: Generate list of planned operations
3. **Organize**: Execute file moves
4. **Undo**: Revert operations from journal

### Safety Mechanisms

- **Preview Mode**: Always show what will happen
- **Dry Run**: Test without moving files
- **Undo Journal**: Track all operations for reversal
- **Conflict Resolution**: Handle duplicate filenames
- **Never Delete**: Files are moved, never deleted

### AI Integration

The AI classifier uses local sentence transformers:

1. Extract file metadata (name, extension, content preview)
2. Create semantic embedding
3. Compare with category embeddings
4. Return best match above confidence threshold

**Benefits:**
- Fully offline
- No API costs
- Privacy-preserving
- Fast inference (<100ms per file)

## Performance Optimization

### For Large Folders

- Process in batches (1000 files at a time)
- Use threading for I/O operations
- Cache AI embeddings for repeated analyses

### Memory Management

- Lazy load file contents
- Stream large files
- Clear preview data after organization

## Troubleshooting

### Common Issues

**Issue**: AI model download fails
**Solution**: Download manually from Hugging Face and place in `../AI Model/`

**Issue**: Permission errors when moving files
**Solution**: Run as administrator or check folder permissions

**Issue**: UI freezes during organization
**Solution**: Ensure background threading is enabled

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Document all public methods
- Keep functions focused and small

### Commit Guidelines

- Use clear, descriptive commit messages
- Reference issues when applicable
- Test before committing

## License & Distribution

This is a commercial product. See LICENSE file for details.

**Distribution Platforms:**
- Gumroad (primary)
- Itch.io (secondary)
- Direct sales

**Pricing Strategy:**
- Base: ₹499 (rule-based only)
- Pro: ₹1,299 (with AI features)

---

For questions or support during development, check the project documentation or create an issue.
