"""Check remaining unsafe calls"""
from pathlib import Path
import re

files = list(Path('src/core').glob('*.py'))
total_unsafe = 0

print("\n📊 REMAINING UNSAFE .stat() CALLS:\n")
for f in files:
    if f.name == '__init__.py':
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        content = f.read_text(encoding='latin-1')
    # Count .stat() but exclude safe_stat()
    unsafe = len(re.findall(r'(?<!safe_)(?<!def )\.stat\(\)', content))
    if unsafe > 0:
        total_unsafe += unsafe
        print(f"  {f.name}: {unsafe} calls")

print(f"\n{'✅ ALL PROTECTED!' if total_unsafe == 0 else f'⚠️  {total_unsafe} calls remaining'}\n")
