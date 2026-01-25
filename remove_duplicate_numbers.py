"""
Safe script to remove (1) (2) (3) patterns from filenames in Documents folder
"""
import re
from pathlib import Path
from collections import defaultdict

def clean_filename(name: str) -> str:
    """Remove all (1) (2) (3) patterns from filename."""
    stem = Path(name).stem
    ext = Path(name).suffix
    
    # Remove all (number) patterns
    cleaned = stem
    while re.search(r'\s*\(\d+\)\s*', cleaned):
        cleaned = re.sub(r'\s*\(\d+\)\s*', ' ', cleaned)
    
    # Clean up extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return f"{cleaned}{ext}"

def rename_files_safely(folder_path: Path, dry_run: bool = True):
    """
    Rename files to remove (1) patterns.
    
    Args:
        folder_path: Path to folder
        dry_run: If True, only show what would be renamed (no actual changes)
    """
    # Get all files recursively
    all_files = [f for f in folder_path.rglob('*') if f.is_file()]
    
    # Track renames
    renames = []
    skipped = []
    conflicts = defaultdict(list)
    
    print(f"\n{'='*70}")
    print(f"Scanning: {folder_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE MODE (will rename)'}")
    print(f"{'='*70}\n")
    
    for file_path in all_files:
        original_name = file_path.name
        cleaned_name = clean_filename(original_name)
        
        # Skip if no change needed
        if original_name == cleaned_name:
            continue
        
        # Check if cleaned name already exists
        new_path = file_path.parent / cleaned_name
        
        # If file with cleaned name exists, add suffix to avoid conflict
        if new_path.exists() and new_path != file_path:
            stem = Path(cleaned_name).stem
            ext = Path(cleaned_name).suffix
            counter = 1
            while new_path.exists():
                new_name = f"{stem}_{counter}{ext}"
                new_path = file_path.parent / new_name
                counter += 1
            cleaned_name = new_name
            conflicts[original_name].append(f"Renamed to: {cleaned_name}")
        
        renames.append((file_path, new_path, original_name, cleaned_name))
    
    # Show what will be renamed
    print(f"Found {len(renames)} files to rename:\n")
    
    for i, (old_path, new_path, old_name, new_name) in enumerate(renames[:20], 1):
        print(f"{i}. {old_name}")
        print(f"   -> {new_name}")
        print(f"   Location: {old_path.parent}")
        print()
    
    if len(renames) > 20:
        print(f"... and {len(renames) - 20} more files\n")
    
    # Show conflicts (now handled with suffixes)
    if conflicts:
        print(f"\nNote: {len(conflicts)} files had naming conflicts (resolved with _1, _2, etc.):")
        for name, msgs in list(conflicts.items())[:5]:
            print(f"  {name}")
            for msg in msgs:
                print(f"    -> {msg}")
        if len(conflicts) > 5:
            print(f"  ... and {len(conflicts) - 5} more")
    
    # Perform renames if not dry run
    if not dry_run:
        print("\n" + "="*70)
        response = input("Proceed with renaming? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Cancelled.")
            return
        
        print("\nRenaming files...")
        success_count = 0
        error_count = 0
        
        for old_path, new_path, old_name, new_name in renames:
            try:
                old_path.rename(new_path)
                success_count += 1
                print(f"OK: {old_name} -> {new_name}")
            except Exception as e:
                error_count += 1
                print(f"FAILED: {old_name} - {e}")
        
        print(f"\n{'='*70}")
        print(f"Successfully renamed: {success_count} files")
        if error_count > 0:
            print(f"Errors: {error_count} files")
        print(f"{'='*70}")
    else:
        print(f"\n{'='*70}")
        print("DRY RUN COMPLETE - No files were changed")
        print("To actually rename files, run with: python remove_duplicate_numbers.py --live")
        print(f"{'='*70}")

if __name__ == "__main__":
    import sys
    
    # Default to Documents folder
    docs_folder = Path.home() / "OneDrive" / "Documents"
    
    # Check if --live flag is provided
    dry_run = "--live" not in sys.argv
    
    if not docs_folder.exists():
        docs_folder = Path.home() / "Documents"
    
    if not docs_folder.exists():
        print("Error: Documents folder not found!")
        sys.exit(1)
    
    rename_files_safely(docs_folder, dry_run=dry_run)
