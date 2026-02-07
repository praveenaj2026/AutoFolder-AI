# Week 9-10 Plan: Integration Testing & Validation

**Timeline**: 5-7 days  
**Status**: 📝 Planning  
**Dependencies**: Weeks 1-8 complete

## Overview

Comprehensive integration testing and validation of the complete v2.0 pipeline. Ensure all components work together seamlessly, handle edge cases, and perform well under stress.

## Objectives

1. End-to-end pipeline testing (all components integrated)
2. Stress testing (10K, 100K file scenarios)
3. Real-world validation (actual messy folders)
4. Performance profiling and optimization
5. Memory usage validation
6. Error handling and recovery
7. Cross-validation with expected behaviors

## Current Components to Integrate

```
┌─────────────┐
│  Scanner    │ Week 1-2: DeepScanner
│  (50 tests) │ ✅ Complete
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Root Detector│ Week 3: RootDetector
│  (23 tests) │ ✅ Complete
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Rule Engine  │ Week 4: RuleEngine
│  (37 tests) │ ✅ Complete
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Context      │ Week 4: ContextBuilder
│Builder      │ ✅ Complete
│  (16 tests) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Placement    │ Week 5-6: PlacementResolver
│Resolver     │ ✅ Complete (5 anti-redundancy rules)
│  (19 tests) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│AI Grouper   │ Week 7: AIGrouper
│  (16 tests) │ ✅ Complete (semantic grouping)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Preview      │ Week 8: PreviewBuilder
│Builder      │ ✅ Complete (visual previews)
│  (23 tests) │
└─────────────┘
```

**Total**: 168 tests (167 passing, 1 skipped)

## Testing Strategy

### Phase 1: End-to-End Pipeline (Day 1-2)

Create integration tests that run the entire pipeline:

```python
def test_full_pipeline_simple():
    """Test complete pipeline with small dataset."""
    # 1. Create test directory structure
    # 2. Scan with DeepScanner
    # 3. Detect protected roots
    # 4. Classify with RuleEngine
    # 5. Group with AIGrouper
    # 6. Build context
    # 7. Resolve placements
    # 8. Generate preview
    # 9. Validate output
```

**Test Scenarios**:
- Simple flat folder (20 files)
- Nested structure (5 levels, 50 files)
- Mixed file types (documents, images, code)
- Protected roots (project folder in Downloads)
- AI groupable files (vacation photos, tax documents)
- Naming conflicts
- Edge cases (empty folders, single files, huge files)

### Phase 2: Stress Testing (Day 3-4)

Test with large datasets:

**10K Files Test**:
- Generate 10,000 files with realistic names
- Various extensions
- Nested folder structure
- Measure: time, memory, accuracy

**100K Files Test**:
- Generate 100,000 files
- Stress test all components
- Monitor memory usage
- Ensure no crashes or slowdowns

**Deep Nesting Test**:
- Create 20-level deep structure
- Validate depth limits work
- Check path length limits

**Performance Targets**:
- 10K files: < 30 seconds
- 100K files: < 5 minutes
- Memory: < 2GB for 100K files
- No memory leaks

### Phase 3: Real-World Validation (Day 5)

Test with actual messy folders:

**Test Cases**:
1. Downloads folder snapshot
2. Desktop cleanup scenario
3. Photo library organization
4. Document archive
5. Mixed content folder

**Validation**:
- Manual review of organization quality
- Check for logical groupings
- Verify protected roots respected
- Confirm AI groupings make sense

### Phase 4: Error Handling (Day 6)

Test failure scenarios:

**Error Cases**:
- Permission denied files
- Locked files (in use)
- Network paths
- Invalid paths
- Corrupted files
- Disk full simulation
- ML model unavailable

**Recovery**:
- Graceful degradation
- Clear error messages
- Partial completion handling
- Rollback capability

### Phase 5: Cross-Component Validation (Day 7)

Ensure components interact correctly:

**Integration Points**:
- Scanner → Root Detector
- Root Detector → Rule Engine (skip protected)
- Rule Engine → Context Builder
- Context + Rules → Placement Resolver
- AI Grouper → Placement Resolver
- Placements → Preview Builder

**Validation**:
- Data flows correctly
- No information loss
- Immutability preserved
- Performance acceptable

## Implementation Plan

### Test File Structure

```
tests/
├── integration/
│   ├── __init__.py
│   ├── test_full_pipeline.py         # End-to-end tests
│   ├── test_stress.py                # Performance tests
│   ├── test_real_world.py            # Realistic scenarios
│   ├── test_error_handling.py        # Failure scenarios
│   └── fixtures/
│       ├── create_test_data.py       # Generate test files
│       └── scenarios.py              # Test scenario definitions
└── core_v2/
    └── ... (existing unit tests)
```

### Key Integration Test Class

```python
class TestFullPipeline:
    """End-to-end integration tests."""
    
    def test_simple_organization(self, tmp_path):
        """Test basic organization flow."""
        # Setup
        test_folder = self._create_test_structure(tmp_path, scenario="simple")
        
        # Execute pipeline
        result = run_full_pipeline(test_folder)
        
        # Validate
        assert result.total_files > 0
        assert result.folders_created > 0
        assert result.preview is not None
        
    def test_with_protected_roots(self, tmp_path):
        """Test that protected roots are respected."""
        # Create test structure with project folder
        test_folder = self._create_project_in_downloads(tmp_path)
        
        # Run pipeline
        result = run_full_pipeline(test_folder)
        
        # Verify project folder untouched
        project_files = list((tmp_path / "MyProject").rglob("*"))
        for file in project_files:
            placement = result.get_placement_for(file)
            assert placement.source == DecisionSource.PROTECTED
            assert placement.target == file  # No move
    
    def test_ai_grouping_integration(self, tmp_path):
        """Test AI grouping affects placement."""
        # Create vacation photos
        photos = self._create_vacation_photos(tmp_path)
        
        # Run pipeline
        result = run_full_pipeline(tmp_path)
        
        # Check all photos grouped together
        vacation_placements = [p for p in result.placements if "vacation" in p.file.name.lower()]
        target_folders = {p.target.parent for p in vacation_placements}
        assert len(target_folders) == 1  # All in same folder
```

### Stress Test Implementation

```python
class TestStress:
    """Stress tests with large datasets."""
    
    @pytest.mark.slow
    def test_10k_files(self, tmp_path):
        """Test with 10,000 files."""
        # Generate realistic 10K file structure
        self._generate_files(tmp_path, count=10_000)
        
        # Time the pipeline
        start = time.time()
        result = run_full_pipeline(tmp_path)
        duration = time.time() - start
        
        # Validate performance
        assert duration < 30.0  # Under 30 seconds
        assert result.total_files == 10_000
        
        # Check memory usage
        memory_mb = self._get_memory_usage()
        assert memory_mb < 500  # Under 500MB
    
    @pytest.mark.slow
    @pytest.mark.skipif(os.getenv("CI"), reason="Too slow for CI")
    def test_100k_files(self, tmp_path):
        """Test with 100,000 files."""
        self._generate_files(tmp_path, count=100_000)
        
        start = time.time()
        result = run_full_pipeline(tmp_path)
        duration = time.time() - start
        
        assert duration < 300.0  # Under 5 minutes
        assert result.total_files == 100_000
```

### Real-World Scenario Tests

```python
class TestRealWorld:
    """Tests with realistic folder structures."""
    
    def test_downloads_cleanup(self, tmp_path):
        """Simulate typical Downloads folder."""
        # Mix of:
        # - PDFs (invoices, documents)
        # - Images (screenshots, photos)
        # - Installers (.exe, .msi)
        # - Archives (.zip, .rar)
        # - Random files
        self._create_downloads_scenario(tmp_path)
        
        result = run_full_pipeline(tmp_path)
        
        # Validate categories created
        assert (tmp_path / "Documents").exists()
        assert (tmp_path / "Images").exists()
        assert (tmp_path / "Installers").exists()
        assert (tmp_path / "Archives").exists()
```

## Performance Profiling

Use cProfile and memory_profiler:

```python
import cProfile
import pstats
import memory_profiler

def profile_pipeline():
    """Profile full pipeline execution."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run pipeline
    result = run_full_pipeline(test_path)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

**Focus Areas**:
- Scanner file tree building
- Rule engine classification
- AI grouper embedding generation
- Placement resolver anti-redundancy rules
- Preview builder tree formatting

## Success Criteria

### Correctness
- [ ] All integration tests pass
- [ ] Protected roots never modified
- [ ] AI groupings logically correct
- [ ] Anti-redundancy rules work
- [ ] No data loss or corruption

### Performance
- [ ] 10K files in < 30 seconds
- [ ] 100K files in < 5 minutes
- [ ] Memory usage < 2GB
- [ ] No memory leaks
- [ ] Responsive during operation

### Robustness
- [ ] Handles permission errors
- [ ] Graceful ML model failure
- [ ] Works with edge cases
- [ ] Clear error messages
- [ ] Partial completion possible

### Quality
- [ ] Organization makes sense
- [ ] Folder names intuitive
- [ ] Depth limits respected
- [ ] Minimum group sizes enforced
- [ ] Confidence scores accurate

## Test Data Generation

Create realistic test data generator:

```python
class TestDataGenerator:
    """Generate realistic test file structures."""
    
    def generate_downloads_folder(self, path: Path, file_count: int):
        """Generate typical Downloads folder."""
        # PDFs: 30%
        # Images: 25%
        # Documents: 20%
        # Installers: 10%
        # Archives: 10%
        # Other: 5%
        
    def generate_photo_library(self, path: Path, photo_count: int):
        """Generate photo library with events."""
        # Vacation photos (grouped)
        # Family events
        # Random screenshots
        # Camera exports
        
    def generate_project_structure(self, path: Path):
        """Generate development project."""
        # src/ folder
        # .git/ folder
        # package.json
        # README.md
```

## Optimization Opportunities

Based on profiling results:

1. **Scanner**: Parallel directory traversal
2. **Rule Engine**: Cache results
3. **AI Grouper**: Batch embedding generation
4. **Placement Resolver**: Optimize tree operations
5. **Preview Builder**: Lazy tree formatting

## Deliverables

- [ ] `test_full_pipeline.py` (20+ tests)
- [ ] `test_stress.py` (5+ tests)
- [ ] `test_real_world.py` (10+ tests)
- [ ] `test_error_handling.py` (15+ tests)
- [ ] Test data generator
- [ ] Performance profiling report
- [ ] Integration documentation
- [ ] Optimization recommendations

## Timeline

**Day 1**: Full pipeline tests (basic scenarios)  
**Day 2**: Full pipeline tests (complex scenarios)  
**Day 3**: Stress tests (10K files)  
**Day 4**: Stress tests (100K files, deep nesting)  
**Day 5**: Real-world validation  
**Day 6**: Error handling tests  
**Day 7**: Performance profiling, optimization

**Estimated**: 50+ new integration tests  
**Total Tests**: 168 + 50 = 218+

## Notes

- Mark slow tests with `@pytest.mark.slow`
- Skip 100K test in CI with `@pytest.mark.skipif`
- Use fixtures for test data generation
- Clean up test files after each test
- Profile memory usage during stress tests
- Document any performance bottlenecks found

---

**Next**: Week 11 - Side-by-Side Comparison (v1 vs v2 on real data)
