"""
Undo D:\ Drive Organization

This script reads the undo history and reverts the D:\ organization.
"""

import json
import shutil
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    history_file = Path('.undo_journal/history.json')
    
    if not history_file.exists():
        logger.error("No undo history found!")
        return
    
    # Load history
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    if not history:
        logger.error("Undo history is empty!")
        return
    
    # Get last operation
    last_op = history[-1]
    
    print("=" * 70)
    print("UNDO LAST OPERATION")
    print("=" * 70)
    print(f"Folder: {last_op.get('folder', 'Unknown')}")
    print(f"Timestamp: {last_op.get('timestamp', 'Unknown')}")
    print(f"Files organized: {len(last_op.get('operations', []))}")
    print("=" * 70)
    
    confirm = input("\n⚠️  Undo this operation? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    # Undo operations
    operations = last_op.get('operations', [])
    success_count = 0
    failed = []
    
    print(f"\nUndoing {len(operations)} operations...")
    
    for i, op in enumerate(operations, 1):
        try:
            source = Path(op['source'])
            target = Path(op['target'])
            
            if target.exists():
                # Create parent directory for source
                source.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file back
                shutil.move(str(target), str(source))
                success_count += 1
                
                if i % 100 == 0:
                    print(f"  ✓ Progress: {i}/{len(operations)} files restored")
            else:
                logger.warning(f"Target not found: {target}")
                failed.append(str(target))
                
        except Exception as e:
            logger.error(f"Failed to undo {target.name}: {e}")
            failed.append(str(target))
    
    print("\n" + "=" * 70)
    print("UNDO COMPLETE")
    print("=" * 70)
    print(f"✓ Successfully restored: {success_count}/{len(operations)} files")
    
    if failed:
        print(f"✗ Failed to restore: {len(failed)} files")
        print("\nFailed files:")
        for f in failed[:10]:
            print(f"  - {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Remove from history
    if success_count == len(operations):
        history.pop()
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        print("\n✓ Operation removed from undo history")
    
    print("\n✓ D:\\ drive has been restored to original state!")
    print("  Now you can re-run organization with the fixed code.")

if __name__ == '__main__':
    main()
