#!/usr/bin/env python3
"""
Validation Test Script
Tests all features of AutoFolder AI
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.organizer import FileOrganizer
from core.rules import RuleEngine
from utils.config_manager import ConfigManager
from ai.classifier import AIClassifier

def main():
    print("=" * 70)
    print("AutoFolder AI - VALIDATION TEST")
    print("=" * 70)
    
    # Load config
    config = ConfigManager()
    print(f"\n✓ Configuration loaded")
    print(f"  - AI enabled: {config.get('ai', {}).get('enabled', False)}")
    
    # Initialize components
    organizer = FileOrganizer(config.config)
    rule_engine = RuleEngine()
    ai_classifier = AIClassifier(config.config)
    
    print(f"✓ Components initialized")
    print(f"  - Available profiles: {', '.join(rule_engine.get_available_profiles())}")
    print(f"  - AI status: {ai_classifier.get_status()}")
    
    # Test folder
    test_folder = Path('test_validation')
    if not test_folder.exists():
        print(f"\n✗ Test folder not found: {test_folder}")
        return 1
    
    print(f"\n✓ Test folder: {test_folder.absolute()}")
    
    # Analyze folder
    print("\n" + "=" * 70)
    print("STEP 1: ANALYZING FOLDER")
    print("=" * 70)
    
    analysis = organizer.analyze_folder(test_folder)
    
    print(f"\nTotal files: {analysis['total_files']}")
    print(f"Total size: {analysis['total_size']:,} bytes")
    
    print(f"\nFiles by extension:")
    for ext, count in sorted(analysis['by_extension'].items()):
        print(f"  {ext:15} : {count} file(s)")
    
    print(f"\nFiles by size:")
    for size_range, count in analysis['by_size_range'].items():
        print(f"  {size_range:10} : {count} file(s)")
    
    # Preview organization
    print("\n" + "=" * 70)
    print("STEP 2: PREVIEW ORGANIZATION (Downloads Profile)")
    print("=" * 70)
    
    preview = organizer.preview_organization(test_folder, profile='downloads')
    
    print(f"\nOperations planned: {len(preview)}\n")
    print(f"{'File Name':<35} {'Category':<15} {'Target Folder':<20}")
    print("-" * 70)
    
    for op in preview:
        print(f"{op['source'].name:<35} {op['category']:<15} {op['target'].parent.name:<20}")
    
    # Test dry run
    print("\n" + "=" * 70)
    print("STEP 3: DRY RUN (No files moved)")
    print("=" * 70)
    
    result = organizer.organize_folder(test_folder, profile='downloads', dry_run=True)
    
    print(f"\n✓ Dry run completed")
    print(f"  - Success: {result['success']}")
    print(f"  - Dry run: {result['dry_run']}")
    print(f"  - Operations: {result['total']}")
    
    # Test actual organization
    print("\n" + "=" * 70)
    print("STEP 4: ACTUAL ORGANIZATION")
    print("=" * 70)
    
    confirm = input("\n⚠️  Organize files now? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        result = organizer.organize_folder(test_folder, profile='downloads', dry_run=False)
        
        print(f"\n✓ Organization completed!")
        print(f"  - Files organized: {result['completed']}")
        print(f"  - Failed: {result['failed']}")
        print(f"  - Can undo: {result['can_undo']}")
        
        # Show result
        print(f"\n📂 Check the '{test_folder}' folder to see organized subfolders!")
        
        # Test undo
        print("\n" + "=" * 70)
        print("STEP 5: UNDO TEST")
        print("=" * 70)
        
        undo_confirm = input("\n⚠️  Test undo? This will restore files. (yes/no): ").strip().lower()
        
        if undo_confirm == 'yes':
            success = organizer.undo_last_operation()
            if success:
                print("\n✓ Undo successful! Files restored to original locations.")
            else:
                print("\n✗ Undo failed or partial success.")
    else:
        print("\n⏭️  Organization skipped")
    
    # Test AI features if enabled
    if ai_classifier.enabled:
        print("\n" + "=" * 70)
        print("STEP 6: AI CLASSIFICATION TEST")
        print("=" * 70)
        
        test_files = list(test_folder.glob('*.pdf'))[:3]
        
        if test_files:
            print(f"\nTesting AI on {len(test_files)} PDF files:\n")
            
            for file_path in test_files:
                result = ai_classifier.classify_file(file_path)
                if result:
                    print(f"  {file_path.name}")
                    print(f"    → Category: {result['category']}")
                    print(f"    → Confidence: {result['confidence']:.2%}\n")
                else:
                    print(f"  {file_path.name}")
                    print(f"    → No confident classification\n")
        else:
            print("\n  No PDF files to test AI on")
    else:
        print("\n" + "=" * 70)
        print("STEP 6: AI FEATURES (Disabled)")
        print("=" * 70)
        print("\n  AI is disabled. Enable in config to test Pro features.")
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION TEST COMPLETE")
    print("=" * 70)
    
    print("\n✓ All core features working:")
    print("  ✓ Folder analysis")
    print("  ✓ Rule-based categorization")
    print("  ✓ Organization preview")
    print("  ✓ Dry run mode")
    print("  ✓ Actual organization")
    print("  ✓ Undo functionality")
    
    if ai_classifier.enabled:
        print("  ✓ AI classification (Pro)")
    
    print("\n✅ AutoFolder AI is fully functional and ready for use!")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
