"""
Unit tests for v2.0 Context Builder.

Tests folder context analysis and redundancy detection.
"""

import pytest
from pathlib import Path
from src.core_v2.context_builder import ContextBuilder, analyze_folder_context, FolderContext
from src.core_v2.models import FileNode, RuleResult


class TestContextBuilder:
    """Test ContextBuilder class."""
    
    def test_initialization(self):
        """Test context builder initialization."""
        builder = ContextBuilder()
        
        # Should have hint mappings
        assert len(builder._category_hints) > 0
        assert len(builder._subcategory_hints) > 0
        assert len(builder._extension_subcategory_map) > 0
    
    def test_build_context_empty_folder(self, tmp_path):
        """Test building context for empty folder."""
        folder = tmp_path / "empty"
        folder.mkdir()
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),  # Empty
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        assert context.path == folder
        assert context.name == "empty"
        assert context.file_count == 0
        assert context.dominant_extension is None
    
    def test_analyze_folder_name_documents(self, tmp_path):
        """Test folder name analysis for Documents."""
        folder = tmp_path / "Documents"
        folder.mkdir()
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        assert context.implies_category == "Documents"
    
    def test_analyze_folder_name_mp3(self, tmp_path):
        """Test folder name analysis for MP3."""
        folder = tmp_path / "MP3"
        folder.mkdir()
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        assert context.implies_subcategory == "MP3"
        assert context.implies_category == "Audio"  # Inferred from subcategory
    
    def test_analyze_folder_name_python(self, tmp_path):
        """Test folder name analysis for Python."""
        folder = tmp_path / "Python Scripts"
        folder.mkdir()
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        assert context.implies_subcategory == "Python"
        assert context.implies_category == "Code"
    
    def test_analyze_contents_single_type(self, tmp_path):
        """Test analyzing folder contents with single file type."""
        folder = tmp_path / "music"
        folder.mkdir()
        
        # Create mock FileNodes
        files = tuple([
            FileNode(
                path=folder / f"song{i}.mp3",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            )
            for i in range(10)
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=files,  # Add files as children
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        assert context.file_count == 10
        assert context.dominant_extension == ".mp3"
        assert context.extension_counts[".mp3"] == 10
    
    def test_analyze_contents_mixed_types(self, tmp_path):
        """Test analyzing folder with mixed file types."""
        folder = tmp_path / "mixed"
        folder.mkdir()
        
        files = tuple([
            # 6 MP3 files (60%)
            *[FileNode(
                path=folder / f"song{i}.mp3",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(6)],
            # 4 TXT files (40%)
            *[FileNode(
                path=folder / f"note{i}.txt",
                is_dir=False,
                size=100,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(4)],
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=files,
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        assert context.file_count == 10
        assert context.dominant_extension == ".mp3"  # >50%
        assert context.extension_counts[".mp3"] == 6
        assert context.extension_counts[".txt"] == 4
    
    def test_would_create_redundancy_subcategory_match(self, tmp_path):
        """Test redundancy detection when parent subcategory matches file."""
        folder = tmp_path / "MP3"
        folder.mkdir()
        
        # File being placed
        file_node = FileNode(
            path=folder / "song.mp3",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        # Rule result for the file
        rule_result = RuleResult(
            file=file_node,
            category="Audio",
            subcategory="MP3",
            confidence=0.9,
            matched_rule=".mp3",
            context_hint="MP3 audio"
        )
        
        # Build folder context (will detect MP3 from folder name)
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        folder_context = builder.build_context(folder_node)
        
        is_redundant = builder.would_create_redundancy(
            parent_context=folder_context,
            rule_result=rule_result
        )
        
        # Should detect: MP3 folder + MP3 file = redundant
        assert is_redundant is True
    
    def test_would_create_redundancy_extension_match(self, tmp_path):
        """Test redundancy detection when parent implies extension."""
        folder = tmp_path / "pdf"
        folder.mkdir()
        
        file_node = FileNode(
            path=folder / "doc.pdf",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        rule_result = RuleResult(
            file=file_node,
            category="Documents",
            subcategory="PDF",
            confidence=0.9,
            matched_rule=".pdf",
            context_hint="PDF document"
        )
        
        # Build folder context (folder named "pdf" implies .pdf extension)
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        folder_context = builder.build_context(folder_node)
        
        is_redundant = builder.would_create_redundancy(
            parent_context=folder_context,
            rule_result=rule_result
        )
        
        # Should detect: "pdf" folder + .pdf file = redundant
        assert is_redundant is True
    
    def test_would_create_redundancy_dominant_extension(self, tmp_path):
        """Test redundancy detection with dominant extension."""
        folder = tmp_path / "music"
        folder.mkdir()
        
        # New MP3 file being placed
        new_file = FileNode(
            path=folder / "new_song.mp3",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=0
        )
        
        rule_result = RuleResult(
            file=new_file,
            category="Audio",
            subcategory="MP3",
            confidence=0.9,
            matched_rule=".mp3",
            context_hint="MP3 audio"
        )
        
        # Folder dominated by MP3 files (80%)
        existing_files = tuple([
            *[FileNode(
                path=folder / f"song{i}.mp3",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(8)],
            *[FileNode(
                path=folder / f"track{i}.flac",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(2)],
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=existing_files,
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        folder_context = builder.build_context(folder_node)
        
        is_redundant = builder.would_create_redundancy(
            parent_context=folder_context,
            rule_result=rule_result
        )
        
        # Should detect: folder dominated by MP3 + new MP3 = redundant
        assert is_redundant is True
    
    def test_no_redundancy_category_only(self, tmp_path):
        """Test NO redundancy when only category matches (not subcategory)."""
        folder = tmp_path / "Documents"
        folder.mkdir()
        
        file_node = FileNode(
            path=folder / "doc.pdf",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        rule_result = RuleResult(
            file=file_node,
            category="Documents",
            subcategory="PDF",
            confidence=0.9,
            matched_rule=".pdf",
            context_hint="PDF document"
        )
        
        # Build folder context (Documents folder has category but not subcategory)
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        folder_context = builder.build_context(folder_node)
        
        is_redundant = builder.would_create_redundancy(
            parent_context=folder_context,
            rule_result=rule_result
        )
        
        # Should NOT detect redundancy: Documents/PDF is acceptable
        assert is_redundant is False
    
    def test_no_redundancy_mixed_folder(self, tmp_path):
        """Test NO redundancy for mixed-type folder."""
        folder = tmp_path / "work"
        folder.mkdir()
        
        file_node = FileNode(
            path=folder / "doc.pdf",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        rule_result = RuleResult(
            file=file_node,
            category="Documents",
            subcategory="PDF",
            confidence=0.9,
            matched_rule=".pdf",
            context_hint="PDF document"
        )
        
        # Mixed folder (no dominant extension)
        existing_files = tuple([
            *[FileNode(
                path=folder / f"doc{i}.pdf",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(3)],
            *[FileNode(
                path=folder / f"report{i}.docx",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(3)],
            *[FileNode(
                path=folder / f"sheet{i}.xlsx",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(4)],
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=existing_files,
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        folder_context = builder.build_context(folder_node)
        
        is_redundant = builder.would_create_redundancy(
            parent_context=folder_context,
            rule_result=rule_result
        )
        
        # Should NOT detect redundancy: mixed folder is fine
        assert is_redundant is False
    
    def test_get_context_hint_subcategory(self, tmp_path):
        """Test context hint generation."""
        folder = tmp_path / "MP3"
        folder.mkdir()
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        hint = builder.get_context_hint(folder_node)  # Pass FileNode, not context
        
        assert "MP3" in hint
        assert "Audio" in hint or "Type" in hint
    
    def test_get_context_hint_dominant(self, tmp_path):
        """Test context hint with dominant extension."""
        folder = tmp_path / "photos"
        folder.mkdir()
        
        files = tuple([
            *[FileNode(
                path=folder / f"img{i}.jpg",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(18)],
            *[FileNode(
                path=folder / f"img{i}.png",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(2)],
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=files,
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        hint = builder.get_context_hint(folder_node)  # Pass FileNode, not context
        
        assert "jpg" in hint.lower()
        assert "mostly" in hint.lower()  # Should say "Mostly .jpg files"


class TestConvenienceFunction:
    """Test analyze_folder_context convenience function."""
    
    def test_analyze_folder_context(self, tmp_path):
        """Test convenience function."""
        folder = tmp_path / "MP3"
        folder.mkdir()
        
        files = tuple([
            FileNode(
                path=folder / f"song{i}.mp3",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            )
            for i in range(5)
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=files,
            depth=0,
            root_distance=0
        )
        
        context = analyze_folder_context(folder_node)
        
        assert context.name == "MP3"
        assert context.implies_subcategory == "MP3"
        assert context.file_count == 5
        assert context.dominant_extension == ".mp3"


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_case_insensitive_folder_names(self, tmp_path):
        """Test that folder name matching is case-insensitive."""
        builder = ContextBuilder()
        
        # Lowercase
        folder_lower = tmp_path / "mp3_lower"
        folder_lower.mkdir()
        node_lower = FileNode(
            path=folder_lower,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        context_lower = builder.build_context(node_lower)
        
        # Uppercase
        folder_upper = tmp_path / "MP3_UPPER"
        folder_upper.mkdir()
        node_upper = FileNode(
            path=folder_upper,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        context_upper = builder.build_context(node_upper)
        
        # Both should imply MP3 subcategory (because they contain "mp3" in lowercase)
        assert context_lower.implies_subcategory == "MP3"
        assert context_upper.implies_subcategory == "MP3"
    
    def test_folder_name_with_spaces(self, tmp_path):
        """Test folder names with spaces."""
        folder = tmp_path / "Python Scripts"
        folder.mkdir()
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        # Should still detect "python" in the name
        assert context.implies_subcategory == "Python"
    
    def test_threshold_boundary_50_percent(self, tmp_path):
        """Test dominant extension exactly at 50% boundary."""
        folder = tmp_path / "mixed"
        folder.mkdir()
        
        files = tuple([
            # 5 MP3 files (50%)
            *[FileNode(
                path=folder / f"song{i}.mp3",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(5)],
            # 5 FLAC files (50%)
            *[FileNode(
                path=folder / f"song{i}.flac",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(5)],
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=files,
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        # At exactly 50%, should not have dominant extension
        assert context.dominant_extension is None
    
    def test_threshold_boundary_51_percent(self, tmp_path):
        """Test dominant extension just above 50%."""
        folder = tmp_path / "mostly_mp3"
        folder.mkdir()
        
        files = tuple([
            # 51 MP3 files (51%)
            *[FileNode(
                path=folder / f"song{i}.mp3",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(51)],
            # 49 FLAC files (49%)
            *[FileNode(
                path=folder / f"song{i}.flac",
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=1,
                root_distance=0
            ) for i in range(49)],
        ])
        
        folder_node = FileNode(
            path=folder,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=files,
            depth=0,
            root_distance=0
        )
        
        builder = ContextBuilder()
        context = builder.build_context(folder_node)
        
        # At 51%, should have dominant extension
        assert context.dominant_extension == ".mp3"
