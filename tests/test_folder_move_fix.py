"""
Quick Test: Verify no "cannot find path" errors when folders are moved.

This script creates a test structure with nested files and folders,
then organizes it to verify that files inside moving folders are NOT
double-processed (which caused the 272 failed items).
"""

import sys
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.organizer import FileOrganizer
from core.rules import RuleEngine
from ai.classifier import AISemanticClassifier
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_structure(base_path: Path):
    """Create realistic test structure with nested files."""
    base_path.mkdir(exist_ok=True)
    
    # Root files (should be organized)
    (base_path / "RootFile1.txt").write_text("Root text file")
    (base_path / "RootImage.png").write_text("PNG image")
    
    # Folder with Python project (should move as whole unit)
    project_folder = base_path / "MyAutomationProject"
    project_folder.mkdir(exist_ok=True)
    (project_folder / "main_script.py").write_text("# Main script")
    (project_folder / "config.json").write_text('{"setting": 1}')
    (project_folder / "utils.py").write_text("# Utilities")
    
    # Nested subfolder inside project
    data_folder = project_folder / "data"
    data_folder.mkdir(exist_ok=True)
    (data_folder / "test_data.csv").write_text("col1,col2\n1,2")
    (data_folder / "results.txt").write_text("Test results")
    
    # Another folder with mixed content
    docs_folder = base_path / "ImportantDocs"
    docs_folder.mkdir(exist_ok=True)
    (docs_folder / "report.pdf").write_text("PDF report")
    (docs_folder / "presentation.pptx").write_text("Presentation")
    
    logger.info(f"✅ Created test structure in {base_path}")
    logger.info(f"   - 2 root files")
    logger.info(f"   - MyAutomationProject/ (3 files + data subfolder with 2 files)")
    logger.info(f"   - ImportantDocs/ (2 files)")

def main():
    """Run organization test."""
    test_base = Path("test_folder_move")
    
    # Clean previous test
    if test_base.exists():
        shutil.rmtree(test_base)
    
    # Create test structure
    create_test_structure(test_base)
    
    # Initialize organizer
    logger.info("\n🤖 Initializing AI classifier...")
    ai_classifier = AISemanticClassifier()
    
    logger.info("📋 Loading rule engine...")
    rule_engine = RuleEngine()
    
    logger.info("📁 Creating file organizer...")
    organizer = FileOrganizer(rule_engine=rule_engine, ai_classifier=ai_classifier)
    
    # Organize folder
    logger.info(f"\n🚀 Organizing {test_base}...\n")
    result = organizer.organize_folder(
        folder_path=test_base,
        profile='downloads',
        dry_run=False
    )
    
    # Check results
    logger.info("\n" + "="*60)
    logger.info("📊 ORGANIZATION RESULTS")
    logger.info("="*60)
    logger.info(f"✅ Completed: {result['completed']} items")
    logger.info(f"❌ Failed: {result['failed']} items")
    logger.info(f"📁 Total: {result['total']} operations")
    
    if result['failed'] > 0:
        logger.error("\n⚠️ FAILED ITEMS:")
        for item_name, error in result.get('failed_items', [])[:10]:
            logger.error(f"   - {item_name}: {error}")
    
    # Expected behavior
    logger.info("\n" + "="*60)
    logger.info("🎯 EXPECTED BEHAVIOR")
    logger.info("="*60)
    logger.info("1. RootFile1.txt → Documents/")
    logger.info("2. RootImage.png → Images/")
    logger.info("3. MyAutomationProject/ → Code/ (as whole folder)")
    logger.info("4. ImportantDocs/ → Documents/ (as whole folder)")
    logger.info("5. ✅ NO errors about 'cannot find path' for nested files")
    logger.info("   (main_script.py, config.json, utils.py, test_data.csv, results.txt)")
    
    # Verify
    logger.info("\n" + "="*60)
    logger.info("🔍 VERIFICATION")
    logger.info("="*60)
    
    if result['failed'] == 0:
        logger.info("✅ SUCCESS! No failed items - fix is working!")
    elif result['failed'] > 0:
        # Check if failures are "cannot find path"
        failed_errors = [error for _, error in result.get('failed_items', [])]
        cannot_find_errors = [e for e in failed_errors if 'cannot find the path' in e.lower()]
        
        if cannot_find_errors:
            logger.error(f"❌ FAILURE! {len(cannot_find_errors)} 'cannot find path' errors detected")
            logger.error("   The fix may not be working correctly.")
        else:
            logger.warning(f"⚠️ {result['failed']} items failed for other reasons (not 'cannot find path')")
            logger.info("   This may be acceptable (permissions, locked files, etc.)")
    
    # Show organized structure
    logger.info("\n" + "="*60)
    logger.info("📂 ORGANIZED STRUCTURE")
    logger.info("="*60)
    for item in test_base.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(test_base)
            logger.info(f"   {rel_path}")
    
    logger.info("\n✅ Test complete! Check results above.")
    logger.info(f"📁 Test folder: {test_base.absolute()}")

if __name__ == "__main__":
    main()
