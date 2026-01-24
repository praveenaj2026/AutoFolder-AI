"""
Test suite for File Organizer
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.core.organizer import FileOrganizer
from src.core.rules import RuleEngine


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def organizer():
    """Create a FileOrganizer instance with test config."""
    config = {
        'safety': {
            'preview_required': True,
            'undo_enabled': True,
            'max_undo_history': 10,
            'dry_run_default': False,
            'never_delete': True
        },
        'organization': {
            'create_folders_if_missing': True,
            'handle_conflicts': 'rename',
            'preserve_timestamps': True,
            'ignore_hidden_files': True
        },
        'ai': {
            'enabled': False
        }
    }
    return FileOrganizer(config)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {
        'document.pdf': temp_dir / 'document.pdf',
        'image.jpg': temp_dir / 'image.jpg',
        'video.mp4': temp_dir / 'video.mp4',
        'archive.zip': temp_dir / 'archive.zip',
        'code.py': temp_dir / 'code.py',
    }
    
    for name, path in files.items():
        path.write_text(f"Sample content for {name}")
    
    return files


class TestFileOrganizer:
    """Test cases for FileOrganizer."""
    
    def test_analyze_folder(self, organizer, temp_dir, sample_files):
        """Test folder analysis."""
        analysis = organizer.analyze_folder(temp_dir)
        
        assert analysis['total_files'] == 5
        assert analysis['total_size'] > 0
        assert '.pdf' in analysis['by_extension']
        assert '.jpg' in analysis['by_extension']
    
    def test_preview_organization(self, organizer, temp_dir, sample_files):
        """Test organization preview."""
        preview = organizer.preview_organization(temp_dir, profile='downloads')
        
        assert len(preview) == 5
        assert all('source' in op for op in preview)
        assert all('target' in op for op in preview)
        assert all('category' in op for op in preview)
    
    def test_organize_folder_dry_run(self, organizer, temp_dir, sample_files):
        """Test dry run organization."""
        result = organizer.organize_folder(temp_dir, profile='downloads', dry_run=True)
        
        assert result['success'] == True
        assert result['dry_run'] == True
        assert result['total'] > 0
        
        # Files should not be moved
        for file_path in sample_files.values():
            assert file_path.exists()
    
    def test_organize_folder_actual(self, organizer, temp_dir, sample_files):
        """Test actual file organization."""
        result = organizer.organize_folder(temp_dir, profile='downloads', dry_run=False)
        
        assert result['success'] == True
        assert result['dry_run'] == False
        assert result['completed'] > 0
        
        # Check files were moved
        assert (temp_dir / 'Documents' / 'document.pdf').exists()
        assert (temp_dir / 'Images' / 'image.jpg').exists()
        assert (temp_dir / 'Videos' / 'video.mp4').exists()
    
    def test_undo_operation(self, organizer, temp_dir, sample_files):
        """Test undo functionality."""
        # Organize files
        organizer.organize_folder(temp_dir, profile='downloads', dry_run=False)
        
        # Undo
        success = organizer.undo_last_operation()
        assert success == True
        
        # Files should be back in original location
        for file_path in sample_files.values():
            assert file_path.exists()
    
    def test_conflict_handling(self, organizer, temp_dir):
        """Test duplicate filename handling."""
        # Create two files with same name
        file1 = temp_dir / 'test.txt'
        file1.write_text("Content 1")
        
        # Create target folder with existing file
        target_folder = temp_dir / 'Documents'
        target_folder.mkdir()
        existing = target_folder / 'test.txt'
        existing.write_text("Existing content")
        
        # Organize should rename the new file
        result = organizer.organize_folder(temp_dir, profile='downloads', dry_run=False)
        
        # Both files should exist
        assert existing.exists()
        assert (target_folder / 'test (1).txt').exists()


class TestRuleEngine:
    """Test cases for RuleEngine."""
    
    def test_get_profiles(self):
        """Test profile retrieval."""
        engine = RuleEngine()
        profiles = engine.get_available_profiles()
        
        assert 'downloads' in profiles
        assert 'media' in profiles
        assert 'gaming' in profiles
        assert 'work' in profiles
    
    def test_extension_rule_matching(self):
        """Test extension-based rule matching."""
        engine = RuleEngine()
        
        rule = {
            'type': 'extension',
            'patterns': ['.pdf', '.doc', '.docx']
        }
        
        assert engine.matches_rule(Path('document.pdf'), rule) == True
        assert engine.matches_rule(Path('image.jpg'), rule) == False
    
    def test_name_pattern_rule_matching(self):
        """Test name pattern rule matching."""
        engine = RuleEngine()
        
        rule = {
            'type': 'name_pattern',
            'patterns': [r'screenshot', r'capture']
        }
        
        assert engine.matches_rule(Path('Screenshot_2024.png'), rule) == True
        assert engine.matches_rule(Path('screen_capture.png'), rule) == True
        assert engine.matches_rule(Path('photo.png'), rule) == False
    
    def test_custom_rule_creation(self):
        """Test custom rule creation."""
        engine = RuleEngine()
        
        rule = engine.create_custom_rule(
            name="My Rule",
            rule_type="extension",
            patterns=['.custom'],
            target_folder="Custom Files"
        )
        
        assert rule['name'] == "My Rule"
        assert rule['type'] == "extension"
        assert '.custom' in rule['patterns']
        assert rule['target_folder'] == "Custom Files"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
