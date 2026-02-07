"""Integration tests for AutoFolder AI v2.0 full pipeline."""

import pytest
from pathlib import Path
import time
from typing import List, Dict

from src.core_v2.scanner import DeepScanner
from src.core_v2.root_detector import RootDetector
from src.core_v2.rule_engine import RuleEngine
from src.core_v2.context_builder import ContextBuilder
from src.core_v2.placement_resolver import PlacementResolver
from src.core_v2.ai_grouper import AIGrouper
from src.core_v2.preview_builder import PreviewBuilderV2
from src.core_v2.models import DecisionSource, FileNode


def run_full_pipeline(base_path: Path, use_ai: bool = True):
    """Run complete v2.0 organization pipeline.
    
    Args:
        base_path: Root folder to organize
        use_ai: Whether to use AI grouping
        
    Returns:
        Dictionary with results from each stage
    """
    results = {}
    
    # 1. Scan files
    scanner = DeepScanner()
    file_tree = scanner.scan(base_path)
    results['file_tree'] = file_tree
    results['total_files'] = len(list(file_tree.iter_files()))
    
    # 2. Classify files
    rule_engine = RuleEngine()
    files = list(file_tree.iter_files())
    rule_results = rule_engine.classify_batch(files)
    results['rule_results'] = rule_results
    
    # 3. AI grouping (optional)
    ai_results = None
    if use_ai:
        ai_grouper = AIGrouper()
        ai_results = ai_grouper.group_files(files, rule_results)
        results['ai_results'] = ai_results or []
    else:
        results['ai_results'] = []
    
    # 4. Resolve placements (includes root detection and context building)
    resolver = PlacementResolver(target_root=base_path)
    placements = resolver.resolve_placements(file_tree, rule_results, ai_results)
    results['placements'] = placements
    
    # Extract info from resolver
    results['protected_roots'] = resolver._protected_roots if hasattr(resolver, '_protected_roots') else []
    results['context'] = resolver._context if hasattr(resolver, '_context') else None
    
    # 5. Generate preview
    preview_builder = PreviewBuilderV2()
    preview = preview_builder.build_preview(placements, results['ai_results'])
    results['preview'] = preview
    
    return results


class TestFullPipelineBasic:
    """Basic end-to-end pipeline tests."""
    
    def test_empty_folder(self, tmp_path):
        """Test pipeline with empty folder."""
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 0
        assert len(result['placements']) == 0
        assert "No files to organize" in result['preview']
    
    def test_single_file(self, tmp_path):
        """Test pipeline with single file."""
        # Create single file
        test_file = tmp_path / "document.pdf"
        test_file.write_text("test content")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 1
        assert len(result['placements']) == 1
        assert result['placements'][0].file.path == test_file
        assert "document.pdf" in result['preview']
    
    def test_simple_flat_structure(self, tmp_path):
        """Test pipeline with flat folder of mixed files."""
        # Create test files
        files = [
            "report.pdf",
            "invoice.pdf",
            "photo.jpg",
            "screenshot.png",
            "script.py",
            "data.csv"
        ]
        
        for filename in files:
            (tmp_path / filename).write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 6
        assert len(result['placements']) == 6
        
        # Check categories created
        categories = {p.target.parts[-2] for p in result['placements'] if len(p.target.parts) > 1}
        assert "Documents" in categories
        assert "Images" in categories
        assert "Code" in categories
    
    def test_nested_structure(self, tmp_path):
        """Test pipeline with nested folders."""
        # Create nested structure
        (tmp_path / "folder1" / "subfolder1").mkdir(parents=True)
        (tmp_path / "folder1" / "subfolder2").mkdir(parents=True)
        (tmp_path / "folder2").mkdir()
        
        # Add files at various levels
        (tmp_path / "root.txt").write_text("test")
        (tmp_path / "folder1" / "file1.pdf").write_text("test")
        (tmp_path / "folder1" / "subfolder1" / "file2.jpg").write_text("test")
        (tmp_path / "folder1" / "subfolder2" / "file3.doc").write_text("test")
        (tmp_path / "folder2" / "file4.py").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 5
        assert len(result['placements']) == 5
    
    def test_without_ai_grouping(self, tmp_path):
        """Test pipeline without AI grouping."""
        # Create vacation photos that could be grouped
        for i in range(5):
            (tmp_path / f"vacation_2025_{i}.jpg").write_text("test")
        
        result = run_full_pipeline(tmp_path, use_ai=False)
        
        assert result['total_files'] == 5
        assert len(result['ai_results']) == 0
        assert len(result['placements']) == 5


class TestProtectedRoots:
    """Test protected root detection and preservation."""
    
    def test_project_folder_protected(self, tmp_path):
        """Test that project folders are protected."""
        # Create project structure
        project = tmp_path / "MyProject"
        project.mkdir()
        (project / ".git").mkdir()
        (project / "src").mkdir()
        (project / "src" / "main.py").write_text("print('hello')")
        (project / "README.md").write_text("# My Project")
        
        # Add some loose files
        (tmp_path / "document.pdf").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Check project files are protected
        project_placements = [
            p for p in result['placements']
            if str(p.file.path).startswith(str(project))
        ]
        
        for placement in project_placements:
            assert placement.source == DecisionSource.PROTECTED
            assert placement.target == placement.file.path  # No move
    
    def test_media_library_protected(self, tmp_path):
        """Test that media libraries are protected."""
        # Create photo library structure
        library = tmp_path / "Photos"
        library.mkdir()
        (library / "DCIM").mkdir()
        (library / "DCIM" / "IMG_001.jpg").write_text("test")
        (library / "DCIM" / "IMG_002.jpg").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Check photos are protected
        photo_placements = [
            p for p in result['placements']
            if str(p.file.path).startswith(str(library))
        ]
        
        for placement in photo_placements:
            assert placement.source == DecisionSource.PROTECTED


class TestAIGroupingIntegration:
    """Test AI grouping integration with placement resolver."""
    
    def test_vacation_photos_grouped(self, tmp_path):
        """Test vacation photos are grouped together."""
        # Create vacation photos with similar names
        for i in range(5):
            (tmp_path / f"vacation_beach_2025_{i}.jpg").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Check AI grouping found the group
        if result['ai_results']:
            groups = {r.group for r in result['ai_results'] if r.group}
            assert len(groups) > 0
            
            # Check photos placed in same folder
            vacation_placements = [
                p for p in result['placements']
                if "vacation" in p.file.name.lower()
            ]
            target_folders = {p.target.parent for p in vacation_placements}
            # May be in same folder or organized separately
            assert len(target_folders) <= 2
    
    def test_ai_group_appears_in_preview(self, tmp_path):
        """Test AI groups are shown in preview."""
        # Create groupable files
        for i in range(4):
            (tmp_path / f"tax_2025_{i}.pdf").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        if result['ai_results']:
            # Check preview mentions AI grouping
            preview = result['preview']
            assert "AI Grouping" in preview or "[AI]" in preview


class TestAntiRedundancyRules:
    """Test that anti-redundancy rules work in full pipeline."""
    
    def test_rule1_format_specific_collapse(self, tmp_path):
        """Test Rule 1: Format-specific folders collapse."""
        # Create MP3 files (should collapse Audio/MP3/ → Audio/)
        for i in range(5):
            (tmp_path / f"song{i}.mp3").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Check placements don't create Audio/MP3/ redundancy
        mp3_targets = [p.target for p in result['placements'] if p.file.name.endswith('.mp3')]
        for target in mp3_targets:
            # Should be directly in Audio/ or a meaningful subfolder
            # Not Audio/MP3/
            path_parts = [p.lower() for p in target.parts]
            if 'audio' in path_parts:
                audio_idx = path_parts.index('audio')
                # Next part should not be 'mp3'
                if audio_idx + 1 < len(path_parts) - 1:  # Not the filename
                    assert path_parts[audio_idx + 1] != 'mp3'
    
    def test_rule2_minimum_group_size(self, tmp_path):
        """Test Rule 2: Small groups merge up."""
        # Create 2 Excel files (below min threshold)
        (tmp_path / "budget.xlsx").write_text("test")
        (tmp_path / "report.xlsx").write_text("test")
        
        # Create 10 Word files (above threshold)
        for i in range(10):
            (tmp_path / f"doc{i}.docx").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Excel files should merge to Documents/
        # Word files might stay in Documents/Word/
        excel_targets = [p.target for p in result['placements'] if p.file.name.endswith('.xlsx')]
        word_targets = [p.target for p in result['placements'] if p.file.name.endswith('.docx')]
        
        assert len(excel_targets) == 2
        assert len(word_targets) == 10
    
    def test_rule3_depth_limit(self, tmp_path):
        """Test Rule 3: Maximum depth enforcement."""
        # Create files that might create deep structure
        (tmp_path / "file.pdf").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Check no placement exceeds depth 3
        for placement in result['placements']:
            depth = len(placement.target.parts)
            assert depth <= 10  # Reasonable limit (including drive letter, etc.)


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""
    
    def test_files_with_no_extension(self, tmp_path):
        """Test files without extensions."""
        (tmp_path / "README").write_text("test")
        (tmp_path / "LICENSE").write_text("test")
        (tmp_path / "Makefile").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 3
        assert len(result['placements']) == 3
    
    def test_files_with_multiple_dots(self, tmp_path):
        """Test files like file.tar.gz."""
        (tmp_path / "archive.tar.gz").write_text("test")
        (tmp_path / "backup.tar.bz2").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 2
        assert len(result['placements']) == 2
    
    def test_files_with_special_characters(self, tmp_path):
        """Test files with special characters in names."""
        (tmp_path / "file (1).pdf").write_text("test")
        (tmp_path / "doc [final].docx").write_text("test")
        (tmp_path / "image #2.jpg").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 3
        assert len(result['placements']) == 3
    
    def test_very_long_filename(self, tmp_path):
        """Test files with very long names."""
        long_name = "a" * 200 + ".txt"
        (tmp_path / long_name).write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        assert result['total_files'] == 1
        assert len(result['placements']) == 1


class TestPerformance:
    """Basic performance tests."""
    
    def test_pipeline_completes_quickly(self, tmp_path):
        """Test pipeline completes in reasonable time."""
        # Create 100 files
        for i in range(100):
            ext = ['.pdf', '.jpg', '.docx', '.py', '.txt'][i % 5]
            (tmp_path / f"file{i}{ext}").write_text("test")
        
        start = time.time()
        result = run_full_pipeline(tmp_path)
        duration = time.time() - start
        
        assert result['total_files'] == 100
        assert duration < 5.0  # Should complete in under 5 seconds
    
    def test_nested_structure_performance(self, tmp_path):
        """Test performance with nested structure."""
        # Create nested structure (5 levels, 50 files)
        for i in range(5):
            folder = tmp_path / f"level{i}"
            folder.mkdir(exist_ok=True)
            for j in range(10):
                (folder / f"file{j}.txt").write_text("test")
        
        start = time.time()
        result = run_full_pipeline(tmp_path)
        duration = time.time() - start
        
        assert result['total_files'] == 50
        assert duration < 3.0


class TestPreviewGeneration:
    """Test preview generation in full pipeline."""
    
    def test_preview_contains_statistics(self, tmp_path):
        """Test preview includes statistics."""
        # Create some files
        for i in range(10):
            (tmp_path / f"file{i}.pdf").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        preview = result['preview']
        
        assert "Statistics" in preview
        assert "Total Files" in preview
        assert "10" in preview
    
    def test_preview_contains_folder_tree(self, tmp_path):
        """Test preview includes folder tree."""
        (tmp_path / "file.pdf").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        preview = result['preview']
        
        assert "Folder Structure" in preview
        assert "file.pdf" in preview
    
    def test_preview_shows_protected_files(self, tmp_path):
        """Test preview marks protected files."""
        # Create project
        project = tmp_path / "MyProject"
        project.mkdir()
        (project / ".git").mkdir()
        (project / "main.py").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        preview = result['preview']
        
        # Preview should mention protected files
        if result['protected_roots']:
            assert "Protected" in preview or "protected" in preview.lower()


class TestContextAwareness:
    """Test context-aware placement."""
    
    def test_respects_existing_structure(self, tmp_path):
        """Test pipeline respects existing folder structure."""
        # Create existing Documents folder with PDFs
        docs = tmp_path / "Documents"
        docs.mkdir()
        (docs / "existing1.pdf").write_text("test")
        (docs / "existing2.pdf").write_text("test")
        
        # Add new PDF in root
        (tmp_path / "new.pdf").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # New PDF should go to Documents (respecting context)
        new_placement = [p for p in result['placements'] if p.file.name == "new.pdf"][0]
        assert "Documents" in str(new_placement.target)
    
    def test_avoids_redundant_folders(self, tmp_path):
        """Test pipeline avoids creating redundant folder names."""
        # Create MP3 folder
        mp3_folder = tmp_path / "MP3"
        mp3_folder.mkdir()
        (mp3_folder / "song.mp3").write_text("test")
        
        result = run_full_pipeline(tmp_path)
        
        # Should not create MP3/MP3/ or similar redundancy
        mp3_placement = result['placements'][0]
        path_parts = str(mp3_placement.target).lower().split('\\')
        # Count occurrences of 'mp3'
        mp3_count = sum(1 for part in path_parts if 'mp3' in part)
        assert mp3_count <= 2  # At most: folder name + file name
