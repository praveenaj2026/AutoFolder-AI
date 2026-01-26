"""
Smart script to clean (1) (2) (3) patterns from filenames in Documents folder.
- If original file exists (e.g., "file.pdf" exists), DELETE "file (1).pdf" as duplicate
- If original doesn't exist, RENAME "file (1).pdf" → "file.pdf"
"""
import re
from pathlib import Path
from typing import List, Tuple

def has_number_suffix(name: str) -> bool:
    """Check if filename has (1) (2) (3) pattern."""
    stem = Path(name).stem
    return bool(re.search(r'\s*\(\d+\)\s*', stem))

def remove_number_suffix(name: str) -> str:
    """Remove all (number) patterns from filename."""
    stem = Path(name).stem
    ext = Path(name).suffix
    
    # Remove all (number) patterns
    cleaned = stem
    while re.search(r'\s*\(\d+\)\s*', cleaned):
        cleaned = re.sub(r'\s*\(\d+\)\s*', ' ', cleaned)
    
    # Clean up extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return f"{cleaned}{ext}"

def analyze_files(folder_path: Path) -> Tuple[List, List]:
    """
    Analyze files and determine actions.
    
    Returns:
        (files_to_delete, files_to_rename)
    """
    # Get all files with (number) patterns
    all_files = [f for f in folder_path.rglob('*') 
                 if f.is_file() and has_number_suffix(f.name)]
    
    files_to_delete = []
    files_to_rename = []
    
    for file_path in all_files:
        original_name = file_path.name
        cleaned_name = remove_number_suffix(original_name)
        original_path = file_path.parent / cleaned_name
        
        # If original file exists, mark for deletion (it's a duplicate)
        if original_path.exists() and original_path != file_path:
            files_to_delete.append((file_path, original_name, cleaned_name))
        else:
            # Original doesn't exist, safe to rename
            files_to_rename.append((file_path, original_path, original_name, cleaned_name))
    
    return files_to_delete, files_to_rename

def clean_files(folder_path: Path, dry_run: bool = True):
    """
    Clean duplicate number patterns from files.
    
    Args:
        folder_path: Path to folder
        dry_run: If True, only show what would happen (no actual changes)
    """
    print(f"\n{'='*80}")
    print(f"📁 Scanning: {folder_path}")
    print(f"🔧 Mode: {'🔍 DRY RUN (preview only)' if dry_run else '⚡ LIVE MODE (will make changes)'}")
    print(f"{'='*80}\n")
    
    files_to_delete, files_to_rename = analyze_files(folder_path)
    
    total_actions = len(files_to_delete) + len(files_to_rename)
    
    if total_actions == 0:
        print("✅ No files with (1) (2) (3) patterns found!")
        print("📂 Your Documents folder is already clean.\n")
        return
    
    print(f"📊 Found {total_actions} files to clean:\n")
    print(f"  🗑️  {len(files_to_delete)} files to DELETE (duplicates)")
    print(f"  ✏️  {len(files_to_rename)} files to RENAME (safe to clean)")
    print()
    
    # Show files to delete
    if files_to_delete:
        print(f"🗑️  FILES TO DELETE (originals exist):")
        print(f"{'='*80}")
        for i, (path, old_name, clean_name) in enumerate(files_to_delete[:15], 1):
            print(f"{i}. {old_name}")
            print(f"   ❌ DELETE (because '{clean_name}' already exists)")
            print(f"   📁 {path.parent}")
            print()
        
        if len(files_to_delete) > 15:
            print(f"   ... and {len(files_to_delete) - 15} more files to delete\n")
    
    # Show files to rename
    if files_to_rename:
        print(f"\n✏️  FILES TO RENAME (safe to clean):")
        print(f"{'='*80}")
        for i, (old_path, new_path, old_name, new_name) in enumerate(files_to_rename[:15], 1):
            print(f"{i}. {old_name}")
            print(f"   ✅ RENAME → {new_name}")
            print(f"   📁 {old_path.parent}")
            print()
        
        if len(files_to_rename) > 15:
            print(f"   ... and {len(files_to_rename) - 15} more files to rename\n")
    
    # Perform actions if not dry run
    if not dry_run:
        print(f"\n{'='*80}")
        print("⚠️  WARNING: This will permanently delete duplicate files!")
        response = input("Type 'yes' to proceed: ").strip().lower()
        
        if response != 'yes':
            print("❌ Cancelled - No changes made.\n")
            return
        
        print(f"\n{'='*80}")
        print("🔧 Processing files...\n")
        
        deleted_count = 0
        renamed_count = 0
        error_count = 0
        
        # Delete duplicates
        for path, old_name, clean_name in files_to_delete:
            try:
                path.unlink()
                deleted_count += 1
                print(f"✅ Deleted: {old_name}")
            except Exception as e:
                error_count += 1
                print(f"❌ FAILED to delete {old_name}: {e}")
        
        # Rename files
        for old_path, new_path, old_name, new_name in files_to_rename:
            try:
                old_path.rename(new_path)
                renamed_count += 1
                print(f"✅ Renamed: {old_name} → {new_name}")
            except Exception as e:
                error_count += 1
                print(f"❌ FAILED to rename {old_name}: {e}")
        
        print(f"\n{'='*80}")
        print(f"✅ Successfully deleted: {deleted_count} files")
        print(f"✅ Successfully renamed: {renamed_count} files")
        if error_count > 0:
            print(f"❌ Errors: {error_count} files")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("🔍 DRY RUN COMPLETE - No files were changed")
        print("💡 To actually clean files, run with: python clean_duplicate_numbers.py --live")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys
    
    # Default to Documents folder
    docs_folder = Path.home() / "OneDrive" / "Documents"
    
    # Check if --live flag is provided
    dry_run = "--live" not in sys.argv
    
    if not docs_folder.exists():
        docs_folder = Path.home() / "Documents"
    
    if not docs_folder.exists():
        print("❌ Error: Documents folder not found!")
        sys.exit(1)
    
    clean_files(docs_folder, dry_run=dry_run)
