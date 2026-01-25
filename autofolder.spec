# -*- mode: python ; coding: utf-8 -*-
"""
AutoFolder AI - PyInstaller Spec File
Creates standalone Windows EXE with all dependencies bundled
"""

import os
import sys
from pathlib import Path

# Get project root
project_root = Path(os.path.abspath(SPECPATH))


def _safe_add_data(datas_list, src, dst):
    try:
        src_path = Path(src)
        if src_path.exists():
            datas_list.append((str(src_path), dst))
    except Exception:
        # Skip bundling rather than failing the build.
        pass


datas = [
    # Configuration files
    ('config/default_config.yaml', 'config'),

    # Resources
    ('resources/folder_icons/*.ico', 'resources/folder_icons'),
]

# Bundle local AI model cache (preferred, created by build.py)
_safe_add_data(datas, project_root / 'models', 'models')

# Bundle Tesseract installer if present
_safe_add_data(
    datas,
    project_root / 'tesseract-ocr-w64-setup-5.5.0.20241111.exe',
    'third_party',
)

block_cipher = None

# Collect all Python source files
a = Analysis(
    ['src/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'sentence_transformers',
        'torch',
        'numpy',
        'sklearn',
        'scipy',
        'PIL',
        'pytesseract',
        'yaml',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'watchdog',
        'dateutil',
        'humanize',
        'magic',
        'PyPDF2',
        'filetype',
        'pydantic',
        'pydantic_core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'IPython',
        'notebook',
        'jupyter',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoFolder AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app_icon.ico' if Path('resources/app_icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoFolder AI',
)
