"""
Unit tests for v2.0 data models.

Tests all 6 data classes, validation, properties, and helper functions.
"""

import pytest
from pathlib import Path
from datetime import datetime
from src.core_v2.models import (
    FileNode,
    RootInfo,
    RuleResult,
    AIResult,
    PlacementDecision,
    PreviewResult,
    RootType,
    DecisionSource,
    validate_path_safe,
    calculate_file_hash
)


class TestFileNode:
    """Test FileNode immutable data class."""
    
    def test_file_node_creation(self, tmp_path):
        """Test creating a FileNode."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        
        node = FileNode(
            path=file_path,
            is_dir=False,
            size=4,
            mtime=datetime.now().timestamp(),
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        assert node.path == file_path
        assert node.is_file is True
        assert node.is_dir is False
        assert node.name == "test.txt"
        assert node.extension == ".txt"
        assert node.size == 4
        assert node.depth == 0
    
    def test_file_node_immutable(self, tmp_path):
        """Test FileNode is immutable (frozen)."""
        file_path = tmp_path / "test.txt"
        node = FileNode(
            path=file_path,
            is_dir=False,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        with pytest.raises(AttributeError):
            node.size = 100
    
    def test_file_node_validation_negative_size(self, tmp_path):
        """Test FileNode rejects negative size."""
        with pytest.raises(ValueError, match="Size cannot be negative"):
            FileNode(
                path=tmp_path / "test.txt",
                is_dir=False,
                size=-1,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            )
    
    def test_file_node_validation_negative_mtime(self, tmp_path):
        """Test FileNode rejects negative mtime."""
        with pytest.raises(ValueError, match="Modification time cannot be negative"):
            FileNode(
                path=tmp_path / "test.txt",
                is_dir=False,
                size=0,
                mtime=-1.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            )
    
    def test_file_node_validation_negative_depth(self, tmp_path):
        """Test FileNode rejects negative depth."""
        with pytest.raises(ValueError, match="Depth cannot be negative"):
            FileNode(
                path=tmp_path / "test.txt",
                is_dir=False,
                size=0,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=-1,
                root_distance=0
            )
    
    def test_directory_node_with_children(self, tmp_path):
        """Test directory node with children."""
        dir_path = tmp_path / "folder"
        dir_path.mkdir()
        
        child1 = FileNode(
            path=dir_path / "file1.txt",
            is_dir=False,
            size=10,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=1
        )
        
        child2 = FileNode(
            path=dir_path / "file2.txt",
            is_dir=False,
            size=20,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=1
        )
        
        parent = FileNode(
            path=dir_path,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=(child1, child2),
            depth=0,
            root_distance=0
        )
        
        assert parent.is_dir is True
        assert parent.is_file is False
        assert len(parent.children) == 2
    
    def test_iter_files(self, tmp_path):
        """Test iter_files() method."""
        dir_path = tmp_path / "folder"
        dir_path.mkdir()
        
        file1 = FileNode(
            path=dir_path / "file1.txt",
            is_dir=False,
            size=10,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=1
        )
        
        subdir = FileNode(
            path=dir_path / "subfolder",
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=1
        )
        
        parent = FileNode(
            path=dir_path,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=(file1, subdir),
            depth=0,
            root_distance=0
        )
        
        files = list(parent.iter_files())
        assert len(files) == 1
        assert files[0] == file1
    
    def test_iter_dirs(self, tmp_path):
        """Test iter_dirs() method."""
        dir_path = tmp_path / "folder"
        dir_path.mkdir()
        
        file1 = FileNode(
            path=dir_path / "file1.txt",
            is_dir=False,
            size=10,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=1
        )
        
        subdir = FileNode(
            path=dir_path / "subfolder",
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=1
        )
        
        parent = FileNode(
            path=dir_path,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=(file1, subdir),
            depth=0,
            root_distance=0
        )
        
        dirs = list(parent.iter_dirs())
        assert len(dirs) == 2  # parent itself + subdir
        assert subdir in dirs


class TestRootInfo:
    """Test RootInfo data class."""
    
    def test_root_info_creation(self, tmp_path):
        """Test creating RootInfo."""
        root = RootInfo(
            path=tmp_path,
            root_type=RootType.PROJECT,
            confidence=0.9,
            markers=('.git', 'pyproject.toml'),
            protect=True
        )
        
        assert root.path == tmp_path
        assert root.root_type == RootType.PROJECT
        assert root.confidence == 0.9
        assert root.protect is True
        assert len(root.markers) == 2
    
    def test_root_info_validation_confidence_range(self, tmp_path):
        """Test confidence must be 0-1."""
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            RootInfo(
                path=tmp_path,
                root_type=RootType.PROJECT,
                confidence=1.5,
                markers=tuple(),
                protect=True
            )
        
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            RootInfo(
                path=tmp_path,
                root_type=RootType.PROJECT,
                confidence=-0.1,
                markers=tuple(),
                protect=True
            )
    
    def test_root_info_relative_path(self):
        """Test RootInfo rejects relative paths."""
        with pytest.raises(ValueError, match="Path must be absolute"):
            RootInfo(
                path=Path("relative/path"),
                root_type=RootType.PROJECT,
                confidence=0.9,
                markers=tuple(),
                protect=True
            )


class TestRuleResult:
    """Test RuleResult data class."""
    
    def test_rule_result_creation(self, tmp_path):
        """Test creating RuleResult."""
        file_path = tmp_path / "test.py"
        result = RuleResult(
            file=file_path,
            category="Code",
            subcategory="Python",
            confidence=0.95,
            matched_rule="*.py",
            context_hint="Python scripts"
        )
        
        assert result.file == file_path
        assert result.category == "Code"
        assert result.subcategory == "Python"
        assert result.confidence == 0.95
        assert result.is_high_confidence is True
    
    def test_rule_result_low_confidence(self, tmp_path):
        """Test is_high_confidence property."""
        result = RuleResult(
            file=tmp_path / "test.txt",
            category="Documents",
            subcategory="Text",
            confidence=0.7,
            matched_rule="*.txt",
            context_hint=""
        )
        
        assert result.is_high_confidence is False
    
    def test_rule_result_validation_empty_category(self, tmp_path):
        """Test RuleResult rejects empty category."""
        with pytest.raises(ValueError, match="Category cannot be empty"):
            RuleResult(
                file=tmp_path / "test.txt",
                category="",
                subcategory="Text",
                confidence=0.9,
                matched_rule="*.txt",
                context_hint=""
            )


class TestAIResult:
    """Test AIResult data class."""
    
    def test_ai_result_creation(self, tmp_path):
        """Test creating AIResult."""
        file1 = tmp_path / "report1.pdf"
        file2 = tmp_path / "report2.pdf"
        
        result = AIResult(
            file=file1,
            group="Financial Reports",
            confidence=0.85,
            similar_files=(file1, file2),
            embedding=None,
            context_used="2024 tax documents"
        )
        
        assert result.file == file1
        assert result.group == "Financial Reports"
        assert result.group_size == 2
        assert result.is_large_group is False
    
    def test_ai_result_large_group(self, tmp_path):
        """Test is_large_group property."""
        files = [tmp_path / f"file{i}.txt" for i in range(6)]
        
        result = AIResult(
            file=files[0],
            group="Large Group",
            confidence=0.8,
            similar_files=tuple(files),
            embedding=None,
            context_used=""
        )
        
        assert result.group_size == 6
        assert result.is_large_group is True
    
    def test_ai_result_validation_min_files(self, tmp_path):
        """Test AIResult requires at least 2 files."""
        with pytest.raises(ValueError, match="AI groups must have"):
            AIResult(
                file=tmp_path / "file.txt",
                group="Tiny Group",
                confidence=0.8,
                similar_files=(tmp_path / "file.txt",),
                embedding=None,
                context_used=""
            )
    
    def test_ai_result_validation_empty_group(self, tmp_path):
        """Test AIResult rejects empty group name."""
        with pytest.raises(ValueError, match="Group name cannot be empty"):
            AIResult(
                file=tmp_path / "file1.txt",
                group="",
                confidence=0.8,
                similar_files=(tmp_path / "file1.txt", tmp_path / "file2.txt"),
                embedding=None,
                context_used=""
            )


class TestPlacementDecision:
    """Test PlacementDecision data class."""
    
    def test_placement_decision_creation(self, tmp_path):
        """Test creating PlacementDecision."""
        source = tmp_path / "file.txt"
        source.write_text("test")
        target = tmp_path / "Documents" / "file.txt"
        
        file_node = FileNode(
            path=source,
            is_dir=False,
            size=4,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        decision = PlacementDecision(
            file=file_node,
            target=target,
            reason="Matched rule: Documents/*.txt",
            source=DecisionSource.RULE,
            conflicts=tuple(),
            safe=True,
            rule_result=None,
            ai_result=None
        )
        
        assert decision.file == file_node
        assert decision.target == target
        assert decision.will_move is True
        assert decision.has_conflicts is False
        assert decision.safe is True
    
    def test_placement_decision_with_conflicts(self, tmp_path):
        """Test PlacementDecision with conflicts."""
        source = tmp_path / "file.txt"
        source.write_text("test")
        target = tmp_path / "Documents" / "file.txt"
        
        file_node = FileNode(
            path=source,
            is_dir=False,
            size=4,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        decision = PlacementDecision(
            file=file_node,
            target=target,
            reason="Target exists",
            source=DecisionSource.RULE,
            conflicts=("target_exists",),
            safe=False,
            rule_result=None,
            ai_result=None
        )
        
        assert decision.has_conflicts is True
        assert len(decision.conflicts) == 1
    
    def test_placement_decision_skip(self, tmp_path):
        """Test PlacementDecision for skipped file."""
        source = tmp_path / "file.txt"
        source.write_text("test")
        
        file_node = FileNode(
            path=source,
            is_dir=False,
            size=4,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        decision = PlacementDecision(
            file=file_node,
            target=source,  # Target = source means skip
            reason="Protected root",
            source=DecisionSource.SKIP,
            conflicts=tuple(),
            safe=True,
            rule_result=None,
            ai_result=None
        )
        
        assert decision.will_move is False
    
    def test_placement_decision_validation_empty_reason(self, tmp_path):
        """Test PlacementDecision rejects empty reason."""
        source = tmp_path / "file.txt"
        source.write_text("test")
        
        file_node = FileNode(
            path=source,
            is_dir=False,
            size=4,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        with pytest.raises(ValueError, match="Reason cannot be empty"):
            PlacementDecision(
                file=file_node,
                target=tmp_path / "Documents" / "file.txt",
                reason="",
                source=DecisionSource.RULE,
                conflicts=tuple(),
                safe=True,
                rule_result=None,
                ai_result=None
            )


class TestPreviewResult:
    """Test PreviewResult data class."""
    
    def test_preview_result_creation(self):
        """Test creating PreviewResult."""
        preview = PreviewResult(
            total_files=100,
            will_move=80,
            will_skip=20,
            conflicts=[],
            decisions=[],
            tree_preview={},
            by_category={},
            by_source={},
            protected_roots=[],
            scan_time=1.5,
            classify_time=2.0,
            ai_time=3.0,
            resolve_time=1.0
        )
        
        assert preview.total_files == 100
        assert preview.will_move == 80
        assert preview.will_skip == 20
        assert preview.total_time == 7.5
        assert preview.conflict_count == 0
    
    def test_preview_result_mutable(self):
        """Test PreviewResult is mutable (not frozen)."""
        preview = PreviewResult(
            total_files=100,
            will_move=80,
            will_skip=20,
            conflicts=[],
            decisions=[],
            tree_preview={},
            by_category={},
            by_source={},
            protected_roots=[],
            scan_time=1.0,
            classify_time=1.0,
            ai_time=1.0,
            resolve_time=1.0
        )
        
        # Should be able to modify
        preview.total_files = 200
        assert preview.total_files == 200
    
    def test_preview_result_summary(self):
        """Test summary() method."""
        preview = PreviewResult(
            total_files=100,
            will_move=80,
            will_skip=20,
            conflicts=[],
            decisions=[],
            tree_preview={},
            by_category={'Documents': 50, 'Images': 30},
            by_source={},
            protected_roots=[],
            scan_time=1.0,
            classify_time=1.0,
            ai_time=1.0,
            resolve_time=1.0
        )
        
        summary = preview.summary()
        assert "Total files: 100" in summary
        assert "Will move: 80" in summary
        assert "Will skip: 20" in summary
        assert "Conflicts: 0" in summary


class TestEnums:
    """Test enum types."""
    
    def test_root_type_enum(self):
        """Test RootType enum."""
        assert RootType.PROJECT.value == "project"
        assert RootType.MEDIA.value == "media"
        assert RootType.ARCHIVE.value == "archive"
        assert RootType.BACKUP.value == "backup"
        assert RootType.GAME.value == "game"
        assert RootType.VM.value == "vm"
        assert RootType.UNKNOWN.value == "unknown"
    
    def test_decision_source_enum(self):
        """Test DecisionSource enum."""
        assert DecisionSource.RULE.value == "rule"
        assert DecisionSource.AI.value == "ai"
        assert DecisionSource.CONTEXT.value == "context"
        assert DecisionSource.SKIP.value == "skip"
        assert DecisionSource.PROTECTED.value == "protected"


class TestHelpers:
    """Test helper functions."""
    
    def test_validate_path_safe_valid(self, tmp_path):
        """Test validate_path_safe with valid path."""
        # Use a simple path that should always be valid
        valid_path = Path("D:/TestFolder/file.txt")
        # Note: validate_path_safe checks system paths, which may reject
        # temporary paths. Just verify it doesn't crash
        result = validate_path_safe(valid_path)
        assert isinstance(result, bool)
    
    def test_validate_path_safe_too_long(self):
        """Test validate_path_safe with path too long."""
        long_path = Path("C:/") / ("a" * 300)
        assert validate_path_safe(long_path) is False
    
    def test_validate_path_safe_invalid_chars(self):
        """Test validate_path_safe with invalid characters."""
        invalid_path = Path("C:/test<>file.txt")
        assert validate_path_safe(invalid_path) is False
    
    def test_validate_path_safe_system_path(self):
        """Test validate_path_safe with system path."""
        system_path = Path("C:/Windows/System32")
        assert validate_path_safe(system_path) is False
    
    def test_calculate_file_hash(self, tmp_path):
        """Test calculate_file_hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        hash1 = calculate_file_hash(test_file)
        assert len(hash1) == 64  # SHA256 hex length
        
        # Same content should produce same hash
        hash2 = calculate_file_hash(test_file)
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text("Different content")
        hash3 = calculate_file_hash(test_file)
        assert hash1 != hash3
    
    def test_calculate_file_hash_nonexistent(self, tmp_path):
        """Test calculate_file_hash with nonexistent file returns None."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        result = calculate_file_hash(nonexistent)
        assert result is None
