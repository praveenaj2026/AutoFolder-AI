#!/usr/bin/env python3
"""
Quick test script to verify the application runs correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from core import FileOrganizer, RuleEngine, FileAnalyzer, UndoManager
        print("✅ Core modules imported successfully")
    except Exception as e:
        print(f"❌ Core modules failed: {e}")
        return False
    
    try:
        from ai import AIClassifier
        print("✅ AI module imported successfully")
    except Exception as e:
        print(f"❌ AI module failed: {e}")
        return False
    
    try:
        from utils import ConfigManager, setup_logger
        print("✅ Utils modules imported successfully")
    except Exception as e:
        print(f"❌ Utils modules failed: {e}")
        return False
    
    try:
        from profiles import ProfileManager
        print("✅ Profiles module imported successfully")
    except Exception as e:
        print(f"❌ Profiles module failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from utils import ConfigManager
        config = ConfigManager()
        
        assert config.get('app', {}).get('name') == 'AutoFolder AI'
        assert 'safety' in config.config
        assert 'organization' in config.config
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_rule_engine():
    """Test rule engine."""
    print("\nTesting rule engine...")
    
    try:
        from core import RuleEngine
        engine = RuleEngine()
        
        profiles = engine.get_available_profiles()
        assert 'downloads' in profiles
        assert 'media' in profiles
        
        rules = engine.get_profile_rules('downloads')
        assert len(rules) > 0
        
        print(f"✅ Rule engine working ({len(profiles)} profiles, {len(rules)} rules in downloads)")
        return True
    except Exception as e:
        print(f"❌ Rule engine failed: {e}")
        return False

def test_file_analyzer():
    """Test file analyzer."""
    print("\nTesting file analyzer...")
    
    try:
        from core import FileAnalyzer
        analyzer = FileAnalyzer()
        
        categories = analyzer.categories
        assert 'document' in categories
        assert 'image' in categories
        
        print(f"✅ File analyzer working ({len(categories)} categories)")
        return True
    except Exception as e:
        print(f"❌ File analyzer failed: {e}")
        return False

def test_ui_imports():
    """Test UI imports (without actually showing UI)."""
    print("\nTesting UI imports...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui import MainWindow
        
        print("✅ UI modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ UI imports failed: {e}")
        print("   Note: PySide6 might not be installed")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("AutoFolder AI - Quick Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_rule_engine,
        test_file_analyzer,
        test_ui_imports,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All tests passed! Application is ready to run.")
        print("\nNext steps:")
        print("1. Run: python src/main.py")
        print("2. Test with a sample folder")
        print("3. Build with: pyinstaller (see docs/BUILDING.md)")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
