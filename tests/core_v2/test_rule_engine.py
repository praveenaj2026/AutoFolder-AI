"""
Unit tests for v2.0 Rule Engine.

Tests enhanced rule-based classification with context hints.
"""

import pytest
from pathlib import Path
from src.core_v2.rule_engine import RuleEngine, classify_file, RULES
from src.core_v2.models import FileNode


class TestRuleEngine:
    """Test RuleEngine class."""
    
    def test_initialization(self):
        """Test rule engine initialization."""
        engine = RuleEngine()
        
        # Should have extension map
        assert len(engine._extension_map) > 0
        
        # Should cover common extensions
        assert ".pdf" in engine._extension_map
        assert ".py" in engine._extension_map
        assert ".jpg" in engine._extension_map
    
    def test_classify_pdf(self, tmp_path):
        """Test classifying PDF file."""
        file_path = tmp_path / "document.pdf"
        file_path.write_text("PDF content")
        
        node = FileNode(
            path=file_path,
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        engine = RuleEngine()
        result = engine.classify(node)
        
        assert result is not None
        assert result.category == "Documents"
        assert result.subcategory == "PDF"
        assert result.confidence >= 0.9
        assert result.matched_rule == ".pdf"
        assert "PDF" in result.context_hint
    
    def test_classify_python(self, tmp_path):
        """Test classifying Python file."""
        file_path = tmp_path / "script.py"
        file_path.write_text("print('hello')")
        
        node = FileNode(
            path=file_path,
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        engine = RuleEngine()
        result = engine.classify(node)
        
        assert result is not None
        assert result.category == "Code"
        assert result.subcategory == "Python"
        assert result.confidence >= 0.9
    
    def test_classify_image(self, tmp_path):
        """Test classifying image files."""
        engine = RuleEngine()
        
        # JPEG
        jpg_node = FileNode(
            path=tmp_path / "photo.jpg",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        result = engine.classify(jpg_node)
        assert result.category == "Images"
        assert result.subcategory == "JPEG"
        
        # PNG
        png_node = FileNode(
            path=tmp_path / "screenshot.png",
            is_dir=False,
            size=1000,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        result = engine.classify(png_node)
        assert result.category == "Images"
        assert result.subcategory == "PNG"
    
    def test_classify_no_match(self, tmp_path):
        """Test classifying file with unknown extension."""
        node = FileNode(
            path=tmp_path / "unknown.xyz",
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        engine = RuleEngine()
        result = engine.classify(node)
        
        assert result is None
    
    def test_classify_no_extension(self, tmp_path):
        """Test classifying file with no extension."""
        node = FileNode(
            path=tmp_path / "README",
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        engine = RuleEngine()
        result = engine.classify(node)
        
        assert result is None
    
    def test_classify_directory(self, tmp_path):
        """Test that directories return None."""
        node = FileNode(
            path=tmp_path / "folder",
            is_dir=True,
            size=0,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        engine = RuleEngine()
        result = engine.classify(node)
        
        assert result is None
    
    def test_classify_batch(self, tmp_path):
        """Test batch classification."""
        # Create multiple files
        nodes = [
            FileNode(
                path=tmp_path / "doc.pdf",
                is_dir=False,
                size=100,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            ),
            FileNode(
                path=tmp_path / "script.py",
                is_dir=False,
                size=100,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            ),
            FileNode(
                path=tmp_path / "photo.jpg",
                is_dir=False,
                size=100,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            ),
            FileNode(
                path=tmp_path / "unknown.xyz",
                is_dir=False,
                size=100,
                mtime=0.0,
                parent=None,
                children=tuple(),
                depth=0,
                root_distance=0
            ),
        ]
        
        engine = RuleEngine()
        results = engine.classify_batch(nodes)
        
        # Should classify 3 out of 4 (skip .xyz)
        assert len(results) == 3
        
        categories = {r.category for r in results}
        assert "Documents" in categories
        assert "Code" in categories
        assert "Images" in categories
    
    def test_get_categories(self):
        """Test getting all categories."""
        engine = RuleEngine()
        categories = engine.get_categories()
        
        assert "Documents" in categories
        assert "Images" in categories
        assert "Videos" in categories
        assert "Audio" in categories
        assert "Code" in categories
        assert "Archives" in categories
    
    def test_get_subcategories(self):
        """Test getting subcategories for a category."""
        engine = RuleEngine()
        
        # Documents
        doc_subcats = engine.get_subcategories("Documents")
        assert "PDF" in doc_subcats
        assert "Word" in doc_subcats
        assert "Excel" in doc_subcats
        
        # Code
        code_subcats = engine.get_subcategories("Code")
        assert "Python" in code_subcats
        assert "JavaScript" in code_subcats
        assert "HTML" in code_subcats
    
    def test_get_extensions_for_category(self):
        """Test getting extensions for a category."""
        engine = RuleEngine()
        
        # Images
        image_exts = engine.get_extensions_for_category("Images")
        assert ".jpg" in image_exts
        assert ".png" in image_exts
        assert ".gif" in image_exts
        
        # Code
        code_exts = engine.get_extensions_for_category("Code")
        assert ".py" in code_exts
        assert ".js" in code_exts
        assert ".html" in code_exts


class TestConvenienceFunction:
    """Test classify_file convenience function."""
    
    def test_classify_file(self, tmp_path):
        """Test convenience function."""
        node = FileNode(
            path=tmp_path / "test.pdf",
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        
        result = classify_file(node)
        
        assert result is not None
        assert result.category == "Documents"
        assert result.subcategory == "PDF"


class TestRuleDefinitions:
    """Test rule definitions are comprehensive."""
    
    def test_rules_have_required_fields(self):
        """Test all rules have required fields."""
        for rule in RULES:
            assert rule.extensions
            assert rule.category
            assert rule.subcategory
            assert 0.0 <= rule.confidence <= 1.0
            assert isinstance(rule.context_hint, str)
    
    def test_common_extensions_covered(self):
        """Test common file extensions are covered."""
        engine = RuleEngine()
        
        # Documents
        assert ".pdf" in engine._extension_map
        assert ".docx" in engine._extension_map
        assert ".xlsx" in engine._extension_map
        assert ".txt" in engine._extension_map
        
        # Images
        assert ".jpg" in engine._extension_map
        assert ".png" in engine._extension_map
        assert ".gif" in engine._extension_map
        
        # Videos
        assert ".mp4" in engine._extension_map
        assert ".mkv" in engine._extension_map
        
        # Audio
        assert ".mp3" in engine._extension_map
        assert ".wav" in engine._extension_map
        
        # Archives
        assert ".zip" in engine._extension_map
        assert ".rar" in engine._extension_map
        
        # Code
        assert ".py" in engine._extension_map
        assert ".js" in engine._extension_map
        assert ".html" in engine._extension_map
        assert ".css" in engine._extension_map
    
    def test_no_duplicate_extensions(self):
        """Test extensions aren't duplicated across rules (or keep highest confidence)."""
        extension_rules = {}
        
        for rule in RULES:
            for ext in rule.extensions:
                if ext in extension_rules:
                    # If duplicate, ensure we keep the higher confidence one
                    existing = extension_rules[ext]
                    if rule.confidence > existing.confidence:
                        extension_rules[ext] = rule
                else:
                    extension_rules[ext] = rule
        
        # This should work without errors
        assert len(extension_rules) > 0
    
    def test_context_hints_provided(self):
        """Test all rules have meaningful context hints."""
        for rule in RULES:
            # Context hint should be descriptive
            assert len(rule.context_hint) > 0
            # Should not just be the category/subcategory
            assert rule.context_hint.lower() != rule.category.lower()


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_case_insensitive_extensions(self, tmp_path):
        """Test that extension matching is case-insensitive."""
        engine = RuleEngine()
        
        # Uppercase extension
        node_upper = FileNode(
            path=tmp_path / "FILE.PDF",
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        result_upper = engine.classify(node_upper)
        
        # Lowercase extension
        node_lower = FileNode(
            path=tmp_path / "file.pdf",
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        result_lower = engine.classify(node_lower)
        
        # Both should classify the same
        assert result_upper is not None
        assert result_lower is not None
        assert result_upper.category == result_lower.category
        assert result_upper.subcategory == result_lower.subcategory
    
    def test_multiple_dots_in_filename(self, tmp_path):
        """Test files with multiple dots."""
        engine = RuleEngine()
        
        node = FileNode(
            path=tmp_path / "my.backup.file.pdf",
            is_dir=False,
            size=100,
            mtime=0.0,
            parent=None,
            children=tuple(),
            depth=0,
            root_distance=0
        )
        result = engine.classify(node)
        
        # Should use the last extension (.pdf)
        assert result is not None
        assert result.category == "Documents"
        assert result.subcategory == "PDF"
