"""
Rescue Misplaced System Folders

This script automatically detects and moves system folders (Desktop, Documents, etc.)
that were incorrectly organized into category folders back to the root.

This fixes the issue where Desktop folder ended up in Code folder.
"""

import shutil
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def rescue_misplaced_folders(root_path: Path):
    """
    Scan for misplaced system folders and move them back to root.
    
    Args:
        root_path: Root path to scan (e.g., D:\)
    """
    # CRITICAL system folders that should NEVER be in category folders
    system_folders = [
        'Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos',
        'AppData', 'Application Data', 'Local Settings',
        'Contacts', 'Favorites', 'Links', 'Saved Games', 'Searches',
        'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
        'System32', 'SysWOW64', '$Recycle.Bin', 'Recovery'
    ]
    
    # Category folders where system folders might have been incorrectly moved
    category_folders = [
        'Code', 'Documents', 'Images', 'Videos', 'Audio', 'Archives',
        'Installers', 'Gaming', 'Other', 'Compressed', 'Databases'
    ]
    
    rescued = []
    
    print("=" * 70)
    print(f"SCANNING: {root_path}")
    print("=" * 70)
    
    for category in category_folders:
        category_path = root_path / category
        
        if not category_path.exists() or not category_path.is_dir():
            continue
        
        print(f"\nChecking {category}/ ...")
        
        # Scan subdirectories
        try:
            for item in category_path.iterdir():
                if not item.is_dir():
                    continue
                
                # Is this a misplaced system folder?
                if item.name in system_folders:
                    target = root_path / item.name
                    
                    print(f"  🚨 FOUND MISPLACED: {item.name}")
                    print(f"     Current location: {category}\\{item.name}")
                    print(f"     Should be at: {target}")
                    
                    # Check if target already exists
                    if target.exists():
                        print(f"     ⚠️  SKIPPED: {item.name} already exists at root")
                        print(f"        Manual merge required!")
                        continue
                    
                    # Count files for confirmation
                    try:
                        file_count = len(list(item.rglob('*')))
                        print(f"     Contains: {file_count:,} items")
                    except:
                        print(f"     Contains: Unknown number of items")
                    
                    # Ask for confirmation
                    confirm = input(f"\n     Move {item.name} back to root? (yes/no): ").strip().lower()
                    
                    if confirm == 'yes':
                        try:
                            print(f"     Moving...")
                            shutil.move(str(item), str(target))
                            rescued.append(item.name)
                            print(f"     ✅ SUCCESS: {item.name} rescued!")
                        except Exception as e:
                            print(f"     ❌ FAILED: {e}")
                    else:
                        print(f"     ⏭️  Skipped")
                        
        except PermissionError:
            print(f"  ⚠️  Permission denied for {category}/")
        except Exception as e:
            print(f"  ❌ Error scanning {category}/: {e}")
    
    print("\n" + "=" * 70)
    print("RESCUE COMPLETE")
    print("=" * 70)
    
    if rescued:
        print(f"\n✅ Successfully rescued {len(rescued)} folders:")
        for folder in rescued:
            print(f"   ✓ {folder}")
        print(f"\n🎉 Folders have been moved back to {root_path}")
    else:
        print("\n✓ No misplaced system folders found.")
    
    return rescued

def main():
    print("=" * 70)
    print("RESCUE MISPLACED SYSTEM FOLDERS")
    print("=" * 70)
    print()
    print("This script will scan for system folders (Desktop, Documents, etc.)")
    print("that were incorrectly moved into category folders (Code, Archives, etc.)")
    print("and move them back to the root.")
    print()
    
    # Get path from user
    path_input = input("Enter path to scan (e.g., D:\\ or leave empty for current directory): ").strip()
    
    if not path_input:
        root_path = Path.cwd()
    else:
        root_path = Path(path_input)
    
    if not root_path.exists():
        print(f"\n❌ Error: Path not found: {root_path}")
        return
    
    if not root_path.is_dir():
        print(f"\n❌ Error: Not a directory: {root_path}")
        return
    
    print(f"\n📂 Scanning: {root_path}")
    confirm = input("\nProceed? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    # Run rescue
    rescued = rescue_misplaced_folders(root_path)
    
    print("\n✅ Rescue operation complete!")
    print("\nYou can now safely re-run AutoFolder AI organization.")

if __name__ == '__main__':
    main()
