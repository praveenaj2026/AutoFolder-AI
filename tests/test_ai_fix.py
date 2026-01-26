"""Quick test to verify AI grouping path comparison fix"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.organizer import FileOrganizer
from ai.classifier import AIClassifier
from utils.config_manager import ConfigManager

# Setup
config_manager = ConfigManager()

organizer = FileOrganizer(config_manager)
ai_classifier = AIClassifier(config_manager.config)
organizer.set_ai_classifier(ai_classifier)

# Test with test_ai_grouping folder
test_folder = Path(__file__).parent / "test_ai_grouping"

if not test_folder.exists():
    print("❌ test_ai_grouping folder not found")
    sys.exit(1)

print(f"🧪 Testing AI grouping with: {test_folder}")
print(f"Files: {len(list(test_folder.glob('*.txt')))} txt files\n")

# Generate preview WITH AI grouping
print("=" * 60)
print("WITH AI GROUPING (Category → AI Group → Type → Date)")
print("=" * 60)
preview_ai = organizer.preview_organization(
    test_folder,
    profile='downloads',
    use_ai_grouping=True
)

print(f"\n✅ Generated {len(preview_ai)} operations")

# Check if AI groups are in the paths
ai_groups_found = set()
for op in preview_ai:
    target_parts = op['target'].parts
    # Look for AI group level (between Documents and TXT)
    for i, part in enumerate(target_parts):
        if part == 'Documents' and i + 1 < len(target_parts):
            next_part = target_parts[i + 1]
            if next_part not in ['TXT', 'DOCX', 'PDF']:  # Not a file type
                ai_groups_found.add(next_part)

if ai_groups_found:
    print(f"\n✅ AI GROUPING WORKING! Found groups:")
    for group in sorted(ai_groups_found):
        print(f"   📁 {group}")
    
    # Show some example paths
    print(f"\n📋 Sample organized paths:")
    for op in preview_ai[:5]:
        print(f"   {op['source'].name}")
        print(f"     → {op['target'].relative_to(test_folder)}")
else:
    print("\n❌ AI GROUPING NOT WORKING - No AI group level found in paths")
    print("Expected: Documents/[AI_Group]/TXT/[Date]/file.txt")
    print("Got examples:")
    for op in preview_ai[:3]:
        print(f"   {op['target'].relative_to(test_folder)}")

# Compare with non-AI preview
print("\n" + "=" * 60)
print("WITHOUT AI GROUPING (Category → Type → Date)")
print("=" * 60)
preview_no_ai = organizer.preview_organization(
    test_folder,
    profile='downloads',
    use_ai_grouping=False
)

print(f"\n✅ Generated {len(preview_no_ai)} operations")
print(f"\n📋 Sample organized paths:")
for op in preview_no_ai[:3]:
    print(f"   {op['source'].name}")
    print(f"     → {op['target'].relative_to(test_folder)}")
