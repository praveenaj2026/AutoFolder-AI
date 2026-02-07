# Week 8 Plan: Preview Builder v2

**Timeline**: 3-4 days  
**Status**: 📝 Planning  
**Dependencies**: Weeks 1-7 complete

## Overview

Create Preview Builder v2 that generates comprehensive, user-facing previews of the proposed file organization before execution. Shows folder structure, file counts, confidence scores, and AI groupings.

## Objectives

1. Generate visual preview of proposed organization
2. Show both rule-based and AI-grouped suggestions
3. Display confidence scores and context information
4. Calculate statistics (files moved, folders created, etc.)
5. Format output for terminal display
6. Support export to text file for review

## Current State Analysis

### Existing PreviewBuilder (v1)
- Location: [src/core/preview_builder.py](src/core/preview_builder.py)
- Uses: organize_result.py with SimpleOrganizeResult
- Output: Terminal-formatted tree structure
- Limitations:
  - No AI grouping support
  - No confidence scores
  - Limited statistics
  - No export functionality

### New Requirements (v2)
- Input: OrganizedFiles + PlacementDecision list + optional AIResult list
- Output: Enhanced preview with AI context
- Show both individual files and grouped files
- Display confidence indicators
- Export-friendly format

## Data Flow

```
┌─────────────────┐
│  Scanner v2     │
│  (Week 1-2)     │
└────────┬────────┘
         │ files
         ▼
┌─────────────────┐
│  Rule Engine v2 │
│  (Week 4)       │
└────────┬────────┘
         │ Results
         ▼
┌─────────────────┐
│  AI Grouper v2  │
│  (Week 7)       │──────┐
└────────┬────────┘      │ ai_results
         │               │
         ▼               │
┌─────────────────┐      │
│ Context Builder │      │
│  (Week 4)       │      │
└────────┬────────┘      │
         │ Context       │
         ▼               │
┌─────────────────┐      │
│Placement        │      │
│Resolver (W5-6)  │◄─────┘
└────────┬────────┘
         │ PlacementDecisions
         ▼
┌─────────────────┐
│Preview Builder  │ ◄── WEEK 8 (THIS)
│  v2             │
└────────┬────────┘
         │ Preview
         ▼
┌─────────────────┐
│  User Review    │
└─────────────────┘
```

## Implementation Design

### Core Class: PreviewBuilderV2

```python
@dataclass
class PreviewConfig:
    """Configuration for preview generation."""
    show_confidence: bool = True
    show_ai_groups: bool = True
    max_files_per_folder: int = 10  # Show first N files
    show_hidden: bool = False
    color_output: bool = True  # Terminal colors
    export_path: Optional[Path] = None

@dataclass
class PreviewStats:
    """Statistics about the organization preview."""
    total_files: int
    total_folders: int
    files_moved: int
    folders_created: int
    ai_groups_found: int
    avg_confidence: float
    protected_files: int

class PreviewBuilderV2:
    """Builds user-facing preview of file organization."""
    
    def __init__(self, config: PreviewConfig = None):
        self.config = config or PreviewConfig()
    
    def build_preview(
        self,
        placements: List[PlacementDecision],
        ai_results: List[AIResult] = None,
        base_path: Path = None
    ) -> str:
        """Generate preview of organization."""
        pass
    
    def _build_tree(self, placements: List[PlacementDecision]) -> Dict:
        """Build folder tree structure."""
        pass
    
    def _format_tree(self, tree: Dict, indent: int = 0) -> List[str]:
        """Format tree as visual ASCII tree."""
        pass
    
    def _calculate_stats(
        self,
        placements: List[PlacementDecision],
        ai_results: List[AIResult]
    ) -> PreviewStats:
        """Calculate organization statistics."""
        pass
    
    def _format_ai_groups(self, ai_results: List[AIResult]) -> List[str]:
        """Format AI grouping information."""
        pass
    
    def _colorize(self, text: str, color: str) -> str:
        """Add terminal color codes."""
        pass
    
    def export_preview(self, preview: str, path: Path):
        """Export preview to text file."""
        pass
```

### Tree Building Algorithm

```python
def _build_tree(self, placements):
    """
    Convert flat placements to nested tree structure.
    
    Input: 
    - PlacementDecision(file="doc1.pdf", folder="Documents/Work/2025")
    - PlacementDecision(file="doc2.pdf", folder="Documents/Personal")
    
    Output:
    {
        "Documents": {
            "_files": [],
            "Work": {
                "_files": [],
                "2025": {
                    "_files": ["doc1.pdf"]
                }
            },
            "Personal": {
                "_files": ["doc2.pdf"]
            }
        }
    }
    """
    tree = {}
    for placement in placements:
        parts = placement.final_path.parts
        current = tree
        
        # Navigate/create nested structure
        for part in parts[:-1]:  # Folders
            if part not in current:
                current[part] = {"_files": []}
            current = current[part]
        
        # Add file
        if "_files" not in current:
            current["_files"] = []
        current["_files"].append({
            "name": parts[-1],
            "confidence": placement.confidence,
            "ai_grouped": placement.ai_group is not None,
            "protected": placement.is_protected
        })
    
    return tree
```

### Preview Format

```
╔════════════════════════════════════════════════════════════════╗
║              AutoFolder AI - Organization Preview              ║
╚════════════════════════════════════════════════════════════════╝

📊 Statistics
─────────────────────────────────────────────────────────────────
  Total Files:          247
  Total Folders:        18
  Files to Move:        235
  Folders to Create:    12
  AI Groups Found:      8
  Avg Confidence:       87%
  Protected Files:      12

📁 Folder Structure
─────────────────────────────────────────────────────────────────
Documents/
├── Work/
│   ├── 2025/
│   │   ├── report_q1.pdf [95%]
│   │   ├── budget_2025.xlsx [92%]
│   │   └── ... (8 more files)
│   └── Archive/
│       └── old_docs/ [Protected]
├── Personal/
│   ├── taxes_2025/ [AI Group: "Tax 2025", 4 files, 88%]
│   │   ├── tax_form_1040.pdf
│   │   ├── tax_w2.pdf
│   │   └── ... (2 more files)
│   └── receipts.pdf [82%]
├── Invoices/
│   └── ... (15 files)
└── ... (5 more folders)

Images/
├── Vacation/
│   └── vacation_2025/ [AI Group: "Vacation 2025", 12 files, 91%]
│       ├── beach_1.jpg
│       ├── beach_2.jpg
│       └── ... (10 more files)
└── Screenshots/
    └── ... (43 files)

... (3 more root folders)

🤖 AI Groupings
─────────────────────────────────────────────────────────────────
  1. "Vacation 2025" (12 files, 91% confidence)
     → Images/Vacation/vacation_2025/
  
  2. "Tax 2025" (4 files, 88% confidence)
     → Documents/Personal/taxes_2025/
  
  3. "Project Meeting Notes" (6 files, 85% confidence)
     → Documents/Work/2025/meetings/
  
  ... (5 more groups)

⚠️  Notes
─────────────────────────────────────────────────────────────────
  • 12 files are protected and will remain in place
  • Files with confidence < 70% should be reviewed
  • AI groups are suggestions based on semantic similarity
  • You can modify this organization before applying

═════════════════════════════════════════════════════════════════
```

## Testing Strategy

### Test File: `tests/core_v2/test_preview_builder.py`

```python
class TestPreviewConfig:
    """Test preview configuration."""
    def test_default_config()
    def test_custom_config()

class TestPreviewBuilderV2:
    """Test preview builder core functionality."""
    def test_initialization()
    def test_build_simple_preview()
    def test_build_preview_with_ai_groups()
    def test_tree_building()
    def test_calculate_stats()
    def test_format_tree_single_level()
    def test_format_tree_nested()
    def test_format_tree_with_files()
    def test_max_files_limit()
    def test_confidence_indicators()

class TestAIGroupFormatting:
    """Test AI group display."""
    def test_format_single_ai_group()
    def test_format_multiple_ai_groups()
    def test_format_no_ai_groups()

class TestStatistics:
    """Test statistics calculation."""
    def test_calculate_basic_stats()
    def test_calculate_with_ai_groups()
    def test_calculate_with_protected_files()

class TestColorization:
    """Test terminal color output."""
    def test_colorize_high_confidence()  # Green
    def test_colorize_medium_confidence()  # Yellow
    def test_colorize_low_confidence()  # Red
    def test_colorize_disabled()

class TestExport:
    """Test export functionality."""
    def test_export_to_file()
    def test_export_strips_colors()

# Estimated: 20 tests
```

## Color Scheme

```python
COLORS = {
    'high': '\033[92m',      # Green (confidence >= 0.85)
    'medium': '\033[93m',    # Yellow (0.70 <= confidence < 0.85)
    'low': '\033[91m',       # Red (confidence < 0.70)
    'ai_group': '\033[94m',  # Blue (AI grouped files)
    'protected': '\033[95m', # Magenta (protected files)
    'reset': '\033[0m'       # Reset color
}
```

## Key Features

### 1. Hierarchical Tree Display
- ASCII tree structure (├─, └─, │)
- Nested folder visualization
- File count summaries
- "..." indicators for truncated lists

### 2. Confidence Indicators
- Percentage shown next to each file/folder
- Color coding: Green (high), Yellow (medium), Red (low)
- Average confidence in statistics

### 3. AI Group Highlighting
- Special markers for AI-grouped files
- Group summary with file count
- Confidence score for entire group
- Target folder path

### 4. Statistics Dashboard
- Total files/folders
- Move operations count
- New folders to create
- AI groups detected
- Protected files count

### 5. Export Functionality
- Save preview to text file
- Strip color codes for clean output
- Useful for sharing/review

## Integration Points

### Input
```python
# From Placement Resolver (Week 5-6)
placements: List[PlacementDecision]

# From AI Grouper (Week 7)
ai_results: List[AIResult] = None

# Optional base path for relative display
base_path: Path = None
```

### Output
```python
# String preview for terminal display
preview: str

# Statistics object
stats: PreviewStats
```

### Usage in Pipeline
```python
# Complete pipeline
files = scanner.scan(Path("D:/Downloads"))
rule_results = rule_engine.apply_rules(files)
ai_results = ai_grouper.group_files(files, rule_results)
context = context_builder.build_context(Path("D:/Downloads"), files)
placements = resolver.resolve_placements(rule_results, context, ai_results)

# Generate preview
preview_builder = PreviewBuilderV2()
preview = preview_builder.build_preview(placements, ai_results)
print(preview)

# Export if needed
preview_builder.export_preview(preview, Path("preview.txt"))
```

## Implementation Steps

### Day 1: Core Structure (3-4 hours)
- [ ] Create `src/core_v2/preview_builder.py`
- [ ] Implement PreviewConfig dataclass
- [ ] Implement PreviewStats dataclass
- [ ] Implement PreviewBuilderV2 class skeleton
- [ ] Implement `_build_tree()` method
- [ ] Write basic tests for tree building

### Day 2: Formatting (3-4 hours)
- [ ] Implement `_format_tree()` with ASCII art
- [ ] Implement `_format_ai_groups()`
- [ ] Implement `_calculate_stats()`
- [ ] Add confidence indicators
- [ ] Write formatting tests

### Day 3: Enhancement (2-3 hours)
- [ ] Implement color output (`_colorize()`)
- [ ] Implement export functionality
- [ ] Add file truncation (max_files_per_folder)
- [ ] Add protected file markers
- [ ] Write colorization and export tests

### Day 4: Testing & Polish (2-3 hours)
- [ ] Complete test suite (target: 20 tests)
- [ ] Manual testing with real data
- [ ] Create demo script
- [ ] Update documentation
- [ ] Commit to git

## Success Criteria

- [ ] 20+ tests passing (100%)
- [ ] Clean, readable tree structure
- [ ] Accurate statistics calculation
- [ ] AI groups clearly displayed
- [ ] Confidence scores visible
- [ ] Export works correctly
- [ ] Colors work on Windows terminal
- [ ] Performance: <100ms for 1000 files

## Edge Cases to Handle

1. **Empty placements**: Show "No files to organize"
2. **Very deep nesting**: Limit depth or use "..." 
3. **Long filenames**: Truncate with "..."
4. **No AI results**: Skip AI section
5. **All protected files**: Special message
6. **Large file counts**: Truncate with "(N more files)"
7. **Terminal width**: Wrap long lines
8. **Export without colors**: Strip ANSI codes

## Performance Considerations

- Tree building: O(n) where n = number of placements
- Formatting: O(m) where m = number of tree nodes
- Expected: <100ms for 1000 files
- Memory: ~1MB for large previews

## Dependencies

- Standard library: pathlib, dataclasses, typing
- No external dependencies (colors using ANSI codes)
- Integrates with: PlacementDecision, AIResult (from models)

## Documentation

- Update [USER_GUIDE.md](docs/USER_GUIDE.md) with preview examples
- Add section on interpreting confidence scores
- Document AI group markers
- Show export functionality

## Future Enhancements (Not in v2.0)

- Interactive preview (select/deselect folders)
- Web-based preview (HTML output)
- Diff view (before/after)
- Undo/redo suggestions
- Custom color schemes
- Preview filtering (show only AI groups, etc.)

## Notes

- Use Windows-compatible ANSI color codes
- Test on both PowerShell and CMD
- Keep preview under 1000 lines for readability
- Export should be GitHub-readable markdown

---

**Estimated Timeline**: 3-4 days  
**Estimated Tests**: 20  
**Estimated Lines**: ~400-500

**Next**: Week 9-10: Integration Testing & Validation
