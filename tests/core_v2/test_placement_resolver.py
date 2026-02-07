"""
Unit tests for v2.0 Placement Resolver.

Tests the CRITICAL component with 5 anti-redundancy rules.
"""

import pytest
from pathlib import Path
from src.core_v2.placement_resolver import (
    PlacementResolver, PlacementConfig, resolve_file_placements
)
from src.core_v2.models import FileNode, RuleResult, DecisionSource


class TestPlacementConfig:
    """Test PlacementConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PlacementConfig()
        
        assert config.min_group_size == 5
        assert config.max_depth == 3
        assert config.merge_threshold == 3
        assert config.respect_roots is True
        assert config.prevent_redundancy is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PlacementConfig(
            min_group_size=10,
            max_depth=2,
            merge_threshold=5
        )
        
        assert config.min_group_size == 10
        assert config.max_depth == 2
        assert config.merge_threshold == 5


class TestPlacementResolver:
    """Test PlacementResolver class."""
    
    def test_initialization(self, tmp_path):
        """Test resolver initialization."""
        resolver = PlacementResolver(tmp_path)
        
        assert resolver.target_root == tmp_path
        assert resolver.config.min_group_size == 5
        assert resolver.root_detector is not None
        assert resolver.context_builder is not None
    
    def test_build_target_path_simple(self, tmp_path):
        """Test building simple target path."""
        resolver = PlacementResolver(tmp_path)
        
        file_node = FileNode(
            path=Path("C:/test/file.pdf"),
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        result = RuleResult(
            file=file_node,
            category="Documents",
            subcategory="PDF",
            confidence=0.9,
            matched_rule=".pdf",
            context_hint="PDF"
        )
        
        target = resolver._build_target_path(result)
        
        assert target == tmp_path / "Documents" / "PDF" / "file.pdf"
    
    def test_build_target_path_same_category_subcategory(self, tmp_path):
        """Test path building when category == subcategory."""
        resolver = PlacementResolver(tmp_path)
        
        file_node = FileNode(
            path=Path("C:/test/image.jpg"),
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        result = RuleResult(
            file=file_node,
            category="Images",
            subcategory="Images",  # Same as category
            confidence=0.9,
            matched_rule=".jpg",
            context_hint="Image"
        )
        
        target = resolver._build_target_path(result)
        
        # Should not duplicate: Images/Images/
        assert target == tmp_path / "Images" / "image.jpg"


class TestRule1RedundancyPrevention:
    """Test Rule 1: Collection Folder Prevention."""
    
    def test_prevents_mp3_collection_redundancy(self, tmp_path):
        """Test preventing MP3 Collection/MP3/ pattern."""
        resolver = PlacementResolver(tmp_path)
        
        # Create file nodes
        files = [
            FileNode(
                path=Path(f"C:/music/song{i}.mp3"),
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            )
            for i in range(6)
        ]
        
        # Create rule results (all MP3)
        rule_results = [
            RuleResult(
                file=f,
                category="Audio",
                subcategory="MP3",
                confidence=0.9,
                matched_rule=".mp3",
                context_hint="MP3"
            )
            for f in files
        ]
        
        # Build initial placement map
        placement_map = resolver._build_placement_map(rule_results, None)
        
        # All files would go to Audio/MP3/
        for target in placement_map.values():
            assert target.parent == tmp_path / "Audio" / "MP3"
        
        # Apply redundancy prevention
        updated_map = resolver._apply_redundancy_prevention(placement_map, rule_results)
        
        # Should collapse to Audio/ (removing redundant MP3 subfolder)
        for target in updated_map.values():
            assert target.parent == tmp_path / "Audio"
    
    def test_keeps_non_redundant_structure(self, tmp_path):
        """Test that non-redundant structure is kept."""
        resolver = PlacementResolver(tmp_path)
        
        # Mix of file types in Documents - need 5+ files each for min group size
        files = [
            FileNode(path=Path(f"C:/docs/doc{i}.pdf"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(5)
        ] + [
            FileNode(path=Path(f"C:/docs/sheet{i}.xlsx"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(5)
        ]
        
        rule_results = [
            *[RuleResult(file=f, category="Documents", subcategory="PDF",
                        confidence=0.9, matched_rule=".pdf", context_hint="PDF")
              for f in files[:5]],
            *[RuleResult(file=f, category="Documents", subcategory="Excel",
                        confidence=0.9, matched_rule=".xlsx", context_hint="Excel")
              for f in files[5:]],
        ]
        
        placement_map = resolver._build_placement_map(rule_results, None)
        updated_map = resolver._apply_redundancy_prevention(placement_map, rule_results)
        
        # Documents/PDF/ and Documents/Excel/ should be kept (not redundant)
        pdf_targets = [updated_map[f] for f in files[:5]]
        excel_targets = [updated_map[f] for f in files[5:]]
        
        for target in pdf_targets:
            assert target.parent == tmp_path / "Documents" / "PDF"
        
        for target in excel_targets:
            assert target.parent == tmp_path / "Documents" / "Excel"


class TestRule2MinimumGroupSize:
    """Test Rule 2: Minimum Group Size."""
    
    def test_merges_small_folders(self, tmp_path):
        """Test merging folders with <5 files."""
        resolver = PlacementResolver(tmp_path)
        
        # Create 4 files (below minimum of 5)
        files = [
            FileNode(
                path=Path(f"C:/test/file{i}.txt"),
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            )
            for i in range(4)
        ]
        
        # All go to Documents/Text/
        placement_map = {
            f: tmp_path / "Documents" / "Text" / f.path.name
            for f in files
        }
        
        # Apply minimum group size
        updated_map = resolver._apply_minimum_group_size(placement_map)
        
        # Should merge to Documents/ (removing Text/ because it has <5 files)
        for target in updated_map.values():
            assert target.parent == tmp_path / "Documents"
    
    def test_keeps_large_folders(self, tmp_path):
        """Test keeping folders with ≥5 files."""
        resolver = PlacementResolver(tmp_path)
        
        # Create 6 files (above minimum)
        files = [
            FileNode(
                path=Path(f"C:/test/file{i}.pdf"),
                is_dir=False,
                size=1000,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            )
            for i in range(6)
        ]
        
        placement_map = {
            f: tmp_path / "Documents" / "PDF" / f.path.name
            for f in files
        }
        
        updated_map = resolver._apply_minimum_group_size(placement_map)
        
        # Should keep Documents/PDF/ (has 6 files ≥ 5)
        for target in updated_map.values():
            assert target.parent == tmp_path / "Documents" / "PDF"


class TestRule3DepthLimit:
    """Test Rule 3: Depth Limit."""
    
    def test_enforces_max_depth_3(self, tmp_path):
        """Test maximum depth of 3 levels."""
        resolver = PlacementResolver(tmp_path)
        
        file_node = FileNode(
            path=Path("C:/test/file.txt"),
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        # Create path with 4 levels (exceeds max of 3)
        deep_path = tmp_path / "A" / "B" / "C" / "D" / "file.txt"
        placement_map = {file_node: deep_path}
        
        updated_map = resolver._apply_depth_limit(placement_map)
        
        # Should flatten to max depth 3
        result_path = updated_map[file_node]
        relative = result_path.relative_to(tmp_path)
        depth = len(relative.parts) - 1  # -1 for filename
        
        assert depth == 3
        assert result_path == tmp_path / "A" / "B" / "C" / "file.txt"
    
    def test_allows_depth_3(self, tmp_path):
        """Test that depth 3 is allowed."""
        resolver = PlacementResolver(tmp_path)
        
        file_node = FileNode(
            path=Path("C:/test/file.txt"),
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        # Path with exactly 3 levels
        path_3 = tmp_path / "A" / "B" / "C" / "file.txt"
        placement_map = {file_node: path_3}
        
        updated_map = resolver._apply_depth_limit(placement_map)
        
        # Should not change
        assert updated_map[file_node] == path_3


class TestRule4SiblingMerge:
    """Test Rule 4: Sibling Analysis."""
    
    def test_merges_small_sibling_folders(self, tmp_path):
        """Test merging small sibling folders."""
        resolver = PlacementResolver(
            tmp_path,
            config=PlacementConfig(merge_threshold=3)
        )
        
        # Create files in multiple small sibling folders
        files_a = [
            FileNode(path=Path(f"C:/test/a{i}.txt"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(2)  # 2 files in A/
        ]
        
        files_b = [
            FileNode(path=Path(f"C:/test/b{i}.txt"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(2)  # 2 files in B/
        ]
        
        # Place in sibling folders under Documents/
        placement_map = {}
        for f in files_a:
            placement_map[f] = tmp_path / "Documents" / "FolderA" / f.path.name
        for f in files_b:
            placement_map[f] = tmp_path / "Documents" / "FolderB" / f.path.name
        
        updated_map = resolver._apply_sibling_merge(placement_map)
        
        # Both small siblings should merge to Documents/
        for f in files_a + files_b:
            assert updated_map[f].parent == tmp_path / "Documents"
    
    def test_keeps_large_siblings(self, tmp_path):
        """Test keeping sibling folders with enough files."""
        resolver = PlacementResolver(
            tmp_path,
            config=PlacementConfig(merge_threshold=3)
        )
        
        # Create files in larger sibling folders
        files_a = [
            FileNode(path=Path(f"C:/test/a{i}.txt"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(5)  # 5 files in A/
        ]
        
        files_b = [
            FileNode(path=Path(f"C:/test/b{i}.txt"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(5)  # 5 files in B/
        ]
        
        placement_map = {}
        for f in files_a:
            placement_map[f] = tmp_path / "Documents" / "FolderA" / f.path.name
        for f in files_b:
            placement_map[f] = tmp_path / "Documents" / "FolderB" / f.path.name
        
        updated_map = resolver._apply_sibling_merge(placement_map)
        
        # Large siblings should not be merged
        for f in files_a:
            assert updated_map[f].parent == tmp_path / "Documents" / "FolderA"
        for f in files_b:
            assert updated_map[f].parent == tmp_path / "Documents" / "FolderB"


class TestRule5ContextCollapse:
    """Test Rule 5: Context Collapse."""
    
    def test_removes_duplicate_folder_names(self, tmp_path):
        """Test removing duplicate folder names in path."""
        resolver = PlacementResolver(tmp_path)
        
        file_node = FileNode(
            path=Path("C:/test/file.py"),
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
            category="Code",
            subcategory="Python",
            confidence=0.9,
            matched_rule=".py",
            context_hint="Python"
        )
        
        # Create path with duplicate: Code/Python/Python/
        dup_path = tmp_path / "Code" / "Python" / "Python" / "file.py"
        placement_map = {file_node: dup_path}
        
        updated_map = resolver._apply_context_collapse(placement_map, [rule_result])
        
        # Should collapse to Code/Python/
        result_path = updated_map[file_node]
        parts = result_path.relative_to(tmp_path).parts[:-1]  # Exclude filename
        
        assert "Python" in parts
        assert parts.count("Python") == 1  # Only one Python folder
    
    def test_case_insensitive_collapse(self, tmp_path):
        """Test case-insensitive duplicate detection."""
        resolver = PlacementResolver(tmp_path)
        
        file_node = FileNode(
            path=Path("C:/test/file.py"),
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
            category="Code",
            subcategory="Python",
            confidence=0.9,
            matched_rule=".py",
            context_hint="Python"
        )
        
        # Create path with case-different duplicate
        dup_path = tmp_path / "code" / "PYTHON" / "Python" / "file.py"
        placement_map = {file_node: dup_path}
        
        updated_map = resolver._apply_context_collapse(placement_map, [rule_result])
        
        # Should collapse case-insensitive duplicates
        result_path = updated_map[file_node]
        parts_lower = [p.lower() for p in result_path.relative_to(tmp_path).parts[:-1]]
        
        # Should only have one occurrence of "python" (case-insensitive)
        assert parts_lower.count("python") == 1


class TestProtectedRoots:
    """Test protected root handling."""
    
    def test_respects_protected_roots(self, tmp_path):
        """Test that files in protected roots are not moved."""
        # Create a Python project structure
        project = tmp_path / "MyProject"
        project.mkdir()
        
        (project / ".git").mkdir()
        (project / "src").mkdir()
        
        # Create files in project
        file1 = project / "src" / "main.py"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("print('hello')")
        
        # Create FileNode structure that includes .git folder
        git_node = FileNode(
            path=project / ".git",
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=1,
            root_distance=0
        )
        
        file_node = FileNode(
            path=file1,
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=2,
            root_distance=0
        )
        
        src_node = FileNode(
            path=project / "src",
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=(file_node,),
            depth=1,
            root_distance=0
        )
        
        root_node = FileNode(
            path=project,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=(git_node, src_node),  # Include .git and src folders
            depth=0,
            root_distance=0
        )
        
        rule_result = RuleResult(
            file=file_node,
            category="Code",
            subcategory="Python",
            confidence=0.9,
            matched_rule=".py",
            context_hint="Python"
        )
        
        resolver = PlacementResolver(tmp_path)
        decisions = resolver.resolve_placements(root_node, [rule_result])
        
        # File should stay in project (not moved)
        assert len(decisions) == 1
        assert decisions[0].target == file1
        assert "Protected root" in decisions[0].reason


class TestIntegration:
    """Integration tests with all rules."""
    
    def test_full_pipeline(self, tmp_path):
        """Test complete resolution pipeline."""
        resolver = PlacementResolver(tmp_path)
        
        # Create diverse file set
        files = [
            *[FileNode(path=Path(f"C:/music/song{i}.mp3"), is_dir=False, size=1000,
                      mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
              for i in range(10)],  # 10 MP3s
            *[FileNode(path=Path(f"C:/docs/doc{i}.pdf"), is_dir=False, size=1000,
                      mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
              for i in range(3)],   # 3 PDFs (below min)
        ]
        
        # Create root node
        root_node = FileNode(
            path=tmp_path,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(files),
            depth=0,
            root_distance=0
        )
        
        # Create rule results
        rule_results = [
            *[RuleResult(file=f, category="Audio", subcategory="MP3",
                        confidence=0.9, matched_rule=".mp3", context_hint="MP3")
              for f in files[:10]],
            *[RuleResult(file=f, category="Documents", subcategory="PDF",
                        confidence=0.9, matched_rule=".pdf", context_hint="PDF")
              for f in files[10:]],
        ]
        
        decisions = resolver.resolve_placements(root_node, rule_results)
        
        assert len(decisions) == 13
        
        # MP3 files should collapse (Rule 1: redundancy)
        mp3_decisions = decisions[:10]
        for d in mp3_decisions:
            # Should be Audio/ not Audio/MP3/ (redundant)
            assert d.target.parent == tmp_path / "Audio"
        
        # PDF files should merge up (Rule 2: min group size)
        pdf_decisions = decisions[10:]
        for d in pdf_decisions:
            # Should be Documents/ not Documents/PDF/ (too few files)
            assert d.target.parent == tmp_path / "Documents"


class TestConvenienceFunction:
    """Test resolve_file_placements convenience function."""
    
    def test_convenience_function(self, tmp_path):
        """Test convenience function."""
        files = [
            FileNode(path=Path(f"C:/test/file{i}.txt"), is_dir=False, size=1000,
                     mtime=0.0, parent=None, children=tuple(), depth=0, root_distance=0)
            for i in range(6)
        ]
        
        root_node = FileNode(
            path=tmp_path,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(files),
            depth=0,
            root_distance=0
        )
        
        rule_results = [
            RuleResult(file=f, category="Documents", subcategory="Text",
                      confidence=0.9, matched_rule=".txt", context_hint="Text")
            for f in files
        ]
        
        decisions = resolve_file_placements(root_node, rule_results, tmp_path)
        
        assert len(decisions) == 6
        assert all(d.target.parent == tmp_path / "Documents" / "Text" for d in decisions)


class TestConflictDetection:
    """Test conflict detection."""
    
    def test_detects_naming_conflicts(self, tmp_path):
        """Test detecting files with same target name."""
        resolver = PlacementResolver(tmp_path)
        
        # Two files with same name from different sources
        file1 = FileNode(
            path=Path("C:/folder1/report.pdf"),
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        file2 = FileNode(
            path=Path("C:/folder2/report.pdf"),
            is_dir=False,
            size=2000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        root_node = FileNode(
            path=tmp_path,
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=(file1, file2),
            depth=0,
            root_distance=0
        )
        
        rule_results = [
            RuleResult(file=file1, category="Documents", subcategory="PDF",
                      confidence=0.9, matched_rule=".pdf", context_hint="PDF"),
            RuleResult(file=file2, category="Documents", subcategory="PDF",
                      confidence=0.9, matched_rule=".pdf", context_hint="PDF"),
        ]
        
        decisions = resolver.resolve_placements(root_node, rule_results)
        
        # Both should have conflicts listed
        assert len(decisions) == 2
        assert len(decisions[0].conflicts) > 0
        assert len(decisions[1].conflicts) > 0
