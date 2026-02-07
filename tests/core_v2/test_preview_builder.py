"""Tests for Preview Builder v2."""

import pytest
from pathlib import Path
from src.core_v2.preview_builder import (
    PreviewBuilderV2,
    PreviewConfig,
    PreviewStats,
    build_preview
)
from src.core_v2.models import PlacementDecision, AIResult, FileNode, DecisionSource


def make_file_node(path: Path) -> FileNode:
    """Helper to create a FileNode for testing."""
    return FileNode(
        path=path,
        is_dir=False,
        size=1024,
        mtime=1234567890.0,
        parent=None,
        children=tuple(),
        depth=0,
        root_distance=0
    )


class TestPreviewConfig:
    """Test preview configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PreviewConfig()
        assert config.show_confidence is True
        assert config.show_ai_groups is True
        assert config.max_files_per_folder == 10
        assert config.show_hidden is False
        assert config.color_output is True
        assert config.export_path is None
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PreviewConfig(
            show_confidence=False,
            max_files_per_folder=5,
            color_output=False
        )
        assert config.show_confidence is False
        assert config.max_files_per_folder == 5
        assert config.color_output is False


class TestPreviewBuilderV2:
    """Test preview builder core functionality."""
    
    def test_initialization(self):
        """Test builder initialization."""
        builder = PreviewBuilderV2()
        assert builder.config is not None
        assert isinstance(builder.config, PreviewConfig)
    
    def test_initialization_with_config(self):
        """Test builder initialization with custom config."""
        config = PreviewConfig(color_output=False)
        builder = PreviewBuilderV2(config)
        assert builder.config.color_output is False
    
    def test_empty_placements(self):
        """Test preview with no placements."""
        builder = PreviewBuilderV2()
        preview = builder.build_preview([])
        assert "No files to organize" in preview
        assert "AutoFolder AI" in preview
    
    def test_build_simple_preview(self):
        """Test building simple preview."""
        file_node = make_file_node(Path("D:/Downloads/file1.txt"))
        placements = [
            PlacementDecision(
                file=file_node,
                target=Path("D:/Organized/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        preview = builder.build_preview(placements)
        
        assert "AutoFolder AI" in preview
        assert "Statistics" in preview
        assert "Folder Structure" in preview
        assert "file1.txt" in preview
    
    def test_build_preview_with_ai_groups(self):
        """Test preview with AI grouping results."""
        file1 = make_file_node(Path("D:/vacation1.jpg"))
        file2 = make_file_node(Path("D:/vacation2.jpg"))
        placements = [
            PlacementDecision(
                file=file1,
                target=Path("D:/Images/Vacation/vacation1.jpg"),
                reason="Image classification",
                source=DecisionSource.RULE
            ),
            PlacementDecision(
                file=file2,
                target=Path("D:/Images/Vacation/vacation2.jpg"),
                reason="Image classification",
                source=DecisionSource.RULE
            )
        ]
        
        ai_results = [
            AIResult(
                file=file1,
                group="Vacation 2025",
                similar_files=(file1, file2),
                confidence=0.85,
                context_used="filename_only"
            ),
            AIResult(
                file=file2,
                group="Vacation 2025",
                similar_files=(file1, file2),
                confidence=0.85,
                context_used="filename_only"
            )
        ]
        
        builder = PreviewBuilderV2()
        preview = builder.build_preview(placements, ai_results)
        
        assert "AI Groupings" in preview
        assert "Vacation 2025" in preview
        assert "2 files" in preview


class TestTreeBuilding:
    """Test tree structure building."""
    
    def test_build_tree_single_file(self):
        """Test building tree with single file."""
        file_node = make_file_node(Path("file1.txt"))
        placements = [
            PlacementDecision(
                file=file_node,
                target=Path("D:/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        tree = builder._build_tree(placements)
        
        assert "D:\\" in tree
        assert "Documents" in tree["D:\\"]
        assert len(tree["D:\\"]["Documents"]["_files"]) == 1
        assert tree["D:\\"]["Documents"]["_files"][0]["name"] == "file1.txt"
    
    def test_build_tree_nested_folders(self):
        """Test building tree with nested folders."""
        file_node = make_file_node(Path("file1.txt"))
        placements = [
            PlacementDecision(
                file=file_node,
                target=Path("D:/Documents/Work/2025/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        tree = builder._build_tree(placements)
        
        assert "D:\\" in tree
        assert "Documents" in tree["D:\\"]
        assert "Work" in tree["D:\\"]["Documents"]
        assert "2025" in tree["D:\\"]["Documents"]["Work"]
        assert len(tree["D:\\"]["Documents"]["Work"]["2025"]["_files"]) == 1
    
    def test_build_tree_multiple_files(self):
        """Test building tree with multiple files."""
        file1 = make_file_node(Path("file1.txt"))
        file2 = make_file_node(Path("file2.txt"))
        image1 = make_file_node(Path("image1.jpg"))
        placements = [
            PlacementDecision(
                file=file1,
                target=Path("D:/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            ),
            PlacementDecision(
                file=file2,
                target=Path("D:/Documents/file2.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            ),
            PlacementDecision(
                file=image1,
                target=Path("D:/Images/image1.jpg"),
                reason="Image classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        tree = builder._build_tree(placements)
        
        assert "D:\\" in tree
        assert "Documents" in tree["D:\\"]
        assert "Images" in tree["D:\\"]
        assert len(tree["D:\\"]["Documents"]["_files"]) == 2
        assert len(tree["D:\\"]["Images"]["_files"]) == 1


class TestTreeFormatting:
    """Test tree formatting."""
    
    def test_format_tree_single_level(self):
        """Test formatting single-level tree."""
        tree = {
            "Documents": {
                "_files": [{"name": "file1.txt", "confidence": 0.8, "ai_group": None, "protected": False}]
            }
        }
        
        builder = PreviewBuilderV2(PreviewConfig(color_output=False))
        lines = builder._format_tree(tree)
        
        assert any("Documents/" in line for line in lines)
        assert any("file1.txt" in line for line in lines)
    
    def test_format_tree_with_confidence(self):
        """Test formatting tree with confidence indicators."""
        tree = {
            "Documents": {
                "_files": [
                    {"name": "file1.txt", "confidence": 0.9, "ai_group": None, "protected": False}
                ]
            }
        }
        
        builder = PreviewBuilderV2(PreviewConfig(color_output=False))
        lines = builder._format_tree(tree)
        
        # Should show confidence percentage
        assert any("[90%]" in line for line in lines)
    
    def test_format_tree_truncation(self):
        """Test tree formatting with file truncation."""
        files = [
            {"name": f"file{i}.txt", "confidence": 0.8, "ai_group": None, "protected": False}
            for i in range(15)
        ]
        tree = {
            "Documents": {"_files": files}
        }
        
        builder = PreviewBuilderV2(PreviewConfig(max_files_per_folder=5, color_output=False))
        lines = builder._format_tree(tree)
        
        # Should show truncation message
        assert any("more files" in line for line in lines)
        # Should show exactly max_files_per_folder files plus truncation line
        file_lines = [l for l in lines if "file" in l and "Documents" not in l]
        assert len(file_lines) <= 6  # 5 files + 1 truncation line


class TestStatistics:
    """Test statistics calculation."""
    
    def test_calculate_basic_stats(self):
        """Test basic statistics calculation."""
        file1 = make_file_node(Path("D:/Downloads/file1.txt"))
        file2 = make_file_node(Path("D:/Downloads/file2.txt"))
        placements = [
            PlacementDecision(
                file=file1,
                target=Path("D:/Organized/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            ),
            PlacementDecision(
                file=file2,
                target=Path("D:/Organized/Documents/file2.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        stats = builder._calculate_stats(placements, [])
        
        assert stats.total_files == 2
        assert stats.files_moved == 2
        assert stats.protected_files == 0
    
    def test_calculate_stats_with_ai_groups(self):
        """Test statistics with AI grouping results."""
        file1 = make_file_node(Path("file1.txt"))
        file2 = make_file_node(Path("file2.txt"))
        file3 = make_file_node(Path("file3.txt"))
        placements = [
            PlacementDecision(
                file=file1,
                target=Path("D:/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            ),
            PlacementDecision(
                file=file2,
                target=Path("D:/Documents/file2.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            ),
            PlacementDecision(
                file=file3,
                target=Path("D:/Documents/file3.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        ai_results = [
            AIResult(
                file=file1,
                group="Group1",
                similar_files=(file1, file2),
                confidence=0.8,
                context_used="filename_only"
            ),
            AIResult(
                file=file2,
                group="Group1",
                similar_files=(file1, file2),
                confidence=0.9,
                context_used="filename_only"
            ),
            AIResult(
                file=file3,
                group="Group2",
                similar_files=(file3, make_file_node(Path("file4.txt"))),
                confidence=0.85,
                context_used="filename_only"
            )
        ]
        
        builder = PreviewBuilderV2()
        stats = builder._calculate_stats(placements, ai_results)
        
        assert stats.total_files == 3
        assert stats.ai_groups_found == 2
    
    def test_calculate_stats_with_protected_files(self):
        """Test statistics with protected files."""
        file1 = make_file_node(Path("D:/file1.txt"))
        file2 = make_file_node(Path("file2.txt"))
        placements = [
            PlacementDecision(
                file=file1,
                target=Path("D:/file1.txt"),
                reason="Protected file",
                source=DecisionSource.PROTECTED
            ),
            PlacementDecision(
                file=file2,
                target=Path("D:/Documents/file2.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        stats = builder._calculate_stats(placements, [])
        
        assert stats.total_files == 2
        assert stats.protected_files == 1
        assert stats.files_moved == 1  # Only non-protected file moved


class TestColorization:
    """Test terminal color output."""
    
    def test_colorize_enabled(self):
        """Test colorization when enabled."""
        builder = PreviewBuilderV2(PreviewConfig(color_output=True))
        colored = builder._colorize("test", 'high')
        
        assert '\033[' in colored  # Contains ANSI code
        assert 'test' in colored
    
    def test_colorize_disabled(self):
        """Test colorization when disabled."""
        builder = PreviewBuilderV2(PreviewConfig(color_output=False))
        colored = builder._colorize("test", 'high')
        
        assert '\033[' not in colored  # No ANSI codes
        assert colored == "test"
    
    def test_confidence_colors(self):
        """Test confidence-based color selection."""
        builder = PreviewBuilderV2()
        
        assert builder._get_confidence_color(0.95) == 'high'
        assert builder._get_confidence_color(0.80) == 'medium'
        assert builder._get_confidence_color(0.60) == 'low'


class TestExport:
    """Test export functionality."""
    
    def test_export_to_file(self, tmp_path):
        """Test exporting preview to file."""
        file_node = make_file_node(Path("file1.txt"))
        placements = [
            PlacementDecision(
                file=file_node,
                target=Path("D:/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        builder = PreviewBuilderV2()
        preview = builder.build_preview(placements)
        
        export_path = tmp_path / "preview.txt"
        builder.export_preview(preview, export_path)
        
        assert export_path.exists()
        content = export_path.read_text(encoding='utf-8')
        assert "file1.txt" in content
    
    def test_export_strips_colors(self, tmp_path):
        """Test that export strips ANSI color codes."""
        builder = PreviewBuilderV2(PreviewConfig(color_output=True))
        colored_text = builder._colorize("test", 'high')
        
        export_path = tmp_path / "test.txt"
        builder.export_preview(colored_text, export_path)
        
        content = export_path.read_text(encoding='utf-8')
        assert '\033[' not in content  # No ANSI codes
        assert 'test' in content


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_convenience_function(self):
        """Test build_preview convenience function."""
        file_node = make_file_node(Path("file1.txt"))
        placements = [
            PlacementDecision(
                file=file_node,
                target=Path("D:/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        preview = build_preview(placements)
        
        assert "AutoFolder AI" in preview
        assert "file1.txt" in preview
    
    def test_convenience_function_with_config(self):
        """Test convenience function with custom config."""
        file_node = make_file_node(Path("file1.txt"))
        placements = [
            PlacementDecision(
                file=file_node,
                target=Path("D:/Documents/file1.txt"),
                reason="Document classification",
                source=DecisionSource.RULE
            )
        ]
        
        config = PreviewConfig(color_output=False)
        preview = build_preview(placements, config=config)
        
        assert '\033[' not in preview  # No color codes
