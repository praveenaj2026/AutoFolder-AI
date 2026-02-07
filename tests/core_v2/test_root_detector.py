"""
Unit tests for v2.0 Root Detector.

Tests root detection for PROJECT, MEDIA, ARCHIVE, BACKUP, GAME, VM types.
"""

import pytest
from pathlib import Path
from src.core_v2.scanner import scan_folder
from src.core_v2.root_detector import RootDetector, detect_protected_roots, ROOT_MARKERS
from src.core_v2.models import RootType


class TestRootDetector:
    """Test RootDetector class."""
    
    def test_detect_no_roots(self, tmp_path):
        """Test detection with no protected roots."""
        # Create simple folder with no markers
        (tmp_path / "file1.txt").write_text("test")
        (tmp_path / "file2.txt").write_text("test")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 0
    
    def test_detect_project_root_git(self, tmp_path):
        """Test detecting project root with .git folder."""
        # Create project structure
        (tmp_path / ".git").mkdir()
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "src").mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector(min_confidence=0.7)
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.PROJECT
        assert roots[0].confidence >= 0.7
        assert ".git" in roots[0].markers
        assert roots[0].protect is True
    
    def test_detect_project_root_package_json(self, tmp_path):
        """Test detecting project root with package.json."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "src").mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.PROJECT
        assert "package.json" in roots[0].markers
    
    def test_detect_project_root_python(self, tmp_path):
        """Test detecting Python project root."""
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]")
        (tmp_path / "requirements.txt").write_text("requests")
        (tmp_path / "src").mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.PROJECT
        assert roots[0].confidence >= 0.9  # pyproject.toml has high weight
    
    def test_detect_media_root(self, tmp_path):
        """Test detecting media collection root."""
        (tmp_path / "Music").mkdir()
        (tmp_path / "Videos").mkdir()
        (tmp_path / "Photos").mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector(min_confidence=0.5)
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.MEDIA
        assert roots[0].confidence >= 0.5
    
    def test_detect_backup_root(self, tmp_path):
        """Test detecting backup root."""
        (tmp_path / "Backups").mkdir()
        (tmp_path / "backup.log").write_text("Backup log")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.BACKUP
        assert "Backups" in roots[0].markers
    
    def test_detect_game_root(self, tmp_path):
        """Test detecting game installation root."""
        steamapps = tmp_path / "steamapps"
        steamapps.mkdir()
        (steamapps / "common").mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.GAME
        assert roots[0].confidence >= 0.9  # steamapps is strong marker
    
    def test_detect_vm_root(self, tmp_path):
        """Test detecting VM root."""
        (tmp_path / "Windows 10.vbox").write_text("VM config")
        (tmp_path / "Windows 10.vdi").write_text("Disk image")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.VM
        assert roots[0].confidence >= 0.8
    
    def test_detect_nested_roots(self, tmp_path):
        """Test detecting nested roots (should stop at first)."""
        # Create outer project
        (tmp_path / ".git").mkdir()
        
        # Create nested project (should not be detected)
        nested = tmp_path / "subproject"
        nested.mkdir()
        (nested / ".git").mkdir()
        (nested / "README.md").write_text("Nested")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        # Should only detect outer root
        assert len(roots) == 1
        assert roots[0].path == tmp_path
    
    def test_detect_multiple_sibling_roots(self, tmp_path):
        """Test detecting multiple roots at same level."""
        # Create two separate projects
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / ".git").mkdir()
        
        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / "package.json").write_text("{}")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 2
        root_paths = {r.path for r in roots}
        assert project1 in root_paths
        assert project2 in root_paths
    
    def test_is_protected(self, tmp_path):
        """Test is_protected method."""
        (tmp_path / ".git").mkdir()
        src = tmp_path / "src"
        src.mkdir()
        test_file = src / "main.py"
        test_file.write_text("print('hello')")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        detector.detect_roots(tree)
        
        # Root itself is protected
        assert detector.is_protected(tmp_path) is True
        
        # Children are protected
        assert detector.is_protected(src) is True
        assert detector.is_protected(test_file) is True
        
        # Outside path is not protected
        outside = Path(tmp_path.parent / "other")
        assert detector.is_protected(outside) is False
    
    def test_get_root_for_path(self, tmp_path):
        """Test get_root_for_path method."""
        (tmp_path / ".git").mkdir()
        src = tmp_path / "src"
        src.mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        detector.detect_roots(tree)
        
        # Get root for child path
        root = detector.get_root_for_path(src)
        assert root is not None
        assert root.path == tmp_path
        assert root.root_type == RootType.PROJECT
        
        # Get root for outside path
        outside = Path(tmp_path.parent / "other")
        root = detector.get_root_for_path(outside)
        assert root is None
    
    def test_min_confidence_threshold(self, tmp_path):
        """Test minimum confidence threshold."""
        # Create weak markers
        (tmp_path / "src").mkdir()  # Weight 0.4
        
        tree = scan_folder(tmp_path)
        
        # With default threshold (0.7), should not detect
        detector = RootDetector(min_confidence=0.7)
        roots = detector.detect_roots(tree)
        assert len(roots) == 0
        
        # With lower threshold (0.3), should detect
        detector = RootDetector(min_confidence=0.3)
        roots = detector.detect_roots(tree)
        assert len(roots) == 1
    
    def test_confidence_scoring(self, tmp_path):
        """Test confidence scoring with multiple markers."""
        # Create multiple strong markers
        (tmp_path / ".git").mkdir()          # 1.0
        (tmp_path / ".gitignore").write_text("")  # 0.8
        (tmp_path / "src").mkdir()           # 0.4
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        assert len(roots) == 1
        # Multiple markers should boost confidence (capped at 1.0)
        assert roots[0].confidence == 1.0
        assert len(roots[0].markers) >= 2
    
    def test_marker_type_enforcement(self, tmp_path):
        """Test that markers respect file/folder requirements."""
        # Create .git as FILE (wrong - should be folder)
        (tmp_path / ".git").write_text("fake")
        
        tree = scan_folder(tmp_path)
        detector = RootDetector(min_confidence=0.7)
        roots = detector.detect_roots(tree)
        
        # Should not detect because .git must be a folder
        assert len(roots) == 0
        
        # Now create correct .git folder
        (tmp_path / ".git").unlink()
        (tmp_path / ".git").mkdir()
        
        tree = scan_folder(tmp_path)
        roots = detector.detect_roots(tree)
        
        # Should now detect
        assert len(roots) == 1


class TestConvenienceFunction:
    """Test detect_protected_roots convenience function."""
    
    def test_detect_protected_roots(self, tmp_path):
        """Test convenience function."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "README.md").write_text("# Project")
        
        tree = scan_folder(tmp_path)
        roots = detect_protected_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.PROJECT
    
    def test_detect_with_custom_confidence(self, tmp_path):
        """Test convenience function with custom confidence."""
        (tmp_path / "src").mkdir()  # Weak marker (0.4)
        
        tree = scan_folder(tmp_path)
        
        # Default confidence (0.7) - should not detect
        roots = detect_protected_roots(tree)
        assert len(roots) == 0
        
        # Custom low confidence - should detect
        roots = detect_protected_roots(tree, min_confidence=0.3)
        assert len(roots) == 1


class TestRootMarkers:
    """Test root marker definitions."""
    
    def test_marker_types_defined(self):
        """Test all root types have markers defined."""
        marker_types = {marker.root_type for marker in ROOT_MARKERS}
        
        # All types except UNKNOWN should have markers
        expected_types = {
            RootType.PROJECT,
            RootType.MEDIA,
            RootType.ARCHIVE,
            RootType.BACKUP,
            RootType.GAME,
            RootType.VM
        }
        
        assert expected_types.issubset(marker_types)
    
    def test_marker_weights_valid(self):
        """Test all marker weights are in valid range."""
        for marker in ROOT_MARKERS:
            assert 0.0 <= marker.weight <= 1.0, f"Invalid weight for {marker.pattern}"
    
    def test_project_markers_comprehensive(self):
        """Test project markers cover common cases."""
        project_patterns = {
            marker.pattern.lower()
            for marker in ROOT_MARKERS
            if marker.root_type == RootType.PROJECT
        }
        
        # Check for common project markers
        expected = {".git", "package.json", "pyproject.toml", "requirements.txt"}
        assert expected.issubset(project_patterns)


class TestRealWorldScenarios:
    """Test real-world directory scenarios."""
    
    def test_python_project_structure(self, tmp_path):
        """Test realistic Python project."""
        # Create Python project
        (tmp_path / ".git").mkdir()
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]")
        (tmp_path / "requirements.txt").write_text("requests")
        (tmp_path / ".venv").mkdir()
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "main.py").write_text("print('hello')")
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("def test():\n    pass")
        
        tree = scan_folder(tmp_path)
        roots = detect_protected_roots(tree)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.PROJECT
        assert roots[0].confidence >= 0.9
        assert roots[0].path == tmp_path
    
    def test_media_library_structure(self, tmp_path):
        """Test realistic media library."""
        music = tmp_path / "Music"
        music.mkdir()
        (music / "Rock").mkdir()
        (music / "Jazz").mkdir()
        
        videos = tmp_path / "Videos"
        videos.mkdir()
        (videos / "Movies").mkdir()
        
        photos = tmp_path / "Photos"
        photos.mkdir()
        (photos / "2024").mkdir()
        
        tree = scan_folder(tmp_path)
        roots = detect_protected_roots(tree, min_confidence=0.5)
        
        assert len(roots) == 1
        assert roots[0].root_type == RootType.MEDIA
    
    def test_virtualbox_vm_structure(self, tmp_path):
        """Test VirtualBox VM structure."""
        vm_folder = tmp_path / "Windows 10"
        vm_folder.mkdir()
        (vm_folder / "Windows 10.vbox").write_text("VM config")
        (vm_folder / "Windows 10.vdi").write_text("Disk")
        (vm_folder / "Logs").mkdir()
        (vm_folder / "Snapshots").mkdir()
        
        tree = scan_folder(tmp_path)
        detector = RootDetector()
        roots = detector.detect_roots(tree)
        
        # Should detect the VM folder, not parent
        assert len(roots) == 1
        assert roots[0].path == vm_folder
        assert roots[0].root_type == RootType.VM
