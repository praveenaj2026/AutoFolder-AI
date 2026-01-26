"""Quick test script for organization with debug output."""
import sys
from pathlib import Path
import logging
import os

# Setup logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

# Change to project directory
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Now import
import config.config_manager as cm
import core.organizer as org

# Initialize
config = cm.ConfigManager()
organizer = org.FileOrganizer(config.config)

# Test folder
test_folder = Path(r"C:\Users\Praveen\Downloads\Python Scripts\AutoFolder AI\test_organize")

print("\n" + "="*60)
print("TESTING AUTOFOLDER AI ORGANIZATION")
print("="*60)

# Analyze
print("\n--- ANALYSIS ---")
analysis = organizer.analyze_folder(test_folder)
print(f"Total files: {analysis['total_files']}")
print(f"Total folders: {analysis['total_folders']}")
print(f"Files: {[f.name for f in analysis['files']]}")
print(f"Folder items: {[f['path'].name for f in analysis.get('folders', [])]}")

# Preview
print("\n--- PREVIEW ---")
preview = organizer.preview_organization(test_folder, profile='downloads')
print(f"Operations planned: {len(preview)}")
for op in preview:
    print(f"  {op['source'].name} -> {op['target']}")

# Check if we need to organize
if len(preview) > 0:
    print("\n--- ORGANIZING ---")
    result = organizer.organize_folder(test_folder, profile='downloads', recursive=True)
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Total: {result['total']}")
    print(f"  Completed: {result['completed']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Subfolder stats: {result.get('subfolder_stats', {})}")
    
    print("\n--- FINAL STRUCTURE ---")
    import subprocess
    subprocess.run(['tree', '/F', str(test_folder)], shell=True)
else:
    print("\nNo operations planned - checking why...")
