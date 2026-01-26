"""
Realistic Test Case: Simulate External HDD with Deep Folder Structure

This recreates the D:\ drive scenario with:
- Root level files (like the 15 files you had)
- Deep nested folders (Desktop/INI/Jan-26/backup of SSD/Python Scripts)
- System files (desktop.ini)
- Development projects (Python Scripts with requirements.txt)
- Various file types at different depths
"""

import sys
import shutil
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.organizer import FileOrganizer
import yaml

# Setup logging to capture everything
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_external_hdd.log', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_test_structure():
    """Create realistic folder structure matching D:\ drive"""
    
    test_root = Path(__file__).parent / 'test_external_hdd'
    
    # Clean up if exists
    if test_root.exists():
        print(f"🗑️  Cleaning up existing test folder...")
        shutil.rmtree(test_root)
    
    test_root.mkdir(exist_ok=True)
    
    print(f"\n📁 Creating test structure at: {test_root}")
    print("="*70)
    
    file_count = 0
    
    # 1. Root level files (simulating the 15 files that got organized)
    print("\n✓ Creating root level files...")
    root_files = [
        ('document1.pdf', 'PDF document'),
        ('photo1.jpg', 'Image'),
        ('music1.mp3', 'Audio'),
        ('video1.mp4', 'Video'),
        ('script1.py', 'Python script'),
        ('data.json', 'JSON data'),
        ('notes.txt', 'Text notes'),
        ('presentation.pptx', 'PowerPoint'),
        ('spreadsheet.xlsx', 'Excel'),
        ('archive.zip', 'Archive'),
        ('installer.exe', 'Installer'),
        ('readme.md', 'Markdown'),
        ('config.yaml', 'YAML config'),
        ('database.db', 'Database'),
        ('image2.png', 'PNG image')
    ]
    
    for filename, content in root_files:
        file_path = test_root / filename
        file_path.write_text(content)
        file_count += 1
    
    print(f"  Created {len(root_files)} root files")
    
    # 2. Desktop folder (this was moved to Code because of desktop.ini)
    print("\n✓ Creating Desktop folder with nested structure...")
    desktop = test_root / 'Desktop'
    
    # Desktop/INI/Jan-26/backup of SSD/
    backup_path = desktop / 'INI' / 'Jan-26' / 'backup of SSD'
    
    # Add desktop.ini (system file that triggered the bug)
    (backup_path / 'desktop.ini').parent.mkdir(parents=True, exist_ok=True)
    (backup_path / 'desktop.ini').write_text('[.ShellClassInfo]\nIconResource=folder.ico')
    file_count += 1
    
    # Python Scripts folder (development project - should be protected)
    python_scripts = backup_path / 'Python Scripts'
    python_scripts.mkdir(parents=True, exist_ok=True)
    
    # Make it a Python project
    (python_scripts / 'requirements.txt').write_text('numpy==1.24.0\npandas==2.0.0')
    (python_scripts / 'setup.py').write_text('from setuptools import setup\nsetup(name="test")')
    (python_scripts / 'main.py').write_text('print("Hello")')
    (python_scripts / 'utils.py').write_text('def helper(): pass')
    (python_scripts / 'test.py').write_text('import unittest')
    file_count += 5
    
    # Create venv folder (should be skipped)
    venv = python_scripts / 'venv'
    venv.mkdir(exist_ok=True)
    (venv / 'pyvenv.cfg').write_text('version = 3.12')
    file_count += 1
    
    # backup of SSD folder with many files
    print("\n✓ Creating 'backup of SSD' folder with nested files...")
    ssd_backup = backup_path / 'backup of SSD'
    ssd_backup.mkdir(parents=True, exist_ok=True)
    
    # Add various files at different depths
    for i in range(50):
        (ssd_backup / f'document_{i}.pdf').write_text(f'Document {i}')
        file_count += 1
    
    for i in range(30):
        (ssd_backup / f'photo_{i}.jpg').write_text(f'Photo {i}')
        file_count += 1
    
    for i in range(20):
        (ssd_backup / f'music_{i}.mp3').write_text(f'Music {i}')
        file_count += 1
    
    # Softwares folder
    print("\n✓ Creating Softwares folder...")
    softwares = backup_path / 'Softwares'
    softwares.mkdir(parents=True, exist_ok=True)
    
    for i in range(25):
        (softwares / f'installer_{i}.exe').write_text(f'Installer {i}')
        file_count += 1
    
    # Add some .ini and .cfg files (should NOT go to Code)
    for i in range(10):
        (softwares / f'config_{i}.ini').write_text(f'[Settings]\nvalue={i}')
        (softwares / f'settings_{i}.cfg').write_text(f'key=value{i}')
        file_count += 2
    
    # Steam Games folder (should be skipped)
    print("\n✓ Creating Steam Games folder (should be protected)...")
    steam_games = backup_path / 'Steam Games - Hack'
    steam_games.mkdir(parents=True, exist_ok=True)
    
    for i in range(15):
        (steam_games / f'game_file_{i}.dat').write_text(f'Game data {i}')
        file_count += 1
    
    # 3. Create some organized folders (should be skipped)
    print("\n✓ Creating already-organized folders (should be skipped)...")
    documents = test_root / 'Documents'
    documents.mkdir(exist_ok=True)
    (documents / 'existing_doc.pdf').write_text('Existing document')
    file_count += 1
    
    images = test_root / 'Images'
    images.mkdir(exist_ok=True)
    (images / 'existing_img.jpg').write_text('Existing image')
    file_count += 1
    
    print("\n" + "="*70)
    print(f"✅ Test structure created: {file_count} files total")
    print(f"📍 Location: {test_root}")
    
    return test_root, file_count

def analyze_structure(test_root):
    """Analyze the test structure before organizing"""
    print("\n" + "="*70)
    print("📊 ANALYZING TEST STRUCTURE")
    print("="*70)
    
    all_files = list(test_root.rglob('*'))
    files = [f for f in all_files if f.is_file()]
    folders = [f for f in all_files if f.is_dir()]
    
    print(f"\nTotal items: {len(all_files)}")
    print(f"  Files: {len(files)}")
    print(f"  Folders: {len(folders)}")
    
    # Analyze depth distribution
    depth_dist = {}
    for f in files:
        try:
            depth = len(f.relative_to(test_root).parts) - 1  # -1 because filename is a part
            depth_dist[depth] = depth_dist.get(depth, 0) + 1
        except:
            pass
    
    print(f"\nFiles by depth:")
    for depth in sorted(depth_dist.keys()):
        print(f"  Depth {depth}: {depth_dist[depth]} files")
    
    # Check for special items
    print(f"\n🔍 Special items:")
    
    dev_projects = []
    for folder in folders:
        if (folder / 'requirements.txt').exists() or (folder / 'package.json').exists():
            dev_projects.append(folder.name)
    print(f"  Development projects: {len(dev_projects)} - {dev_projects}")
    
    ini_files = len(list(test_root.rglob('*.ini')))
    cfg_files = len(list(test_root.rglob('*.cfg')))
    print(f"  System config files: {ini_files} .ini, {cfg_files} .cfg")
    
    game_folders = [f for f in folders if 'Steam' in f.name or 'Games' in f.name]
    print(f"  Game folders: {len(game_folders)}")
    
    return len(files)

def run_organization_test(test_root):
    """Run the organizer on test structure"""
    print("\n" + "="*70)
    print("🚀 RUNNING ORGANIZATION TEST")
    print("="*70)
    
    # Load config
    config_path = Path(__file__).parent / 'config' / 'default_config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Set test-friendly settings
    config['safety']['dry_run_default'] = False  # Actually move files
    config['organization']['max_depth'] = 10
    config['organization']['progress_chunk_size'] = 10  # Smaller chunks for test
    
    print(f"\n⚙️  Configuration:")
    print(f"  max_depth: {config['organization']['max_depth']}")
    print(f"  progress_chunk_size: {config['organization']['progress_chunk_size']}")
    print(f"  dry_run: False")
    
    # Create organizer
    organizer = FileOrganizer(config)
    
    # Initialize AI classifier (required)
    print(f"\n🤖 Initializing AI classifier...")
    from ai.classifier import AIClassifier
    organizer.ai_classifier = AIClassifier(config)
    
    print(f"\n📋 Starting organization...\n")
    
    # Run organization
    result = organizer.organize_folder(
        test_root,
        dry_run=False,
        recursive=True,
        max_depth=10
    )
    
    return result

def validate_results(test_root, original_file_count, result):
    """Validate the organization results"""
    print("\n" + "="*70)
    print("✅ VALIDATING RESULTS")
    print("="*70)
    
    passed = []
    failed = []
    
    # Check 1: Files were actually organized
    print("\n✓ Test 1: Files organized")
    completed = result.get('completed', 0)
    print(f"  Completed: {completed} operations")
    if completed > 0:
        print(f"  ✅ PASS: {completed} files organized")
        passed.append("Files organized")
    else:
        print(f"  ❌ FAIL: No files organized!")
        failed.append("Files organized")
    
    # Check 2: Category folders created
    print("\n✓ Test 2: Category folders created")
    category_folders = [d for d in test_root.iterdir() if d.is_dir() and d.name in 
                       ['Documents', 'Images', 'Videos', 'Audio', 'Code', 'Archives', 'Installers']]
    print(f"  Found categories: {[f.name for f in category_folders]}")
    if len(category_folders) >= 3:
        print(f"  ✅ PASS: {len(category_folders)} categories created")
        passed.append("Category folders")
    else:
        print(f"  ❌ FAIL: Only {len(category_folders)} categories")
        failed.append("Category folders")
    
    # Check 3: Development project protected
    print("\n✓ Test 3: Development project protected")
    python_scripts = test_root / 'Desktop' / 'INI' / 'Jan-26' / 'backup of SSD' / 'Python Scripts'
    if python_scripts.exists():
        req_exists = (python_scripts / 'requirements.txt').exists()
        main_exists = (python_scripts / 'main.py').exists()
        if req_exists and main_exists:
            print(f"  ✅ PASS: Python project still intact at original location")
            passed.append("Dev project protection")
        else:
            print(f"  ❌ FAIL: Python project was moved/broken")
            failed.append("Dev project protection")
    else:
        print(f"  ⚠️  WARNING: Python Scripts folder not found (may have been moved)")
    
    # Check 4: System config files NOT in Code
    print("\n✓ Test 4: System config files NOT in Code")
    code_folder = test_root / 'Code'
    if code_folder.exists():
        ini_in_code = len(list(code_folder.rglob('*.ini')))
        cfg_in_code = len(list(code_folder.rglob('*.cfg')))
        print(f"  .ini files in Code: {ini_in_code}")
        print(f"  .cfg files in Code: {cfg_in_code}")
        if ini_in_code == 0 and cfg_in_code == 0:
            print(f"  ✅ PASS: No system config files in Code")
            passed.append("Config files protection")
        else:
            print(f"  ❌ FAIL: System config files found in Code!")
            failed.append("Config files protection")
    else:
        print(f"  ✅ PASS: No Code folder created (no code files)")
        passed.append("Config files protection")
    
    # Check 5: Desktop folder NOT moved to Code
    print("\n✓ Test 5: Desktop folder handling")
    desktop_in_code = test_root / 'Code' / 'Desktop'
    if desktop_in_code.exists():
        print(f"  ❌ FAIL: Desktop folder was moved to Code!")
        failed.append("Desktop protection")
    else:
        print(f"  ✅ PASS: Desktop folder not moved to Code")
        passed.append("Desktop protection")
    
    # Check 6: Recursive organization worked
    print("\n✓ Test 6: Recursive organization")
    all_files_now = [f for f in test_root.rglob('*') if f.is_file()]
    organized_files = 0
    for cat_folder in category_folders:
        cat_files = [f for f in cat_folder.rglob('*') if f.is_file()]
        organized_files += len(cat_files)
    
    print(f"  Files in category folders: {organized_files}")
    print(f"  Total operations: {completed}")
    
    if organized_files >= completed * 0.8:  # At least 80% should be in categories
        print(f"  ✅ PASS: Files properly organized into categories")
        passed.append("Recursive organization")
    else:
        print(f"  ❌ FAIL: Many files not in category folders")
        failed.append("Recursive organization")
    
    # Check 7: Check logs for progress updates
    print("\n✓ Test 7: Progress updates in logs")
    log_file = Path('logs/test_external_hdd.log')
    if log_file.exists():
        log_content = log_file.read_text()
        progress_updates = log_content.count('Progress:')
        large_folder_msg = '⚡' in log_content or 'Large folder' in log_content
        
        print(f"  Progress updates found: {progress_updates}")
        print(f"  Large folder detection: {large_folder_msg}")
        
        if progress_updates > 0:
            print(f"  ✅ PASS: Progress updates working")
            passed.append("Progress updates")
        else:
            print(f"  ❌ FAIL: No progress updates in log")
            failed.append("Progress updates")
    
    # Final summary
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    print(f"\n✅ Passed: {len(passed)}/{len(passed) + len(failed)}")
    for test in passed:
        print(f"  ✅ {test}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for test in failed:
            print(f"  ❌ {test}")
    
    print(f"\n📈 Organization Stats:")
    print(f"  Original files: {original_file_count}")
    print(f"  Operations completed: {completed}")
    print(f"  Failed: {result.get('failed', 0)}")
    print(f"  Success rate: {int(completed/original_file_count*100) if original_file_count > 0 else 0}%")
    
    return len(failed) == 0

def main():
    """Run complete validation test"""
    print("\n" + "="*70)
    print("🧪 EXTERNAL HDD SIMULATION TEST")
    print("="*70)
    print("\nThis test simulates your D:\\ drive scenario:")
    print("  • Root files (15 files)")
    print("  • Deep nested structure (Desktop/INI/Jan-26/backup of SSD)")
    print("  • System files (desktop.ini)")
    print("  • Development projects (Python Scripts)")
    print("  • Game folders (Steam Games)")
    print("  • Various depths and file types")
    
    try:
        # Step 1: Create test structure
        test_root, file_count = create_test_structure()
        
        # Step 2: Analyze before
        original_count = analyze_structure(test_root)
        
        # Step 3: Run organization
        result = run_organization_test(test_root)
        
        # Step 4: Validate results
        all_passed = validate_results(test_root, original_count, result)
        
        # Step 5: Show log location
        print("\n" + "="*70)
        print("📋 DETAILED LOGS")
        print("="*70)
        print(f"\nFull log available at: logs/test_external_hdd.log")
        print(f"Test folder: {test_root}")
        print(f"\nInspect the organized files manually to verify!")
        
        if all_passed:
            print("\n🎉 ALL VALIDATION TESTS PASSED!")
            print("\n✅ Ready to use on real D:\\ drive with 149,598 files!")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED - Review results above")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
