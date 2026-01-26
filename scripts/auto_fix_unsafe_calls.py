"""
Auto-Replace Unsafe stat() Calls

Automatically replaces all unsafe file operations with safe versions.
"""

import re
from pathlib import Path

REPLACEMENTS = [
    # Replace .stat().st_size
    (r'(\w+)\.stat\(\)\.st_size', r'safe_get_size(\1)'),
    # Replace .stat().st_mtime  
    (r'(\w+)\.stat\(\)\.st_mtime', r'safe_get_mtime(\1)'),
    # Replace .exists()
    (r'(\w+)\.exists\(\)', r'safe_exists(\1)'),
]

FILES = [
    'src/core/rules.py',
    'src/core/search_engine.py',
    'src/core/smart_renamer.py',
    'src/core/duplicate_detector.py',
    'src/core/content_analyzer.py',
    'src/core/compressor.py'
]

def auto_replace_unsafe_calls(file_path: Path):
    """Replace unsafe calls with safe versions"""
    print(f"\n📝 Processing {file_path.name}...")
    
    content = file_path.read_text(encoding='utf-8')
    original = content
    replacements_made = 0
    
    for pattern, replacement in REPLACEMENTS:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            replacements_made += len(matches)
            print(f"  ✅ Replaced {len(matches)} instances of pattern: {pattern}")
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"  💾 Saved {replacements_made} replacements")
    else:
        print("  ℹ️  No replacements needed")
    
    return replacements_made

def main():
    print("=" * 70)
    print("AUTO-REPLACING UNSAFE FILE OPERATIONS")
    print("=" * 70)
    
    total_replacements = 0
    
    for file_rel_path in FILES:
        file_path = Path(file_rel_path)
        if file_path.exists():
            total_replacements += auto_replace_unsafe_calls(file_path)
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Made {total_replacements} replacements")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: Some .stat() calls need manual review:")
    print("  - Calls with complex expressions")
    print("  - Lambda functions with .stat()")
    print("  - Calls that need full stat object (not just size/mtime)")
    print("\n▶️  Run: python test_defensive.py")

if __name__ == '__main__':
    main()
