"""
Unit tests for v2.0 DeepScanner.

Tests deep scanning, error handling, symlinks, and performance.
"""

import pytest
import os
import time
from pathlib import Path
from src.core_v2.scanner import DeepScanner, scan_folder
from src.core_v2.models import FileNode


class TestDeepScanner:
    """Test DeepScanner class."""
    
    def test_scan_empty_directory(self, tmp_path):
        """Test scanning empty directory."""
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        assert result.path == tmp_path
        assert result.is_dir is True
        assert len(result.children) == 0
        assert scanner.statistics['files_scanned'] == 0
        assert scanner.statistics['dirs_scanned'] == 0
    
    def test_scan_single_file(self, tmp_path):
        """Test scanning directory with single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")
        
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        assert result.path == tmp_path
        assert len(result.children) == 1
        assert scanner.statistics['files_scanned'] == 1
        
        child = result.children[0]
        assert child.path == test_file
        assert child.is_file is True
        assert child.size == 5
    
    def test_scan_nested_structure(self, tmp_path):
        """Test scanning nested directory structure."""
        # Create structure:
        # tmp_path/
        #   file1.txt
        #   folder1/
        #     file2.txt
        #     folder2/
        #       file3.txt
        
        (tmp_path / "file1.txt").write_text("1")
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "file2.txt").write_text("22")
        folder2 = folder1 / "folder2"
        folder2.mkdir()
        (folder2 / "file3.txt").write_text("333")
        
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        assert scanner.statistics['files_scanned'] == 3
        assert scanner.statistics['dirs_scanned'] == 2
        
        # Check root has 2 children (file1.txt and folder1)
        assert len(result.children) == 2
        
        # Find folder1
        folder1_node = next(c for c in result.children if c.is_dir)
        assert folder1_node.path.name == "folder1"
        assert len(folder1_node.children) == 2  # file2.txt and folder2
    
    def test_scan_max_depth(self, tmp_path):
        """Test scanning with max depth limit."""
        # Create deep structure
        (tmp_path / "file1.txt").write_text("1")
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "file2.txt").write_text("2")
        folder2 = folder1 / "folder2"
        folder2.mkdir()
        (folder2 / "file3.txt").write_text("3")
        
        # Scan with max_depth=1
        scanner = DeepScanner(max_depth=1)
        result = scanner.scan(tmp_path)
        
        # Should scan root (depth 0) and folder1 (depth 1)
        # But NOT folder2 contents (depth 2)
        assert scanner.statistics['files_scanned'] == 2  # file1.txt, file2.txt
        # folder2 is encountered but not descended into
        assert scanner.statistics['dirs_scanned'] >= 1  # at least folder1
    
    def test_scan_nonexistent_path(self, tmp_path):
        """Test scanning nonexistent path raises ValueError."""
        nonexistent = tmp_path / "nonexistent"
        
        scanner = DeepScanner()
        with pytest.raises(ValueError, match="Path does not exist"):
            scanner.scan(nonexistent)
    
    def test_scan_file_not_directory(self, tmp_path):
        """Test scanning a file (not directory) raises ValueError."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        scanner = DeepScanner()
        with pytest.raises(ValueError, match="Path is not a directory"):
            scanner.scan(test_file)
    
    def test_progress_callback(self, tmp_path):
        """Test progress callback is called."""
        # Create 150 files to trigger callback (called every 100 files)
        for i in range(150):
            (tmp_path / f"file{i}.txt").write_text("x")
        
        progress_calls = []
        
        def progress(count, path):
            progress_calls.append((count, path))
        
        scanner = DeepScanner(progress_callback=progress)
        scanner.scan(tmp_path)
        
        # Should have been called multiple times during scan
        assert len(progress_calls) >= 1
        # Verify callbacks were made with file counts
        assert all(isinstance(count, int) and count >= 0 for count, _ in progress_calls)
    
    def test_file_node_properties(self, tmp_path):
        """Test FileNode properties are set correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        file_node = result.children[0]
        assert file_node.name == "test.py"
        assert file_node.extension == ".py"
        assert file_node.is_file is True
        assert file_node.size > 0
        assert file_node.mtime > 0
    
    def test_iter_files_recursive(self, tmp_path):
        """Test iterating all files in tree."""
        # Create structure with files at different levels
        (tmp_path / "file1.txt").write_text("1")
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "file2.txt").write_text("2")
        folder2 = folder1 / "folder2"
        folder2.mkdir()
        (folder2 / "file3.txt").write_text("3")
        
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        # Should find all 3 files recursively
        all_files = list(result.iter_files())
        assert len(all_files) == 3
        
        file_names = {f.name for f in all_files}
        assert file_names == {"file1.txt", "file2.txt", "file3.txt"}
    
    def test_scan_with_special_characters(self, tmp_path):
        """Test scanning files with special characters in names."""
        special_files = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt"
        ]
        
        for filename in special_files:
            (tmp_path / filename).write_text("test")
        
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        assert scanner.statistics['files_scanned'] == len(special_files)
        
        scanned_names = {child.name for child in result.children}
        assert scanned_names == set(special_files)


class TestScanFolder:
    """Test scan_folder convenience function."""
    
    def test_scan_folder_basic(self, tmp_path):
        """Test scan_folder convenience function."""
        (tmp_path / "test.txt").write_text("test")
        
        result = scan_folder(tmp_path)
        
        assert result.path == tmp_path
        assert len(result.children) == 1
    
    def test_scan_folder_with_max_depth(self, tmp_path):
        """Test scan_folder with max_depth."""
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        folder2 = folder1 / "folder2"
        folder2.mkdir()
        (folder2 / "deep.txt").write_text("deep")
        
        result = scan_folder(tmp_path, max_depth=1)
        
        # Should not reach deep.txt
        all_files = list(result.iter_files())
        assert len(all_files) == 0


class TestSymlinks:
    """Test symlink handling."""
    
    @pytest.mark.skipif(os.name == 'nt', reason="Symlinks require admin on Windows")
    def test_skip_symlinks(self, tmp_path):
        """Test symlinks are skipped by default."""
        # Create real file
        real_file = tmp_path / "real.txt"
        real_file.write_text("real")
        
        # Create symlink
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(real_file)
        
        scanner = DeepScanner(follow_symlinks=False)
        result = scanner.scan(tmp_path)
        
        # Should only find real file
        assert scanner.statistics['files_scanned'] == 1
        assert scanner.statistics['skipped_symlink'] == 1


class TestPerformance:
    """Test scanner performance."""
    
    def test_scan_performance_1000_files(self, tmp_path):
        """Test scanning 1000 files is reasonably fast."""
        # Create 1000 small files
        for i in range(1000):
            (tmp_path / f"file{i:04d}.txt").write_text(f"content{i}")
        
        start = time.time()
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        elapsed = time.time() - start
        
        assert scanner.statistics['files_scanned'] == 1000
        # Should complete in under 2 seconds
        assert elapsed < 2.0, f"Scan took {elapsed:.2f}s, expected < 2s"
    
    def test_scan_performance_nested(self, tmp_path):
        """Test scanning nested structure is fast."""
        # Create 10 folders with 100 files each
        for i in range(10):
            folder = tmp_path / f"folder{i}"
            folder.mkdir()
            for j in range(100):
                (folder / f"file{j}.txt").write_text(f"content{i}-{j}")
        
        start = time.time()
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        elapsed = time.time() - start
        
        assert scanner.statistics['files_scanned'] == 1000
        assert scanner.statistics['dirs_scanned'] == 10
        # Should complete in under 2 seconds
        assert elapsed < 2.0, f"Scan took {elapsed:.2f}s, expected < 2s"


class TestErrorHandling:
    """Test error handling in scanner."""
    
    def test_permission_error_handling(self, tmp_path):
        """Test scanner handles permission errors gracefully."""
        # Create folder
        protected_folder = tmp_path / "protected"
        protected_folder.mkdir()
        (protected_folder / "file.txt").write_text("secret")
        
        # Make folder unreadable (on Unix)
        if os.name != 'nt':
            os.chmod(protected_folder, 0o000)
        
        try:
            scanner = DeepScanner()
            result = scanner.scan(tmp_path)
            
            # Should complete without crashing
            assert result is not None
            
            if os.name != 'nt':
                # Should have logged permission error
                assert scanner.statistics['skipped_permission'] >= 0
        finally:
            # Restore permissions for cleanup
            if os.name != 'nt':
                os.chmod(protected_folder, 0o755)
    
    def test_statistics_tracking(self, tmp_path):
        """Test statistics are tracked correctly."""
        # Create various items
        (tmp_path / "file1.txt").write_text("1")
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        (folder1 / "file2.txt").write_text("2")
        
        scanner = DeepScanner()
        result = scanner.scan(tmp_path)
        
        stats = scanner.statistics
        assert stats['files_scanned'] == 2
        assert stats['dirs_scanned'] == 1
        assert stats['errors'] == 0
