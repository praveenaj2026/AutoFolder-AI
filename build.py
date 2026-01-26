"""
AutoFolder AI - Build Script
Automated build process for creating Windows EXE distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _run(cmd: list[str], *, check: bool = True):
    return subprocess.run(cmd, check=check)


def _pip_install_requirements():
    print("\n📦 Installing/updating requirements...")
    _run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"], check=True)

    # PyInstaller is incompatible with the obsolete pathlib backport.
    # If it was installed previously, remove it to avoid build failure.
    _run([sys.executable, "-m", "pip", "uninstall", "-y", "pathlib"], check=False)


def _ensure_local_model_cache() -> Path:
    """Download/copy the AI model into ./models so PyInstaller can bundle it."""
    models_root = PROJECT_ROOT / "models"
    models_root.mkdir(parents=True, exist_ok=True)

    print("\n🤖 Caching AI model into local ./models ...")
    from sentence_transformers import SentenceTransformer

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Loading model: {model_name}")

    # Force a local cache folder so the build is reproducible.
    SentenceTransformer(
        model_name,
        cache_folder=str(models_root),
    )
    print(f"✅ AI model cached under: {models_root}")
    return models_root


def _check_tesseract_installer():
    installer = PROJECT_ROOT / "tesseract-ocr-w64-setup-5.5.0.20241111.exe"
    if installer.exists():
        size_mb = installer.stat().st_size / (1024 * 1024)
        print(f"✅ Found Tesseract installer: {installer.name} ({size_mb:.1f} MB)")
    else:
        print("⚠️ Tesseract installer not found in project root.")
        print("   If you want OCR install from inside the EXE, copy it here:")
        print(f"   {installer}")

def main():
    print("=" * 60)
    print("AutoFolder AI - Build Script")
    print("=" * 60)
    
    # 1. Install requirements (fully automated build environment)
    _pip_install_requirements()

    # 2. Ensure local AI model cache exists for bundling
    try:
        _ensure_local_model_cache()
    except Exception as e:
        print(f"⚠️ Warning: Could not pre-cache AI model into ./models: {e}")
        print("   Build will still proceed, but the EXE may lack offline AI.")

    # 3. Check Tesseract installer for in-app install
    _check_tesseract_installer()
    
    # 4. Clean previous build
    print("\n🧹 Cleaning previous build...")
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"✅ Cleaned {folder}/")
    
    # 5. Ensure resources exist
    print("\n🎨 Checking resources...")
    resources_folder = Path('resources/folder_icons')
    if resources_folder.exists():
        icon_count = len(list(resources_folder.glob('*.ico')))
        print(f"✅ Found {icon_count} folder icons")
    else:
        print("⚠️ Warning: No folder icons found. They will be generated at runtime.")
    
    # 6. Run PyInstaller
    print("\n🔨 Building EXE with PyInstaller...")
    print("This may take 5-10 minutes...")
    
    try:
        _run([
            sys.executable,
            "-m",
            "PyInstaller",
            "autofolder.spec",
            "--clean",
            "--noconfirm",
        ], check=True)
        
        print("\n" + "=" * 60)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 60)
        
        dist_folder = Path('dist/AutoFolder AI')
        if dist_folder.exists():
            exe_path = dist_folder / 'AutoFolder AI.exe'
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\n📦 Executable created:")
                print(f"   Location: {exe_path}")
                print(f"   Size: {size_mb:.1f} MB")
                
                print(f"\n📂 Distribution folder:")
                print(f"   Location: {dist_folder}")
                
                print("\n🚀 Next steps:")
                print("   1. Test the EXE: dist/AutoFolder AI/AutoFolder AI.exe")
                print("   2. The entire 'dist/AutoFolder AI' folder is your distribution")
                print("   3. Zip the folder for distribution")
                print("   4. Users just need to extract and run!")

                print("\n📄 OCR (Tesseract):")
                print("   - The Tesseract installer is bundled (if present in project root).")
                print("   - Users can install it from Tools → Install OCR (Tesseract).")
                
            else:
                print(f"⚠️ Warning: EXE not found at expected location")
        else:
            print(f"⚠️ Warning: Distribution folder not found")
            
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("❌ BUILD FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print("\nCommon issues:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Antivirus blocking: Add project folder to exclusions")
        print("  - Insufficient disk space: Need ~500MB free")
        sys.exit(1)

if __name__ == "__main__":
    main()
