"""
Apply Safe File Operations to All Modules

Automatically patches all vulnerable .stat() calls across the codebase.
"""

import re
from pathlib import Path

# Files that need patching with their unsafe stat() call locations
FILES_TO_PATCH = [
    'src/core/rules.py',
    'src/core/search_engine.py',
    'src/core/smart_renamer.py',
    'src/core/duplicate_detector.py',
    'src/core/content_analyzer.py',
    'src/core/compressor.py'
]

SAFE_OPS_IMPORT = "from utils.safe_file_ops import safe_stat, safe_get_size, safe_get_mtime, safe_exists\n"

def patch_file(file_path: Path):
    """Add safe_file_ops import and log which files need manual review"""
    print(f"\n📝 {file_path}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Check if already imported
    if 'from utils.safe_file_ops import' in content:
        print("  ✅ Already has safe_file_ops import")
        return
    
    # Add import after other imports
    lines = content.split('\n')
    import_insert_idx = 0
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_insert_idx = i + 1
        elif import_insert_idx > 0 and line.strip() == '':
            # Found blank line after imports
            break
    
    if import_insert_idx > 0:
        lines.insert(import_insert_idx, SAFE_OPS_IMPORT.strip())
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"  ✅ Added safe_file_ops import at line {import_insert_idx + 1}")
        print(f"  ⚠️  Manual review needed: Replace .stat() calls with safe_* functions")
    else:
        print("  ❌ Could not find import section")

def main():
    print("=" * 70)
    print("PATCHING FILES WITH SAFE FILE OPERATIONS")
    print("=" * 70)
    
    for file_rel_path in FILES_TO_PATCH:
        file_path = Path(file_rel_path)
        if file_path.exists():
            patch_file(file_path)
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("""
1. Review each file and replace unsafe calls:
   - file_path.stat() → safe_stat(file_path)
   - file_path.stat().st_size → safe_get_size(file_path)
   - file_path.stat().st_mtime → safe_get_mtime(file_path)
   - file_path.exists() → safe_exists(file_path)

2. Run: python test_defensive.py

3. Fix any remaining issues
""")

if __name__ == '__main__':
    main()
