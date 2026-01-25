"""
Verification script to check if (1) files were created after organization.
Run this AFTER organizing the TEST_ORGANIZE folder.
"""
from pathlib import Path
import re

def has_number_suffix(name: str) -> bool:
    """Check if filename has (1) (2) (3) pattern."""
    stem = Path(name).stem
    return bool(re.search(r'\s*\(\d+\)\s*$', stem))

def verify_no_duplicates(folder_path: Path):
    """Check if any files with (1) patterns were created."""
    print(f"\n{'='*80}")
    print(f"🔍 VERIFICATION: Checking for (1) patterns in organized files")
    print(f"📁 Target: {folder_path}")
    print(f"{'='*80}\n")
    
    # Get all files recursively
    all_files = [f for f in folder_path.rglob('*') if f.is_file()]
    
    # Filter files with (1) patterns
    files_with_numbers = [f for f in all_files if has_number_suffix(f.name)]
    
    if files_with_numbers:
        print(f"❌ FAILED: Found {len(files_with_numbers)} files with (1) patterns:")
        print(f"{'='*80}")
        for file in files_with_numbers:
            print(f"  ❌ {file.name}")
            print(f"     📁 {file.parent}")
            print()
        print(f"{'='*80}")
        print("❌ THE ORGANIZER IS STILL CREATING (1) FILES!")
    else:
        print(f"✅ SUCCESS: NO files with (1) patterns found!")
        print(f"✅ Total files checked: {len(all_files)}")
        print(f"\n📊 Organized files:")
        print(f"{'='*80}")
        
        # Show organized structure
        categories = {}
        for file in all_files:
            # Get relative path from folder
            rel_path = file.relative_to(folder_path)
            category = str(rel_path.parent) if rel_path.parent != Path('.') else "root"
            if category not in categories:
                categories[category] = []
            categories[category].append(file.name)
        
        for category, files in sorted(categories.items()):
            print(f"\n📂 {category}:")
            for fname in sorted(files):
                print(f"   ✓ {fname}")
        
        print(f"\n{'='*80}")
        print("✅ ORGANIZER WORKING CORRECTLY - NO (1) FILES CREATED!")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    # Check Documents folder
    docs_folder = Path.home() / "OneDrive" / "Documents"
    
    if not docs_folder.exists():
        docs_folder = Path.home() / "Documents"
    
    if not docs_folder.exists():
        print("❌ Error: Documents folder not found!")
        exit(1)
    
    # Verify TEST_ORGANIZE or all Documents
    test_folder = docs_folder / "TEST_ORGANIZE"
    
    if test_folder.exists():
        print("🔍 Checking TEST_ORGANIZE folder...")
        verify_no_duplicates(test_folder)
    else:
        print("⚠️ TEST_ORGANIZE not found, checking entire Documents folder...")
        verify_no_duplicates(docs_folder)
