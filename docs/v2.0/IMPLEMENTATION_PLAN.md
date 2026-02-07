# AutoFolder AI v2.0 — Implementation Plan

**Status:** Planning Phase  
**Start Date:** February 7, 2026  
**Target:** Production-ready v2.0 replacing v1.0  
**Evidence:** D:\ drive shows v1.0 issues (excessive nesting, redundant folders)

---

## Executive Summary

**Why v2.0 Now:**
- v1.0 creates problems we documented:
  - `D:\Audio\MP3 Collection\MP3\` ← Redundant nesting
  - `D:\Documents\Alias\TXT\` ← Created folder for 1-2 files
  - Hundreds of tiny subfolders
- User chose to skip v1.0 distribution and go straight to v2.0
- Real-world evidence validates architecture document predictions

**Core Goal:** Fix the 7 architectural issues with a complete rewrite of `src/core/organizer.py`.

**User Priority:** Quality over speed. Time is not a constraint. Target: 100% improvement (zero redundancy, zero over-organization).

---

## Phase Breakdown

### Phase 1: Foundation & Models (Week 1-2)
**Goal:** Build rock-solid data structures and deep scanner

**Quality Focus:**
- Immutable data structures (prevent bugs)
- Comprehensive type hints (catch errors early)
- 100% test coverage on models
- Property-based testing (hypothesis library)

**Tasks:**
1. Create `src/core_v2/` directory structure
2. Implement all 6 data classes with full validation:
   - `FileNode` (immutable, frozen dataclass)
   - `RootInfo` (with confidence scoring)
   - `RuleResult` (with context)3)
**Goal:** 100% accurate project/special folder protection

**Quality Focus:**
- Zero false positives (never protect wrong folders)
- Zero false negatives (never miss protected folders)
- Confidence scoring (how sure are we?)
- User override capability

**Tasks:**
1. Research and document ALL project markers:
   - Python: `requirements.txt`, `setup.py`, `pyproject.toml`, `.venv/`, `poetry.lock`
   - Node.js: `package.json`, `node_modules/`, `yarn.lock`, `pnpm-lock.yaml`
   - Java: `pom.xml`, `build.gradle`, `.mvn/`
   - C/C++: `CMakeLists.txt`, `Makefile`, `.sln`, `.vcxproj`
   - Rust: `Cargo.toml`, `Cargo.lock`
   - Go: `go.mod`, `go.sum`
   - Git: `.git/`, `.gitignore`
   - Docker: `Dockerfile`, `docker-compose.yml`
   - Game: `*.exe` + save folders, mod folders
   - VMs: `.vdi`, `.vmdk`, `.vbox` files
2. Implement confidence scoring (0.0-1.0)
3. Add marker combination rules (stronger signals)
4. Test against 50+ real project folders
5. Implement user whitelist/blacklist
6. Add "scan mode" that reports what would be protected

**Deliverable:** Root detector with 100% accuracy on test suite

### Phase 2: Root Detection (Week 1)
**Goal:** Protect project folders and special directories

**Tasks:**
1. Implement `RootInfo` data class
2. Create root detection heuristics:
   - PROJECT: `.git/`, `package.json`, `requirements.txt`, `node_modules/`
   - MEDIA: `DCIM/`, camera folder patterns, `.nomedia`
   - ARCHIVE: Time-stamped archives
   - BACKUP: Backup tool markers
   - GAME: Game save files, installation folders
3. Write detection rules for each type
4. Test against real folders (Python Scripts, VirtualBox VMs, Steam Games)
5. Add safety checks (never move files OUT of detected roots)

**Deliverable:** Root detector that correctly identifies protected folders

---

### Phase 3: Rule Engine v2 (Week 2)
**Goal:** Rule-first pipeline with context hints

**Tasks:**
1. Implement `RuleResult` data class
2. Enhance rule matching:
   - Extension-based (fast path)
   - Content analysis (magic bytes)
   - Folder context extraction
3. Add rule confidence scoring
4. Fix missing extensions from v1 (already done: `.md`, `.log`, `.sh`, `.ps1`)
5. Test against 1000+ file samples

**Deliverable:** Rule engine that assigns categories with confidence scores

---

### Phase 4: Context Builder (Week 2)
**Goal:** Give AI folder context for better grouping

**Tasks:**
1. Implement `ContextInheritor` stage
2. Extract meaningful context:
   - Parent folder name
   - Sibling file types
   - Date patterns in path
   - Common prefixes/suffixes
3. Build context strings for AI input
4. Test: Does AI group better with context?

**Deliverable:** Context builder that enriches file metadata

---

### Phase 5: AI Grouper v2 (Week 3)
**Goal:** Context-aware AI with minimum group size

**Tasks:**5-6) ⭐ CRITICAL
**Goal:** ZERO redundancy, ZERO over-organization

**Quality Focus:** This is THE core fix. Take time to get it perfect.

**Anti-Redundancy Rules:**
1. **Collection Folder Prevention:**
   - If AI suggests "MP3 Collection" AND rule says "MP3/" → Use ONLY "MP3/"
   - If AI suggests "ZIP Collection" AND rule says "Archives/ZIP/" → Use ONLY "Archives/ZIP/"
   - Pattern: Detect when AI group name contains file type, merge with rule folder

2. **Minimum Group Size Enforcement:**
   - AI groups require ≥5 files (increased from 3)
   - Exception: High-confidence semantic groups (e.g., "Resume_2024", "VacationPhotos")
   - Files below threshold stay in place or go to rule-based folder

3. **Depth Limit:**
   - Maximum nesting: 3 levels (e.g., `Documents/PDF/Work/`)
   - Prevent: `Documents/Backup/TXT/Config/` (4 levels)
   - Flatten if depth exceeds limit

4. **Sibling Analysis:**
   - If folder would contain only 1-2 files → Don't create
   - Merge small siblings into parent
   - Example: Instead of `Code/Agent/`, `Code/Argv/`, `Code/Chat/` with 1 file each → `Code/`

5. **Context Collapse:**
   - If AI group name matches parent folder name → Don't create subfolder
   - Example: In `Projects/WebApp/`, don't create `Projects/WebApp/WebApp Files/`

**Tasks:**
1. Implement all 5 anti-redundancy rules
2. Add "dry run" mode that logs what would be prevented
3. Test against v1.0 D:\ drive output (must fix ALL issues)
4. Create visual diff tool (v1 vs v2 structure)
5. Implement conflict resolution:
   - Rename with counter (`file (1).txt`)
   - Detect semantic duplicates (AI-based7-8)
**Goal:** Bulletproof validation - catch every bug

**Quality Focus:**
- Test EVERYTHING
- Real-world data, not toy examples
- Stress testing (100K files)
- Edge cases (permissions, long paths, special characters)

**Tasks:**
1. Create pipeline orchestrator
2. Add progress callbacks
3. Write integration tests:
   - 4 scenarios from architecture doc
   - 20 additional real-world scenarios
   - Edge cases: empty folders, symlinks, locked files
4. Test against REAL data:
   - D:\ drive (before undo)
   - C:\Users\Praveen\Downloads\
   - Test folders with 10K+ files
5. Stress testing:
   - 100K files
   - Deep nesting (20+ levels)
   - Long paths (>260 chars)
   - Unicode filenames
   - Locked files
6. Performance benchmarks:
   - 1K, 10K, 100K files
   - Memory usage
   - CPU usage
7. Create visual diff tool:
   - Show v1 vs v2 output side-by-side
   - Highlight improvements
   - Export to HTML report
8. User acceptance testing:
   - Run on YOUR data
   - Verify 100% improvement
   - Check undo works perfectly

**Deliverable:** v2.0 engine with 100% test pass rate
**Deliverable:** Placement resolver with ZERO redundancy in test ru
2. Create decision priority:
   - Protected roots → SKIP
   - High-confidence rules → MOVE
   - AI groups (≥3 files) → MOVE
   - Low confidence → SKIP
3. Detect redundant nesting:
   - Don't create `MP3 Collection/MP3/`
   - Don't create folders for <3 files
4. Handle conflicts (rename, skip, merge)
5. Validate all moves are safe

**Deliverable:** Placement resolver that makes smart, safe decisions

---

### Phase 7: Preview Builder v2 (Week 4)
**Goal:** User-friendly preview with full audit trail

**Tasks:**
1. Implement `PreviewResult` data class
2. Build tree-style preview
3. Show statistics:
   - Files to move
   - Files to skip
   - Conflicts detected
4. Full audit trail (why each decision was made)
5. GUI integration

**Deliverable:** Preview that shows exactly what will happen and why

---

### Phase 8: Integration & Testing (Week 5)
**Goal:** Wire up all stages and validate end-to-end

**Tasks:**
1. Create pipeline orchestrator
2. Add progress callbacks
3. Wire to existing GUI (minimal changes)
4. Run test suites:
   - Unit tests (each stage)
   - Integration tests (4 scenarios from architecture doc)
   - Real-world test (D:\ drive)
5. Performance benchmarks

**Deliverable:** Complete v2.0 engine ready for testing

---

### Phase 9: Side-by-Side Testing (Week 6)
**Goal:** Validate v2 fixes v1 issues

**Tasks:**
1. Add feature flag: `use_v2_engine: true/false`
2. Run both engines on same test data
3. Compare outputs:
   - v1: `D:\Audio\MP3 Collection\MP3\`
   - v2: `D:\Audio\MP3\` (flat, correct)
4. Document differences
5. Fix any regressions

**Deliverable:** Proof that v2 is better than v1

---

### Phase 10: Migration & Rollout (Week 7)
**Goal:** Replace v1 with v2 as default

**Tasks:**
1. Set `use_v2_engine: true` by default
2. Keep v1 as fallback option
3. Update documentation
4. Announce v2.0 release
5. Monitor for issues

**Deliverable:** v2.0 is production default

---

## Detailed Task List (Prioritized)

### PRIORITY 1 (Must Have - Core Fixes)

#### P1.1: Deep Scanner (Week 1, Days 1-2)
- [ ] Create `src/core_v2/__init__.py`
- [ ] Create `src/core_v2/models.py` (all data classes)
- [ ] Create `src/core_v2/scanner.py`
- [ ] Implement `DeepScanner.scan(root: Path) -> FileNode`
- [ ] Use `os.scandir()` for performance
- [ ] Handle permission errors gracefully
- [ ] Write 5 unit tests
- [ ] Benchmark: <5s for 10K files

**Success Criteria:**
- Single recursive pass
- No file visited twice
- Builds complete tree
- Performance ≥ v1

---

#### P1.2: Root Detector (Week 1, Days 3-4)
- [ ] Create `src/core_v2/root_detector.py`
- [ ] Implement `RootDetector.detect(tree: FileNode) -> Dict[Path, RootInfo]`
- [ ] Add PROJECT detection markers
- [ ] Add MEDIA detection markers
- [ ] Add ARCHIVE detection markers
- [ ] Write 10 unit tests
- [ ] Test against real folders:
  - `D:\Python Scripts\` (should detect as PROJECT)
  - `D:\VirtualBox VMs\` (should detect as BACKUP)
  - `D:\Steam Games - Hack\` (should detect as GAME)

**Success Criteria:**
- Correctly identifies `D:\Python Scripts\` as protected
- Never moves files out of detected roots
- No false positives (Documents/ not flagged as PROJECT)

---

#### P1.3: Rule Engine v2 (Week 2, Days 1-3)
- [ ] Create `src/core_v2/rule_engine.py`
- [ ] Implement `RuleEngine.classify(node: FileNode) -> RuleResult`
- [ ] Add confidence scoring (0.0-1.0)
- [ ] Add context hint extraction
- [ ] Test against 1000 files
- [ ] Verify missing extensions work (`.md`, `.log`, `.sh`, `.ps1`)

**Success Criteria:**
- 95%+ classification accuracy
- All common extensions covered
- Confidence scores meaningful

---

#### P1.4: Placement Resolver (Week 3, Days 1-4)
- [ ] Create `src/core_v2/placement_resolver.py`
- [ ] Implement `PlacementResolver.resolve(rules, ai, config) -> List[PlacementDecision]`
- [ ] Add redundancy detection:
  - Prevent `MP3 Collection/MP3/`
  - Prevent `ZIP Collection/ZIP/`
- [ ] Add min group size enforcement (≥3 files)
- [ ] Add conflict handling (rename, skip)
- [ ] Write 15 unit tests

**Success Criteria:**
- NO redundant nesting
- NO folders for <3 files (unless rule match)
- All conflicts resolved safely

---

### PRIORITY 2 (Should Have - Quality Improvements)

#### P2.1: Context Builder (Week 2, Days 4-5)
- [ ] Create `src/core_v2/context_builder.py`
- [ ] Extract parent folder names
- [ ] Extract sibling patterns
- [ ] Extract date patterns
- [ ] Build context strings for AI

**Success Criteria:**
- Context improves AI accuracy by 10%+

---

#### P2.2: AI Grouper v2 (Week 3, Days 1-2)
- [ ] Modify `src/ai/classifier.py` to accept context
- [ ] Enforce min_group_size=3
- [ ] Improve group naming with context
- [ ] Compare v1 vs v2 results

**Success Criteria:**
- AI only creates groups with ≥3 files
- Group names more meaningful

---

#### P2.3: Preview Builder v2 (Week 4, Days 1-2)
- [ ] Create `src/core_v2/preview_builder.py`
- [ ] Build tree-style preview
- [ ] Add statistics
- [ ] Add audit trail (reason for each decision)
- [ ] GUI integration

**Success Criteria:**
- User can see why each decision was made
- Preview is accurate (matches actual results)

---

### PRIORITY 3 (Nice to Have - Polish)

#### P3.1: Performance Optimization (Week 5)
- [ ] Profile v2 vs v1
- [ ] Optimize hot paths
- [ ] Add caching where beneficial
- [ ] Target: <30s for 10K files

---

#### P3.2: Enhanced Logging (Week 5)
- [ ] Add detailed decision logging
- [ ] Add debug mode for troubleshooting
- [ ] Add performance metrics

---

#### P3.3: Configuration Options (Week 5)
- [ ] Add `v2.min_group_size` config
- [ ] Add `v2.root_protection` toggle
- [ ] Add `v2.prevent_redundant_nesting` toggle

---

## Test Scenarios (Integration Tests)

### Test 1: Project Root Protection
```
Input:
  D:\Python Scripts\
    AutoFolder AI\
      .git/
      src/
        main.py
        data.csv
    random_file.py

Expected:
  - AutoFolder AI/ NOT reorganized (protected)
  - random_file.py → D:\Code\PY\
```

---

### Test 2: Redundancy Prevention
```
Input:
  D:\test\
    song1.mp3
    song2.mp3
    song3.mp3

v1 Output (BAD):
  D:\Audio\
    MP3 Collection\
      MP3\
        song1.mp3
        song2.mp3
        song3.mp3

v2 Output (GOOD):
  D:\Audio\
    MP3\
      song1.mp3
      song2.mp3
      song3.mp3
```

---

### Test 3: Min Group Size
``` - QUALITY FOCUSED

### Week 1-2: Foundation & Models
- Perfect data structures
- Immutable, type-safe, validated
- Deep scanner with error handling
- Property-based testing
- 100% test coverage on models

### Week 3: Root Detection
- Research ALL project markers
- Confidence scoring
- Test against 50+ real projects
- Zero false positives/negatives

### Week 4: Rule Engine v2 & Context
- Enhanced rule matching
- Context extraction
- Missing extensions covered
- Confidence scoring

### Week 5-6: Placement Resolver ⭐ CRITICAL
- Implement 5 anti-redundancy rules
- Minimum group size (≥5)
- Depth limits
- Sibling analysis
- Context collapse
- Test against v1.0 D:\ output
- Visual diff tool

### Week 7: AI Grouper v2
- Context-aware grouping
- Better group naming
- Semantic duplicate detection

### Week 8: Preview Builder v2
- Tree visualization
- Audit trail
- Statistics
- GUI integration

### Week 9-10: Testing & Validation
- Unit tests (200+)
- Integration tests (24 scenarios)
- Real-world testing (D:\ drive)
- Stress testing (100K files)
- Edge case testing
- Performance tuning

### Week 11: Side-by-Side Comparison
- Run v1 and v2 on same data
- Visual diff reports
- Fix any regressions
- Performance optimization

### Week 12: Polish & Release
- Documentation
- Migration guide
- Enable v2 by default
- Keep v1 as fallback

**Total Timeline: 12 weeks (3 months)**
**Why longer:** Quality over speed. Zero compromises.2.dat
    IMG003.dat

v2 Output:
  D:\Images\
    vacation_photos_2024\  (preserved structure)
      IMG001.dat
      IMG002.dat
      IMG003.dat
```

---

## Safety Invariants (Must Pass All)

### Hard Constraints
1. ✅ No file moved out of detected PROJECT roots
2. ✅ No overwrites without rename
3. ✅ No folder created for <3 files (unless explicit rule match)
4. ✅ No redundant nesting (e.g., `MP3 Collection/MP3/`)
5. ✅ All moves logged for undo

### Soft Constraints
1. ⚠️ Performance <30s for 10K files
2. ⚠️ AI accuracy improvement >10% vs v1
3. ⚠️ Preview accuracy 100% (matches actual results)

---

## Implementation Order (By Week)

### Week 1: Foundation
- Days 1-2: Deep Scanner
- Days 3-4: Root Detector
- Day 5: Integration tests

### Week 2: Rules & Context
- Days 1-3: Rule Engine v2
- Days 4-5: Context Builder

### Week 3: AI & Placement
- Days 1-2: AI Grouper v2
- Days 3-5: Placement Resolver

### Week 4: Preview & Polish
- Days 1-2: Preview Builder v2
- Days 3-5: GUI integration

### Week 5: Testing
- Days 1-2: Unit tests
- Days 3-4: Integration tests
- Day 5: Real-world tests

### Week 6: Side-by-Side
- Compare v1 vs v2 on same data
- Fix any regressi - 100% IMPROVEMENT TARGET

### Hard Requirements (Must Achieve ALL)
- ✅ ZERO redundant nesting (e.g., no `MP3 Collection/MP3/`)
- ✅ ZERO folders for <5 files (unless explicit rule)
- ✅ ZERO files moved out of protected roots
- ✅ 100% test pass rate (200+ tests)
- ✅ All 24 integration tests pass
- ✅ D:\ drive: When re-organized with v2, output is FLAT and logical

### Comparison Test (v1 vs v2 on D:\ drive)
Before v2 (v1 output):
```
D:\Audio\
  MP3 Collection\
    MP3\
  WAV Collection\
    WAV\
D:\Documents\
  Alias\TXT\
  Backup\TXT\
  Config\TXT\
  (50+ tiny folders)
```

After v2 (REQUIRED output):
```
D:\Audio\
  MP3\
    (all .mp3 files)
  WAV\
    (all .wav files)
D:\Documents\
  (files directly, organized by type)
  PDF\
  TXT\
  DOCX\
```

**Improvement Metrics:**
- Folder count reduced by 60%+
- Average nesting depth reduced from 4 to 2
- Files in correct category: 100%
- User undo rate: <5% (vs v1's ~30%)

### Quality Gates (Cannot Release Without)
- ⭐ Zero data loss in 1000 test runs
- ⭐ Undo success rate: 100%
- ⭐ No crashes on 100K file folders
- ⭐ Protected roots: 100% accuracy
- ⭐ User acceptance: "This is WAY better than v1"

### Performance Targets (Acceptable Ranges)
- 10K files: <60s (v1 baseline: ~45s) - 30% slower acceptable for better results
- 100K files: <10 min
- Memory: <2GB for 100K files
- No memory leak     # Deep scanner
    root_detector.py       # Root protection
    rule_engine.py         # Rule-first classification
    context_builder.py     # Context extraction
    ai_grouper.py          # Wrapper for AI classifier
    placement_resolver.py  # Smart decision making
    preview_builder.py     # User-facing preview
    organizer_v2.py        # Main orchestrator
  
  core/
    organizer.py           # v1 (keep as fallback)
    ...
```

---

## Feature Flag Strategy

Add to `config/default_config.yaml`:

```yaml
engine:
  version: "v2"  # v1 or v2
  fallback_to_v1: true  # If v2 fails, use v1
```

In `src/main.py`:

```python
if config['engine']['version'] == 'v2':
    from core_v2.organizer_v2 import OrganizerV2
    organizer = OrganizerV2(config)
else:
    from core.organizer import Organizer
    organizer = Organizer(config)
```

---

## Success Metrics

### Must Achieve
- ✅ No redundant nesting in test runs
- ✅ Project roots protected (0 false moves)
- ✅ Min group size enforced (100% compliance)
- ✅ All 4 integration tests pass
- ✅ D:\ drive organizes correctly (run again, compare)

### Should Achieve
- ⭐ Performance ≥ v1 (±10% acceptable)
- ⭐ User satisfaction: "v2 is better"
- ⭐ Fewer undo operations needed

### Nice to Have
- 🎯 AI accuracy +20% vs v1
- 🎯 Zero conflicts in normal use
- 🎯 <20s for 10K files

---

## Risk ManagAnswered (User Priority: Quality Over Speed)

1. **Performance Target:** 30% slower is ACCEPTABLE if results are perfect. Quality > Speed.
2. **Timeline:** 12 weeks is fine. Take time to get it right.
3. **AI Model:** Keep current model, focus on better usage (context).
4. **GUI Changes:** Minimal - focus on engine quality first.
5. **Backward Compatibility:** Yes - support v1 undo journals for transition.
6. **Config Migration:** Yes - auto-migrate v1 configs.
7. **Min Group Size:** Increased to 5 (from 3) for better results.
8. **Testing:** Extensive - 200+ tests, real-world data, stress tests.

**Philosophy:** Ship v2.0 when it's PERFECT, not when it's fast.
2. **Breaking existing workflows**
   - Mitigation: Side-by-side testing, gradual rollout
   - Fallback: Feature flag to v1

3. **New bugs introduced**
   - Mitigation: Extensive testing, staged rollout
   - Fallback: Undo system already exists

### Medium Risk
1. **AI changes break grouping**
   - Mitigation: Context should improve, not break
   - Fallback: Disable context if worse

2. **Root detection false positives**
   - Mitigation: Conservative rules, user override
   - Fallback: Disable root protection if needed

### Low Risk
1. **User confusion with changes**
   - Mitigation: Clear documentation, changelog
   - Fallback: Tutorial mode

---

## Go/No-Go Decision Points

### After Week 2 (Foundation + Rules)
**Go if:**
- Deep scanner works
- Root detector accurate
- Rule engine matches v1 accuracy

**No-Go if:**
- Performance <50% of v1
- Critical bugs found

---

### After Week 4 (AI + Placement)
**Go if:**
- Placement resolver prevents redundancy
- Min group size enforced
- Integration tests pass

**No-Go if:**
- Redundant nesting still occurs
- Major regressions vs v1

---

### After Week 6 (Side-by-Side)
**Go if:**
- v2 output clearly better than v1
- No critical bugs
- Performance acceptable

**No-Go if:**
- v2 output worse than v1
- Too many bugs
- Performance unacceptable

---

## Next Immediate Actions

### 1. Create Directory Structure
```powershell
cd "C:\Users\Praveen\Downloads\Python Scripts\AutoFolder AI"
mkdir src\core_v2
New-Item src\core_v2\__init__.py
New-Item src\core_v2\models.py
New-Item src\core_v2\scanner.py
```

### 2. Start with Models
Create all data classes in `models.py`:
- FileNode
- RootInfo
- RuleResult
- AIResult
- PlacementDecision
- PreviewResult

### 3. Implement Deep Scanner
Build the foundation - everything depends on this.

---

## Questions to Answer Before Starting

1. **Performance Target:** What's acceptable for 10K files? (v1 baseline?)
2. **AI Model:** Keep same model or upgrade?
3. **GUI Changes:** Minimal or redesign?
4. **Backward Compatibility:** Support v1 undo journals?
5. **Config Migration:** Auto-migrate v1 configs?

---

## Approval Checklist

Before starting implementation:

- [ ] User approves this plan
- [ ] Timeline is realistic (7 weeks)
- [ ] Priorities are correct (P1 → P2 → P3)
- [ ] Test scenarios cover real issues
- [ ] Success metrics are measurable
- [ ] Fallback strategy is acceptable

---

**Ready to start?** We'll begin with Week 1: Foundation (Deep Scanner + Root Detector).
