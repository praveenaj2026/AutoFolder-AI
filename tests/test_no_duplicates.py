"""
Test script to organize TEST_ORGANIZE folder and verify no (1) files are created.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core import FileOrganizer
from ai import AIClassifier
from utils.config_manager import ConfigManager

def test_organize():
    """Test organizing without creating (1) files."""
    
    # Setup
    config = ConfigManager()
    config.config['ai']['enabled'] = True
    
    # Initialize AI classifier
    print("🤖 Loading AI model...")
    ai_classifier = AIClassifier(config)
    
    # Create organizer
    organizer = FileOrganizer(config)
    organizer.ai_classifier = ai_classifier
    
    print("✅ AI model loaded and configured")
    
    # Test folder
    test_folder = Path.home() / "OneDrive" / "Documents" / "TEST_ORGANIZE"
    
    if not test_folder.exists():
        print("❌ TEST_ORGANIZE folder not found!")
        return
    
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: Organization without (1) file creation")
    print(f"📁 Folder: {test_folder}")
    print(f"{'='*80}\n")
    
    # Count files before
    files_before = list(test_folder.rglob('*'))
    files_before = [f for f in files_before if f.is_file()]
    
    print(f"📊 Files BEFORE organization: {len(files_before)}")
    for f in files_before:
        print(f"   • {f.name}")
    
    # Organize
    print(f"\n🔧 Organizing...")
    result = organizer.organize_folder(test_folder, profile='downloads', dry_run=False)
    
    print(f"\n✅ Organization complete!")
    print(f"   Completed: {result['completed']} files")
    print(f"   Failed: {result['failed']} files")
    
    # Count files after
    files_after = list(test_folder.rglob('*'))
    files_after = [f for f in files_after if f.is_file()]
    
    print(f"\n📊 Files AFTER organization: {len(files_after)}")
    
    # Check for (1) patterns
    import re
    files_with_numbers = [f for f in files_after if re.search(r'\s*\(\d+\)\s*', f.stem)]
    
    print(f"\n{'='*80}")
    if files_with_numbers:
        print(f"❌ FAILED: Found {len(files_with_numbers)} files with (1) patterns:")
        for f in files_with_numbers:
            print(f"   ❌ {f.name}")
        print(f"{'='*80}")
        print("❌ THE ORGANIZER CREATED (1) FILES!")
    else:
        print(f"✅ SUCCESS: NO (1) patterns found!")
        print(f"\n📂 Organized structure:")
        
        # Show organized files
        for f in sorted(files_after):
            rel_path = f.relative_to(test_folder)
            print(f"   ✓ {rel_path}")
        
        print(f"\n{'='*80}")
        print("✅ TEST PASSED: Organizer does NOT create (1) files!")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    test_organize()
