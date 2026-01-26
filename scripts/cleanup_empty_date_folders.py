"""
Clean up empty date folders (Jan-26, Nov-25, etc.) from organized drives.

This script finds and removes empty date-based subfolders that were created
by the old organization logic but are no longer needed.
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

def is_folder_empty(folder_path: Path) -> bool:
    """Check if folder is completely empty (no files, no subfolders)."""
    try:
        return not any(folder_path.iterdir())
    except (PermissionError, OSError):
        return False

def find_and_remove_empty_date_folders(root_path: Path, dry_run=True):
    """
    Find and remove empty date folders recursively.
    
    Args:
        root_path: Root folder to scan
        dry_run: If True, only show what would be deleted (don't actually delete)
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Scanning for empty date folders in: {root_path}")
    
    if not root_path.exists():
        logger.error(f"❌ Folder does not exist: {root_path}")
        return
    
    # Find all date folders
    date_folders = []
    for folder in root_path.rglob('*'):
        if folder.is_dir() and is_date_folder(folder.name):
            date_folders.append(folder)
    
    logger.info(f"Found {len(date_folders)} date folders to check")
    
    # Remove empty date folders (bottom-up to handle nested folders)
    removed_count = 0
    skipped_count = 0
    
    # Sort by depth (deepest first) to remove nested folders first
    date_folders.sort(key=lambda p: len(p.parts), reverse=True)
    
    for folder in date_folders:
        if is_folder_empty(folder):
            logger.info(f"{'[DRY RUN] Would remove' if dry_run else '🗑️ Removing'}: {folder}")
            
            if not dry_run:
                try:
                    folder.rmdir()  # Only removes if empty
                    removed_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to remove {folder}: {e}")
                    skipped_count += 1
            else:
                removed_count += 1
        else:
            logger.debug(f"⏭️ Skipping (not empty): {folder}")
            skipped_count += 1
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("CLEANUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ {'Would remove' if dry_run else 'Removed'}: {removed_count} empty date folders")
    logger.info(f"⏭️ Skipped: {skipped_count} non-empty folders")
    logger.info("")
    
    if dry_run and removed_count > 0:
        logger.info("⚠️ This was a DRY RUN. No folders were actually deleted.")
        logger.info("⚠️ To actually delete folders, run with dry_run=False")

def main():
    """Main cleanup script."""
    print("=" * 60)
    print("EMPTY DATE FOLDER CLEANUP TOOL")
    print("=" * 60)
    print()
    
    # Get target folder from user
    if len(sys.argv) > 1:
        target_folder = Path(sys.argv[1])
    else:
        folder_input = input("Enter folder path to clean (e.g., D:\\): ").strip()
        if not folder_input:
            print("❌ No folder specified. Exiting.")
            return
        target_folder = Path(folder_input)
    
    if not target_folder.exists():
        print(f"❌ Folder does not exist: {target_folder}")
        return
    
    # Confirm with user
    print(f"\n📁 Target folder: {target_folder.absolute()}")
    print("🔍 This will find and remove ALL empty date folders (Jan-26, Nov-25, etc.)")
    print()
    
    # DRY RUN first
    print("=" * 60)
    print("STEP 1: DRY RUN (preview what would be deleted)")
    print("=" * 60)
    print()
    
    find_and_remove_empty_date_folders(target_folder, dry_run=True)
    
    # Ask for confirmation
    print()
    response = input("\n⚠️ Do you want to ACTUALLY DELETE these folders? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cleanup cancelled. No folders were deleted.")
        return
    
    # ACTUAL CLEANUP
    print()
    print("=" * 60)
    print("STEP 2: ACTUAL CLEANUP (deleting empty folders)")
    print("=" * 60)
    print()
    
    find_and_remove_empty_date_folders(target_folder, dry_run=False)
    
    print()
    print("✅ Cleanup complete!")
    print()

if __name__ == "__main__":
    main()
