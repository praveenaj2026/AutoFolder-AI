# Week 7: AI Grouper v2 Implementation Plan

## Overview

Week 7 builds the **AI Grouper** - semantic file grouping using sentence transformers to understand file purpose and content beyond just extensions.

## Goals

1. **Semantic Understanding**: Group files by meaning, not just format
   - "Vacation Photos 2023" vs "Work Presentations"
   - "Tax Documents 2025" vs "Personal Letters"
   - "Python Scripts" vs "JavaScript Projects"

2. **Context-Aware Grouping**: Leverage ContextBuilder insights
   - Detect existing folder organization
   - Respect meaningful groupings
   - Suggest intelligent group names

3. **Integration with Placement Resolver**: Generate AIResult objects
   - Placement Resolver already accepts `ai_results` parameter
   - AI groups override rule-based when confidence is high
   - Hybrid approach: rules + AI

## Technical Design

### Core Component: `ai_grouper.py`

```python
class AIGroupConfig:
    """Configuration for AI grouping."""
    min_group_size: int = 3          # Minimum files per AI group
    max_group_size: int = 50         # Maximum files per AI group
    similarity_threshold: float = 0.75  # Cosine similarity threshold
    use_content_analysis: bool = False  # Read file contents (expensive)
    max_content_bytes: int = 10000   # Max bytes to read for analysis

class AIGrouper:
    """
    Groups files semantically using sentence transformers.
    
    Uses:
    - Filename analysis (primary)
    - File metadata (dates, sizes)
    - Optional content analysis (for text files)
    """
    
    def __init__(self, config: AIGroupConfig):
        # Load sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.config = config
    
    def group_files(
        self,
        file_nodes: List[FileNode],
        rule_results: List[RuleResult],
        context_builder: ContextBuilder
    ) -> List[AIResult]:
        """
        Group files semantically.
        
        Args:
            file_nodes: Files to group
            rule_results: Rule-based classifications (for context)
            context_builder: For folder context analysis
            
        Returns:
            List of AIResult objects with group suggestions
        """
        # 1. Extract features from filenames
        # 2. Generate embeddings
        # 3. Cluster similar files
        # 4. Name groups intelligently
        # 5. Create AIResult objects
```

### Feature Extraction

**From Filenames**:
- Remove extensions, dates, numbers
- Extract meaningful words
- Detect patterns: "report_Q1_2025.pdf" → "quarterly report"

**From Metadata**:
- Creation/modification dates → temporal grouping
- File sizes → similar content types
- Directory structure → existing organization

**From Content** (optional, expensive):
- First few KB of text files
- Extract keywords, topics
- OCR for images (future enhancement)

### Clustering Algorithm

**DBSCAN** (Density-Based Spatial Clustering):
- Handles variable cluster sizes
- Finds outliers (ungroupable files)
- No need to specify number of clusters

**Process**:
1. Generate embeddings for all files
2. Compute pairwise similarity matrix
3. Apply DBSCAN with similarity_threshold
4. Validate cluster quality
5. Merge small clusters or reject

### Group Naming

**Strategies**:
1. **Common Terms**: Extract frequent words across filenames
2. **Date Patterns**: "January 2025 Documents"
3. **Topic Detection**: "Financial Reports", "Vacation Photos"
4. **Fallback**: Rule-based category + subcategory

### Integration with Placement Resolver

```python
# Placement Resolver already supports ai_results:
def resolve_placements(
    self,
    root_node: FileNode,
    rule_results: List[RuleResult],
    ai_results: Optional[List[AIResult]] = None  # <-- Here!
) -> List[PlacementDecision]:
    # Merge rule-based and AI groupings
    # AI takes precedence when confidence > threshold
```

**Conflict Resolution**:
- If AI groups high confidence: use AI grouping
- If rule-based clear: use rules
- If ambiguous: prefer rules (safer)

## Implementation Steps

### Step 1: Create AIGrouper Class (100-150 lines)
- Config dataclass
- Model loading
- Basic structure

### Step 2: Feature Extraction (100 lines)
- Filename parsing
- Date extraction
- Metadata analysis

### Step 3: Embedding Generation (50 lines)
- Load sentence transformer
- Batch embedding generation
- Caching for performance

### Step 4: Clustering Logic (150 lines)
- DBSCAN implementation
- Similarity matrix computation
- Cluster validation

### Step 5: Group Naming (100 lines)
- Common term extraction
- Pattern detection
- Intelligent naming

### Step 6: AIResult Creation (50 lines)
- Convert clusters to AIResult objects
- Set confidence scores
- Add reasoning

### Step 7: Integration (50 lines)
- Update Placement Resolver
- Merge AI + rule results
- Conflict resolution

### Step 8: Testing (200-300 lines)
- Unit tests for each component
- Integration tests
- Real-world scenarios

## Test Scenarios

1. **Date-Based Grouping**:
   - `vacation_2023_01.jpg`, `vacation_2023_02.jpg` → "Vacation Photos Jan 2023"

2. **Project Grouping**:
   - `thesis_intro.docx`, `thesis_chapter1.docx` → "Thesis Documents"

3. **Topic Grouping**:
   - `tax_form_2025.pdf`, `w2_2025.pdf` → "Tax Documents 2025"

4. **Mixed Groups**:
   - Some files clearly grouped, others ungrouped → hybrid approach

5. **Conflict Resolution**:
   - AI suggests "Work Docs", rules say "Documents/PDF" → smart merge

## Performance Considerations

**Model Loading**:
- Load once, reuse
- ~100MB memory footprint
- First run: download model (~80MB)

**Embedding Generation**:
- Batch processing: 100 files/second
- Incremental for large datasets
- Optional caching

**Clustering**:
- O(n²) for similarity matrix
- DBSCAN: O(n log n) with spatial index
- Acceptable for <10,000 files

## Dependencies

```
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

## Success Criteria

- ✅ Group semantically similar files (>75% accuracy)
- ✅ Generate meaningful group names
- ✅ Integrate with Placement Resolver
- ✅ Handle edge cases (outliers, small groups)
- ✅ 15+ unit tests covering all functionality
- ✅ Performance: <1s per 100 files
- ✅ Memory: <500MB for 10,000 files

## Timeline

- **Day 1**: Core structure + feature extraction (Steps 1-2)
- **Day 2**: Embedding + clustering (Steps 3-4)
- **Day 3**: Naming + integration (Steps 5-7)
- **Day 4**: Testing + validation (Step 8)

## Future Enhancements (Post-Week 7)

- Content analysis for text files
- OCR for images
- Multi-language support
- Learning from user corrections
- Temporal pattern detection (daily, weekly, monthly)

---

**Status**: Ready to implement  
**Next**: Create `src/core_v2/ai_grouper.py`
