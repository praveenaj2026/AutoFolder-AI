"""
Remove date folder layer - Move files from date folders to parent, then delete empty date folders.

This script:
1. Finds all date folders (Jan-26, Nov-25, etc.)
2. Moves all files FROM date folder TO parent folder
3. Deletes the now-empty date folders

Example:
  D:/Documents/PDF/Jan-26/report.pdf  ->  D:/Documents/PDF/report.pdf
  D:/Code/PY/Nov-25/script.py         ->  D:/Code/PY/script.py
"""

import sys
import shutil
from pathlib import Path
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Date folder patterns (e.g., "Jan-26", "Nov-25", "Dec-24")
DATE_FOLDER_PATTERN = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$')

def is_date_folder(folder_name: str) -> bool:
    """Check if folder name matches date pattern."""
    return bool(DATE_FOLDER_PATTERN.match(folder_name))

def get_unique_path(target_path: Path) -> Path:
    """Get unique path by adding (1), (2), etc. if file exists."""
    if not target_path.exists():
        return target_path
    
    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    counter = 1
    
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
        if counter > 1000:
            return None

def flatten_date_folders(root_path: Path, dry_run=True):
    """
    Flatten date folder structure by moving files to parent.
    
    Args:
        root_path: Root folder to scan
        dry_run: If True, only show what would be done
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Flattening date folder structure in: {root_path}")
    
    if not root_path.exists():
        logger.error(f"❌ Folder does not exist: {root_path}")
        return
    
    # Find all date folders
    date_folders = []
    for folder in root_path.rglob('*'):
        if folder.is_dir() and is_date_folder(folder.name):
            date_folders.append(folder)
    
    logger.info(f"Found {len(date_folders)} date folders to process")
    
    # Process each date folder
    files_moved = 0
    folders_removed = 0
    conflicts = 0
    errors = 0
    
    # Sort by depth (deepest first) to handle nested structures
    date_folders.sort(key=lambda p: len(p.parts), reverse=True)
    
    for date_folder in date_folders:
        parent_folder = date_folder.parent
        logger.info(f"\n📁 Processing: {date_folder.relative_to(root_path)}")
        
        # Get all files in this date folder
        try:
            files_in_date_folder = list(date_folder.rglob('*'))
            files_in_date_folder = [f for f in files_in_date_folder if f.is_file()]
            
            if not files_in_date_folder:
                logger.info(f"   ⏭️ Empty folder, will be removed")
                if not dry_run:
                    try:
                        date_folder.rmdir()
                        folders_removed += 1
                    except Exception as e:
                        logger.error(f"   ❌ Failed to remove: {e}")
                        errors += 1
                else:
                    folders_removed += 1
                continue
            
            logger.info(f"   📦 Contains {len(files_in_date_folder)} files")
            
            # Move each file to parent folder
            for file_path in files_in_date_folder:
                # Calculate relative path within date folder
                try:
                    rel_path = file_path.relative_to(date_folder)
                except ValueError:
                    continue
                
                # Target is parent folder + relative path
                target_path = parent_folder / rel_path
                
                # Handle conflicts
                if target_path.exists():
                    logger.warning(f"   ⚠️ Conflict: {file_path.name} already exists in parent")
                    target_path = get_unique_path(target_path)
                    if target_path is None:
                        logger.error(f"   ❌ Too many conflicts for: {file_path.name}")
                        conflicts += 1
                        continue
                    logger.info(f"   🔄 Will rename to: {target_path.name}")
                
                logger.info(f"   {'[DRY RUN] Would move' if dry_run else '📤 Moving'}: {file_path.name} → {parent_folder.name}/")
                
                if not dry_run:
                    try:
                        # Create target directory if needed
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(target_path))
                        files_moved += 1
                    except Exception as e:
                        logger.error(f"   ❌ Failed to move {file_path.name}: {e}")
                        errors += 1
                else:
                    files_moved += 1
            
            # Remove date folder after moving all files
            if not dry_run:
                try:
                    # Check if empty after moving files
                    if not any(date_folder.iterdir()):
                        date_folder.rmdir()
                        logger.info(f"   🗑️ Removed empty date folder")
                        folders_removed += 1
                    else:
                        logger.warning(f"   ⚠️ Folder not empty after moving files (has subfolders?)")
                        # Try to remove recursively
                        shutil.rmtree(date_folder)
                        logger.info(f"   🗑️ Removed date folder (recursive)")
                        folders_removed += 1
                except Exception as e:
                    logger.error(f"   ❌ Failed to remove folder: {e}")
                    errors += 1
            else:
                folders_removed += 1
        
        except Exception as e:
            logger.error(f"   ❌ Error processing folder: {e}")
            errors += 1
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("FLATTEN SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📦 {'Would move' if dry_run else 'Moved'}: {files_moved} files")
    logger.info(f"🗑️ {'Would remove' if dry_run else 'Removed'}: {folders_removed} date folders")
    logger.info(f"⚠️ Conflicts: {conflicts}")
    logger.info(f"❌ Errors: {errors}")
    logger.info("")
    
    if dry_run and files_moved > 0:
        logger.info("⚠️ This was a DRY RUN. No changes were made.")
        logger.info("⚠️ To actually flatten folders, run with dry_run=False")

def main():
    """Main script."""
    print("=" * 60)
    print("DATE FOLDER FLATTENING TOOL")
    print("=" * 60)
    print("This will:")
    print("  1. Find all date folders (Jan-26, Nov-25, etc.)")
    print("  2. Move files FROM date folders TO parent folders")
    print("  3. Delete empty date folders")
    print()
    print("Example:")
    print("  D:/Documents/PDF/Jan-26/report.pdf")
    print("  -> D:/Documents/PDF/report.pdf")
    print("=" * 60)
    print()
    
    # Get target folder
    if len(sys.argv) > 1:
        target_folder = Path(sys.argv[1])
    else:
        folder_input = input("Enter folder path to flatten (e.g., D:/): ").strip()
        if not folder_input:
            print("No folder specified. Exiting.")
            return
        target_folder = Path(folder_input)
    
    if not target_folder.exists():
        print(f"❌ Folder does not exist: {target_folder}")
        return
    
    print(f"\n📁 Target folder: {target_folder.absolute()}")
    print()
    
    # DRY RUN first
    print("=" * 60)
    print("STEP 1: DRY RUN (preview changes)")
    print("=" * 60)
    print()
    
    flatten_date_folders(target_folder, dry_run=True)
    
    # Ask for confirmation
    print()
    response = input("\n⚠️ Do you want to ACTUALLY FLATTEN these folders? (type 'yes' to confirm): ").strip().lower()
    
    if response != 'yes':
        print("❌ Flattening cancelled. No changes were made.")
        return
    
    # ACTUAL FLATTEN
    print()
    print("=" * 60)
    print("STEP 2: FLATTENING (moving files and removing date folders)")
    print("=" * 60)
    print()
    
    flatten_date_folders(target_folder, dry_run=False)
    
    print()
    print("✅ Flattening complete!")
    print()

if __name__ == "__main__":
    main()
