#!/usr/bin/env python3
"""
Real-world testing script for AutoFolder AI v2.0

Usage:
    python test_real_world.py "C:\\Path\\To\\Test\\Folder" [--no-ai] [--export]

Examples:
    # Full test with AI grouping
    python test_real_world.py "C:\\Temp\\TestDownloads"
    
    # Test without AI (faster)
    python test_real_world.py "C:\\Temp\\TestDownloads" --no-ai
    
    # Export preview to file
    python test_real_world.py "C:\\Temp\\TestDownloads" --export
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core_v2.scanner import ScannerV2, ScanConfig
from core_v2.rule_engine import RuleEngine, RuleConfig
from core_v2.ai_grouper import AIGrouper, AIGroupConfig
from core_v2.placement_resolver import PlacementResolver, PlacementConfig
from core_v2.preview_builder import PreviewBuilderV2, PreviewConfig


def run_real_world_test(folder_path: str, use_ai: bool = True, export: bool = False):
    """Run v2.0 pipeline on real-world folder"""
    
    print("=" * 80)
    print("AutoFolder AI v2.0 - Real-World Test")
    print("=" * 80)
    print()
    
    target_root = Path(folder_path)
    if not target_root.exists():
        print(f"❌ Error: Folder not found: {target_root}")
        return False
    
    print(f"📁 Test folder: {target_root}")
    print(f"🤖 AI grouping: {'Enabled' if use_ai else 'Disabled'}")
    print()
    
    # ========================================================================
    # Phase 1: Scanning
    # ========================================================================
    print("Phase 1: Scanning files...")
    start_scan = time.time()
    
    try:
        scanner = ScannerV2(ScanConfig(max_depth=10))
        root_node = scanner.scan_folder(target_root)
        
        scan_time = time.time() - start_scan
        print(f"  ✅ Scanned {root_node.total_files} files in {scan_time:.2f}s")
        print()
    except Exception as e:
        print(f"  ❌ Scan failed: {e}")
        return False
    
    # ========================================================================
    # Phase 2: Classification
    # ========================================================================
    print("Phase 2: Classifying files...")
    start_classify = time.time()
    
    try:
        rule_engine = RuleEngine(RuleConfig())
        rule_results = rule_engine.classify_all(root_node.all_files)
        
        classify_time = time.time() - start_classify
        print(f"  ✅ Classified {len(rule_results)} files in {classify_time:.2f}s")
        
        # Show category breakdown
        categories = {}
        for result in rule_results:
            cat = result.category.value
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"  📊 Categories: {dict(sorted(categories.items()))}")
        print()
    except Exception as e:
        print(f"  ❌ Classification failed: {e}")
        return False
    
    # ========================================================================
    # Phase 3: AI Grouping (Optional)
    # ========================================================================
    ai_results = []
    if use_ai:
        print("Phase 3: AI Semantic Grouping...")
        start_ai = time.time()
        
        try:
            ai_grouper = AIGrouper(AIGroupConfig(min_group_size=3))
            ai_results = ai_grouper.group_files(root_node.all_files)
            
            ai_time = time.time() - start_ai
            print(f"  ✅ Found {len(ai_results)} AI groups in {ai_time:.2f}s")
            
            # Show some groups
            if ai_results:
                print(f"  📦 Sample groups:")
                for i, group in enumerate(ai_results[:3], 1):
                    print(f"     {i}. \"{group.group_name}\" ({len(group.similar_files) + 1} files)")
            print()
        except Exception as e:
            print(f"  ⚠️  AI grouping failed (continuing without): {e}")
            ai_results = []
            print()
    else:
        print("Phase 3: AI Grouping (skipped)")
        print()
    
    # ========================================================================
    # Phase 4: Placement Resolution
    # ========================================================================
    print("Phase 4: Resolving placements...")
    start_placement = time.time()
    
    try:
        resolver = PlacementResolver(
            config=PlacementConfig(),
            target_root=target_root
        )
        decisions = resolver.resolve_placements(
            root_node=root_node,
            rule_results=rule_results,
            ai_results=ai_results
        )
        
        placement_time = time.time() - start_placement
        print(f"  ✅ Resolved {len(decisions)} placements in {placement_time:.2f}s")
        
        # Count safe vs conflicts
        safe_count = sum(1 for d in decisions if d.safe)
        conflict_count = len(decisions) - safe_count
        print(f"  ✅ Safe moves: {safe_count}")
        if conflict_count > 0:
            print(f"  ⚠️  Conflicts: {conflict_count}")
        print()
    except Exception as e:
        print(f"  ❌ Placement failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # Phase 5: Preview Generation
    # ========================================================================
    print("Phase 5: Generating preview...")
    start_preview = time.time()
    
    try:
        builder = PreviewBuilderV2(PreviewConfig(
            use_color=True,
            show_ai_groups=use_ai
        ))
        preview_text = builder.build_preview(decisions, ai_results)
        
        preview_time = time.time() - start_preview
        print(f"  ✅ Generated preview in {preview_time:.2f}s")
        print()
    except Exception as e:
        print(f"  ❌ Preview failed: {e}")
        return False
    
    # ========================================================================
    # Summary
    # ========================================================================
    total_time = time.time() - start_scan
    
    print("=" * 80)
    print("📊 Performance Summary")
    print("=" * 80)
    print(f"Scan:           {scan_time:>8.2f}s ({root_node.total_files} files)")
    print(f"Classification: {classify_time:>8.2f}s ({len(rule_results)} files)")
    if use_ai:
        print(f"AI Grouping:    {ai_time:>8.2f}s ({len(ai_results)} groups)")
    print(f"Placement:      {placement_time:>8.2f}s ({len(decisions)} decisions)")
    print(f"Preview:        {preview_time:>8.2f}s")
    print(f"{'─' * 80}")
    print(f"Total:          {total_time:>8.2f}s")
    print()
    
    # Performance rating
    files_per_sec = root_node.total_files / total_time if total_time > 0 else 0
    print(f"⚡ Speed: {files_per_sec:.1f} files/second")
    
    if total_time < 5:
        print("🏆 Performance: Excellent!")
    elif total_time < 15:
        print("✅ Performance: Good")
    elif total_time < 30:
        print("⚠️  Performance: Acceptable")
    else:
        print("❌ Performance: Needs optimization")
    print()
    
    # ========================================================================
    # Display Preview
    # ========================================================================
    print("=" * 80)
    print("👀 PREVIEW (What would happen)")
    print("=" * 80)
    print()
    print(preview_text)
    print()
    
    # ========================================================================
    # Export (Optional)
    # ========================================================================
    if export:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = target_root / f"autofolder_preview_{timestamp}.txt"
        
        try:
            builder.export_preview(preview_text, export_path)
            print(f"💾 Preview exported to: {export_path}")
            print()
        except Exception as e:
            print(f"⚠️  Export failed: {e}")
            print()
    
    # ========================================================================
    # Warnings & Recommendations
    # ========================================================================
    print("=" * 80)
    print("⚠️  Important Notes")
    print("=" * 80)
    print()
    print("This is a TEST RUN - no files were moved!")
    print()
    print("Review the preview carefully:")
    print("  • Check protected roots (marked in preview)")
    print("  • Verify AI groups make sense")
    print("  • Look for redundant folder nesting")
    print("  • Confirm important files aren't buried")
    print()
    
    if conflict_count > 0:
        print(f"⚠️  {conflict_count} files have conflicts - review before executing")
        print()
    
    print("To execute this organization:")
    print("  1. Review preview thoroughly")
    print("  2. Backup your data")
    print("  3. Run the executor (Week 12 feature)")
    print()
    
    return True


def main():
    """Main entry point"""
    
    # Parse arguments
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n❌ Error: Please provide a folder path")
        print("\nExample:")
        print('  python test_real_world.py "C:\\Temp\\TestDownloads"')
        sys.exit(1)
    
    folder_path = sys.argv[1]
    use_ai = '--no-ai' not in sys.argv
    export = '--export' in sys.argv
    
    # Run test
    try:
        success = run_real_world_test(folder_path, use_ai, export)
        
        if success:
            print("=" * 80)
            print("✅ Test completed successfully!")
            print("=" * 80)
            sys.exit(0)
        else:
            print("=" * 80)
            print("❌ Test failed - see errors above")
            print("=" * 80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
