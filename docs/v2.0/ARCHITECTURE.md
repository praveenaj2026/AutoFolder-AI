# AutoFolder AI v2.0 — Core Architecture Design

**Status:** Planning Phase (Pre-Implementation)  
**Target Release:** After v1.0 validation complete  
**Author:** GitHub Copilot + Praveen  
**Date:** January 26, 2026

---

## Executive Summary

This document defines the v2.0 organizer core architecture addressing 7 critical issues identified in v1.0:

1. **Shallow scanning** → Unified Deep Scan
2. **No root protection** → Root Detection System
3. **Context-blind AI** → Context-Aware AI Input
4. **Wrong pipeline order** → Rule-First Pipeline
5. **Aggressive folder creation** → Smart Placement Resolver
6. **Tree flattening** → Root Boundary Protection
7. **Missed folders** → Single-Pass Deep Traversal

**Design Principles:**
- Immutability of scan data
- Safety invariants enforced at every stage
- Deterministic behavior (same input → same output)
- Full auditability (every decision logged)
- Testable pipeline stages

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORGANIZER PIPELINE v2.0                   │
└─────────────────────────────────────────────────────────────┘

Input: root_path
   ↓
┌──────────────────────┐
│  1. Deep Scanner     │  → FileNode tree (immutable)
└──────────────────────┘
   ↓
┌──────────────────────┐
│  2. Root Detector    │  → RootInfo tags (PROJECT, MEDIA, etc.)
└──────────────────────┘
   ↓
┌──────────────────────┐
│  3. Rule Engine      │  → RuleResult per file
└──────────────────────┘
   ↓
┌──────────────────────┐
│  4. Context Builder  │  → Inherits folder context
└──────────────────────┘
   ↓
┌──────────────────────┐
│  5. AI Grouper       │  → AIResult for uncategorized
└──────────────────────┘
   ↓
┌──────────────────────┐
│  6. Placement Solver │  → PlacementDecision per file
└──────────────────────┘
   ↓
┌──────────────────────┐
│  7. Preview Builder  │  → User-visible preview
└──────────────────────┘
   ↓
Output: PreviewResult (moves, stats, conflicts)
```

---

## Core Data Models

### 1. FileNode (Immutable)
```python
@dataclass(frozen=True)
class FileNode:
    """Single file/folder in filesystem tree"""
    path: Path
    is_dir: bool
    size: int
    mtime: float
    parent: Optional['FileNode']
    children: tuple['FileNode', ...]  # Empty for files
    depth: int
    root_distance: int  # Hops from scan root
```

### 2. RootInfo
```python
@dataclass
class RootInfo:
    """Root boundary detection result"""
    path: Path
    root_type: RootType  # PROJECT, MEDIA, ARCHIVE, BACKUP, GAME
    confidence: float
    markers: list[str]  # Files/folders that triggered detection
    protect: bool  # Never reorganize inside
```

**Root Detection Heuristics:**

| Type | Markers | Behavior |
|------|---------|----------|
| PROJECT | `.git/`, `package.json`, `requirements.txt`, `.sln` | Protect entire subtree |
| MEDIA | `DCIM/`, `.nomedia`, Camera folder patterns | Preserve structure |
| ARCHIVE | `.zip`, `.7z`, `.rar` with timestamps | Group but don't unpack |
| BACKUP | Time-stamped folders, system backup markers | Preserve |
| GAME | Save files, game executables, mod folders | Protect |

### 3. RuleResult
```python
@dataclass
class RuleResult:
    """Rule engine classification"""
    file: FileNode
    category: str  # Documents, Images, Code, etc.
    subcategory: Optional[str]  # PDF, Python, JPG, etc.
    confidence: float
    matched_rule: str  # Extension, magic bytes, content
    context_hint: Optional[str]  # From parent folder
```

### 4. AIResult
```python
@dataclass
class AIResult:
    """AI semantic grouping"""
    file: FileNode
    group: str  # "Project Proposals", "Family Photos", etc.
    confidence: float
    similar_files: list[FileNode]
    embedding: np.ndarray
    context_used: str  # Folder name + sibling context
```

### 5. PlacementDecision
```python
@dataclass
class PlacementDecision:
    """Final move decision"""
    file: FileNode
    target: Path
    reason: str  # "Rule: extension .py", "AI: Project group"
    source: DecisionSource  # RULE, AI, CONTEXT, SKIP
    conflicts: list[str]
    safe: bool  # Passes all safety checks
```

---

## Pipeline Stages

### Stage 1: Deep Scanner
**Input:** `root_path: Path`  
**Output:** `FileNode` tree

**Algorithm:**
```python
def deep_scan(root: Path) -> FileNode:
    """Single-pass recursive scan building immutable tree"""
    
    # Use os.scandir for speed
    entries = list(os.scandir(root))
    
    children = []
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            child = deep_scan(entry.path)  # Recurse
        else:
            child = FileNode(
                path=entry.path,
                is_dir=False,
                size=entry.stat().st_size,
                mtime=entry.stat().st_mtime,
                parent=None,  # Set after
                children=(),
                depth=0,  # Calculate after
            )
        children.append(child)
    
    return FileNode(
        path=root,
        is_dir=True,
        children=tuple(children),
        ...
    )
```

**Safety Invariants:**
- No file visited twice
- No symlink loops
- No permission crashes (skip + log)

---

### Stage 2: Root Detector
**Input:** `FileNode` tree  
**Output:** `dict[Path, RootInfo]`

**Algorithm:**
```python
def detect_roots(tree: FileNode) -> dict[Path, RootInfo]:
    """Identify protected roots using heuristics"""
    
    roots = {}
    
    def scan(node: FileNode):
        # Check PROJECT markers
        if any(child.path.name in PROJECT_MARKERS for child in node.children):
            roots[node.path] = RootInfo(
                path=node.path,
                root_type=RootType.PROJECT,
                confidence=0.95,
                markers=[...],
                protect=True
            )
            return  # Don't recurse into protected root
        
        # Check other types...
        
        for child in node.children:
            if child.is_dir:
                scan(child)
    
    scan(tree)
    return roots
```

**Root Types:**
- **PROJECT:** `.git`, `node_modules`, `.venv`, `package.json`, `.sln`
- **MEDIA:** `DCIM`, `IMG_*`, `.nomedia`, `Camera`
- **ARCHIVE:** Time-stamped zip/rar collections
- **BACKUP:** Backup software markers
- **GAME:** Save files, game executables

---

### Stage 3: Rule Engine
**Input:** `FileNode` tree, `RootInfo`  
**Output:** `list[RuleResult]`

**Algorithm:**
```python
def classify_by_rules(tree: FileNode, roots: dict) -> list[RuleResult]:
    """Apply extension + content rules"""
    
    results = []
    
    for node in tree.iter_files():
        # Skip if inside protected root
        if is_protected(node.path, roots):
            continue
        
        # Extension match (fast path)
        category = EXTENSION_MAP.get(node.path.suffix.lower())
        
        # Content analysis (slow path)
        if not category:
            category = analyze_content(node.path)
        
        # Context hint from parent folder
        context = extract_context(node.parent.path.name)
        
        results.append(RuleResult(
            file=node,
            category=category,
            context_hint=context,
            ...
        ))
    
    return results
```

**Rule Priority:**
1. Protected root (skip)
2. Extension match (95% of cases)
3. Magic bytes
4. Content analysis
5. Context inheritance

---

### Stage 4: Context Inheritor
**Input:** `list[RuleResult]`  
**Output:** Enhanced `RuleResult` with folder context

**Algorithm:**
```python
def inherit_context(results: list[RuleResult]) -> list[RuleResult]:
    """Add parent folder context to AI input"""
    
    for result in results:
        folder_name = result.file.parent.path.name
        sibling_files = list(result.file.parent.children)
        
        # Extract meaningful context
        context = f"{folder_name} | {len(sibling_files)} files"
        
        result.context_hint = context
    
    return results
```

**Context Sources:**
- Parent folder name
- Sibling file count
- Sibling extensions
- Date patterns in path

---

### Stage 5: AI Grouper
**Input:** `list[RuleResult]` (uncategorized only)  
**Output:** `list[AIResult]`

**Algorithm:**
```python
def ai_group(results: list[RuleResult]) -> list[AIResult]:
    """Semantic grouping for uncategorized files"""
    
    # Filter uncategorized
    uncategorized = [r for r in results if r.category == "Uncategorized"]
    
    if not uncategorized:
        return []
    
    # Build embeddings with context
    texts = []
    for r in uncategorized:
        text = f"{r.file.path.name} | {r.context_hint}"
        texts.append(text)
    
    embeddings = model.encode(texts)
    
    # Cluster
    groups = cluster_embeddings(embeddings, min_group_size=3)
    
    # Build results
    ai_results = []
    for group_id, group_files in groups.items():
        group_name = generate_group_name(group_files)
        
        for file_node in group_files:
            ai_results.append(AIResult(
                file=file_node,
                group=group_name,
                confidence=0.7,
                similar_files=group_files,
                context_used=...
            ))
    
    return ai_results
```

**AI Features:**
- Only runs on uncategorized files
- Uses context (folder name + siblings)
- Min group size = 3 (avoids tiny groups)
- Generates human-readable group names

---

### Stage 6: Placement Resolver
**Input:** `list[RuleResult]`, `list[AIResult]`, config  
**Output:** `list[PlacementDecision]`

**Algorithm:**
```python
def resolve_placements(
    rule_results: list[RuleResult],
    ai_results: list[AIResult],
    config: Config
) -> list[PlacementDecision]:
    """Decide final target path for each file"""
    
    decisions = []
    ai_map = {r.file: r for r in ai_results}
    
    for rule in rule_results:
        # Priority 1: Protected roots (skip)
        if is_protected(rule.file):
            decisions.append(PlacementDecision(
                file=rule.file,
                target=rule.file.path,
                reason="Protected root",
                source=DecisionSource.SKIP,
                safe=True
            ))
            continue
        
        # Priority 2: Rule match
        if rule.confidence > 0.8:
            target = build_target_path(rule, config)
            decisions.append(PlacementDecision(
                file=rule.file,
                target=target,
                reason=f"Rule: {rule.matched_rule}",
                source=DecisionSource.RULE,
                safe=check_safety(rule.file, target)
            ))
            continue
        
        # Priority 3: AI grouping
        if rule.file in ai_map:
            ai = ai_map[rule.file]
            target = build_ai_target(ai, config)
            decisions.append(PlacementDecision(
                file=rule.file,
                target=target,
                reason=f"AI: {ai.group}",
                source=DecisionSource.AI,
                safe=check_safety(rule.file, target)
            ))
            continue
        
        # Priority 4: Keep original location
        decisions.append(PlacementDecision(
            file=rule.file,
            target=rule.file.path,
            reason="No confident match",
            source=DecisionSource.SKIP,
            safe=True
        ))
    
    return decisions
```

**Decision Priority:**
1. Protected roots → SKIP
2. High-confidence rules → MOVE
3. AI groups (≥3 files) → MOVE
4. Low confidence → SKIP

**Safety Checks:**
- No overwrites
- No cross-drive moves (unless configured)
- No breaking project roots
- No circular moves

---

### Stage 7: Preview Builder
**Input:** `list[PlacementDecision]`  
**Output:** `PreviewResult`

**Algorithm:**
```python
def build_preview(decisions: list[PlacementDecision]) -> PreviewResult:
    """Generate user-visible preview with stats"""
    
    moves = [d for d in decisions if d.target != d.file.path]
    skips = [d for d in decisions if d.target == d.file.path]
    conflicts = [d for d in decisions if not d.safe]
    
    # Group by target folder
    by_folder = defaultdict(list)
    for decision in moves:
        folder = decision.target.parent
        by_folder[folder].append(decision)
    
    # Build tree preview
    preview_tree = build_tree_preview(by_folder)
    
    return PreviewResult(
        total_files=len(decisions),
        will_move=len(moves),
        will_skip=len(skips),
        conflicts=conflicts,
        tree_preview=preview_tree,
        decisions=decisions  # Full audit trail
    )
```

---

## Safety Invariants

### Hard Constraints (MUST NEVER VIOLATE)

1. **No Data Loss**
   - Never overwrite existing files
   - Never delete without undo
   - Atomic moves only

2. **Root Protection**
   - Never move files out of detected roots
   - Never break project structures

3. **Permission Safety**
   - Skip files without read permission
   - Skip targets without write permission
   - Never escalate privileges

4. **Path Validity**
   - No path length >260 chars (Windows)
   - No invalid characters
   - No circular references

5. **Undo Guarantee**
   - Every move logged
   - Undo always available
   - Journal never lost

### Soft Constraints (SHOULD FOLLOW)

1. **Min Group Size**
   - AI groups need ≥3 files
   - Avoid creating folders for 1-2 files

2. **Context Preservation**
   - Keep related files together
   - Preserve sibling relationships

3. **User Intent**
   - Prefer explicit rules over AI
   - Respect manual overrides

4. **Performance**
   - Scan completes <30s for 10K files
   - Preview updates <2s

---

## Testing Strategy

### Unit Tests
- Each pipeline stage independently testable
- Mock data structures
- Invariant checks

### Integration Tests

**Test 1: Project Root Protection**
```
Input:
  /home/user/
    project/
      .git/
      src/
        main.py
        data.csv
    random.py

Expected:
  - main.py and data.csv stay in project/
  - random.py moves to Code/
```

**Test 2: Context-Aware AI**
```
Input:
  /Downloads/
    VacationPhotos2024/
      IMG001.dat  (unknown extension)
      IMG002.dat
      IMG003.dat

Expected:
  - Detect "VacationPhotos" context
  - AI groups as "Vacation Images"
  - Stay in same folder (protected context)
```

**Test 3: Min Group Size**
```
Input:
  file1.dat
  file2.dat

Expected:
  - Not enough for AI group (need ≥3)
  - Move to Uncategorized/ or stay put
```

**Test 4: Safety Checks**
```
Input:
  Move file to C:\Program Files\

Expected:
  - Detect permission issue
  - Mark unsafe
  - Show conflict in preview
```

---

## Migration Strategy

### Phase 1: Parallel Development
- Build v2 in `/src/core_v2/`
- Keep v1 running
- Shared UI, separate backend

### Phase 2: Side-by-Side Testing
- Feature flag: `use_v2_engine: false`
- Run both engines on test data
- Compare outputs
- Fix regressions

### Phase 3: Gradual Rollout
- Enable v2 for power users
- Monitor for issues
- Collect real-world feedback

### Phase 4: Full Switchover
- v2 becomes default
- v1 kept as fallback
- Remove v1 after 2 stable releases

---

## Success Criteria

### Must Have
- ✅ No file moves out of project roots
- ✅ AI uses folder context
- ✅ Single deep scan (no multi-pass)
- ✅ Min group size enforced
- ✅ All moves undoable

### Should Have
- ✅ Performance ≥ v1
- ✅ Preview accuracy >95%
- ✅ No regressions in common cases

### Nice to Have
- ✅ Better group names
- ✅ Smarter root detection
- ✅ Configurable safety levels

---

## References

- Original issue document: `AutoFolderAI_Organizer_Issues_and_Fix_Roadmap.txt`
- v1.0 codebase: `/src/core/organizer.py`
- Test scenarios: `/tests/test_organizer.py`

---

**Next Steps:**
1. ✅ Save this document
2. ⏸️ Complete v1.0 validation (EXE testing in VM)
3. ⏸️ Collect real-world usage data
4. ⏸️ Implement v2.0 based on learnings
5. ⏸️ Side-by-side testing
6. ⏸️ Gradual rollout

**Approval Required Before Implementation**
