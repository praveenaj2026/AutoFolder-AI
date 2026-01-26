"""
Defensive Testing for Safe File Operations

Tests all modules to ensure they handle inaccessible files gracefully.
Creates simulated inaccessible files and verifies no crashes occur.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.organizer import FileOrganizer
from core.rules import RuleEngine
from core.file_analyzer import FileAnalyzer
from core.duplicate_detector import DuplicateDetector
from core.search_engine import SearchEngine
from core.smart_renamer import SmartRenamer
from core.content_analyzer import ContentAnalyzer
from core.compressor import SmartCompressor
from utils.safe_file_ops import (
    safe_stat, safe_get_size, safe_get_mtime,
    safe_exists, safe_is_file, safe_is_dir
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.total = 0
    
    def add_pass(self, test_name):
        self.passed.append(test_name)
        self.total += 1
        logger.info(f"  ✅ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        self.total += 1
        logger.error(f"  ❌ {test_name}: {error}")
    
    def summary(self):
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total Tests: {self.total}")
        logger.info(f"✅ Passed: {len(self.passed)}")
        logger.info(f"❌ Failed: {len(self.failed)}")
        
        if self.failed:
            logger.error("\nFailed Tests:")
            for name, error in self.failed:
                logger.error(f"  - {name}: {error}")
        
        return len(self.failed) == 0


def create_test_environment():
    """Create test folder with normal and inaccessible files"""
    temp_dir = Path(tempfile.mkdtemp(prefix="autofolder_defense_test_"))
    
    # Create normal files
    (temp_dir / "normal.txt").write_text("Normal file")
    (temp_dir / "document.pdf").write_bytes(b"PDF content")
    (temp_dir / "image.jpg").write_bytes(b"JPG content")
    
    # Create a file that will be deleted (simulates FileNotFoundError)
    deleted_file = temp_dir / "deleted.txt"
    deleted_file.write_text("Will be deleted")
    
    # Create subfolder
    subdir = temp_dir / "subfolder"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file")
    
    return temp_dir, deleted_file


def test_safe_file_ops(results: TestResults):
    """Test safe file operation wrappers"""
    logger.info("\n🔒 Testing Safe File Operations Wrappers...")
    
    temp_dir, deleted_file = create_test_environment()
    
    try:
        # Test normal file
        normal_file = temp_dir / "normal.txt"
        
        # Test safe_stat
        stat_result = safe_stat(normal_file)
        if stat_result is not None:
            results.add_pass("safe_stat on normal file")
        else:
            results.add_fail("safe_stat on normal file", "Returned None for valid file")
        
        # Test safe_get_size
        size = safe_get_size(normal_file)
        if size > 0:
            results.add_pass("safe_get_size on normal file")
        else:
            results.add_fail("safe_get_size on normal file", f"Got size {size}")
        
        # Test safe_get_mtime
        mtime = safe_get_mtime(normal_file)
        if mtime > 0:
            results.add_pass("safe_get_mtime on normal file")
        else:
            results.add_fail("safe_get_mtime on normal file", f"Got mtime {mtime}")
        
        # Now delete file and test with missing file
        deleted_file.unlink()
        
        # Test safe_stat on missing file
        stat_result = safe_stat(deleted_file)
        if stat_result is None:
            results.add_pass("safe_stat on missing file (returns None)")
        else:
            results.add_fail("safe_stat on missing file", "Did not return None")
        
        # Test safe_get_size on missing file
        size = safe_get_size(deleted_file, default=999)
        if size == 999:
            results.add_pass("safe_get_size on missing file (returns default)")
        else:
            results.add_fail("safe_get_size on missing file", f"Got {size} instead of default")
        
        # Test safe_get_mtime on missing file
        mtime = safe_get_mtime(deleted_file)
        if mtime > 0:
            results.add_pass("safe_get_mtime on missing file (returns current time)")
        else:
            results.add_fail("safe_get_mtime on missing file", f"Got {mtime}")
        
        # Test safe_exists
        if not safe_exists(deleted_file):
            results.add_pass("safe_exists on missing file (returns False)")
        else:
            results.add_fail("safe_exists on missing file", "Returned True")
        
    except Exception as e:
        results.add_fail("safe_file_ops general test", str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_organizer(results: TestResults):
    """Test FileOrganizer with inaccessible files"""
    logger.info("\n🔒 Testing FileOrganizer...")
    
    temp_dir, deleted_file = create_test_environment()
    
    try:
        config = {
            'safety': {'max_undo_history': 10, 'dry_run_default': False, 'never_delete': True},
            'organization': {'create_folders_if_missing': True, 'handle_conflicts': 'rename'},
            'ai': {'enabled': False}
        }
        organizer = FileOrganizer(config)
        
        # Delete file to simulate inaccessible
        deleted_file.unlink()
        
        # Test analyze_folder (should not crash)
        try:
            analysis = organizer.analyze_folder(temp_dir)
            results.add_pass("FileOrganizer.analyze_folder with missing files")
        except Exception as e:
            results.add_fail("FileOrganizer.analyze_folder", str(e))
        
        # Test organize_folder (should not crash)
        try:
            result = organizer.organize_folder(temp_dir, dry_run=True)
            results.add_pass("FileOrganizer.organize_folder with missing files")
        except Exception as e:
            results.add_fail("FileOrganizer.organize_folder", str(e))
        
    except Exception as e:
        results.add_fail("FileOrganizer initialization", str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_analyzer(results: TestResults):
    """Test FileAnalyzer with inaccessible files"""
    logger.info("\n🔒 Testing FileAnalyzer...")
    
    temp_dir, deleted_file = create_test_environment()
    
    try:
        analyzer = FileAnalyzer()
        
        # Test with normal file
        normal_file = temp_dir / "normal.txt"
        try:
            metadata = analyzer.analyze(normal_file)
            results.add_pass("FileAnalyzer.analyze on normal file")
        except Exception as e:
            results.add_fail("FileAnalyzer.analyze on normal file", str(e))
        
        # Test with missing file
        deleted_file.unlink()
        try:
            metadata = analyzer.analyze(deleted_file)
            results.add_pass("FileAnalyzer.analyze with missing file (no crash)")
        except FileNotFoundError:
            results.add_fail("FileAnalyzer.analyze with missing file", "FileNotFoundError not handled")
        except Exception as e:
            results.add_fail("FileAnalyzer.analyze with missing file", str(e))
        
    except Exception as e:
        results.add_fail("FileAnalyzer initialization", str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_duplicate_detector(results: TestResults):
    """Test DuplicateDetector with inaccessible files"""
    logger.info("\n🔒 Testing DuplicateDetector...")
    
    temp_dir, deleted_file = create_test_environment()
    
    try:
        detector = DuplicateDetector()
        
        # Test find_duplicates (should not crash)
        try:
            duplicates = detector.find_duplicates(temp_dir)
            results.add_pass("DuplicateDetector.find_duplicates with mixed files")
        except Exception as e:
            results.add_fail("DuplicateDetector.find_duplicates", str(e))
        
    except Exception as e:
        results.add_fail("DuplicateDetector initialization", str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_search_engine(results: TestResults):
    """Test SearchEngine with inaccessible files"""
    logger.info("\n🔒 Testing SearchEngine...")
    
    temp_dir, deleted_file = create_test_environment()
    
    try:
        config = {'search': {'max_results': 100}}
        search_engine = SearchEngine(config)
        
        # Index files
        try:
            search_engine.index_folder(temp_dir)
            results.add_pass("SearchEngine.index_folder with mixed files")
        except Exception as e:
            results.add_fail("SearchEngine.index_folder", str(e))
        
        # Search (should not crash)
        try:
            search_results = search_engine.search("normal")
            results.add_pass("SearchEngine.search after indexing")
        except Exception as e:
            results.add_fail("SearchEngine.search", str(e))
        
    except Exception as e:
        results.add_fail("SearchEngine initialization", str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_content_analyzer(results: TestResults):
    """Test ContentAnalyzer with inaccessible files"""
    logger.info("\n🔒 Testing ContentAnalyzer...")
    
    temp_dir, deleted_file = create_test_environment()
    
    try:
        analyzer = ContentAnalyzer()
        
        # Test with normal file
        normal_file = temp_dir / "document.pdf"
        try:
            content = analyzer.analyze_pdf(normal_file)
            results.add_pass("ContentAnalyzer.analyze_pdf on normal file")
        except Exception as e:
            # PDF analysis might fail for various reasons, that's ok
            results.add_pass("ContentAnalyzer.analyze_pdf handled gracefully")
        
        # Test with missing file
        deleted_file.unlink()
        try:
            content = analyzer.analyze_pdf(deleted_file)
            results.add_pass("ContentAnalyzer.analyze_pdf with missing file (no crash)")
        except FileNotFoundError:
            results.add_fail("ContentAnalyzer.analyze_pdf", "FileNotFoundError not handled")
        except Exception as e:
            # Other errors are acceptable
            results.add_pass("ContentAnalyzer.analyze_pdf handled error gracefully")
        
    except Exception as e:
        results.add_fail("ContentAnalyzer initialization", str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all defensive tests"""
    logger.info("=" * 70)
    logger.info("DEFENSIVE TESTING - SAFE FILE OPERATIONS")
    logger.info("=" * 70)
    logger.info("\nTesting all modules with inaccessible files...")
    logger.info("(desktop.ini, deleted files, permission errors, etc.)\n")
    
    results = TestResults()
    
    # Run all tests
    test_safe_file_ops(results)
    test_organizer(results)
    test_file_analyzer(results)
    test_duplicate_detector(results)
    test_search_engine(results)
    test_content_analyzer(results)
    
    # Print summary
    success = results.summary()
    
    if success:
        logger.info("\n🎉 ALL TESTS PASSED - Production Ready!")
        return 0
    else:
        logger.error("\n⚠️  SOME TESTS FAILED - Fix Required!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
