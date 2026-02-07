"""
AutoFolder AI v2.0 - Core Data Models

Immutable data structures for the organization pipeline.
All models are frozen dataclasses to prevent bugs from mutation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum
from datetime import datetime
import hashlib


class RootType(Enum):
    """Types of protected roots."""
    PROJECT = "project"        # Development projects
    MEDIA = "media"            # Camera/photo collections
    ARCHIVE = "archive"        # Backup archives
    BACKUP = "backup"          # System backups
    GAME = "game"              # Game installations
    VM = "vm"                  # Virtual machines
    UNKNOWN = "unknown"


class DecisionSource(Enum):
    """Source of placement decision."""
    RULE = "rule"              # Extension/content rule
    AI = "ai"                  # AI semantic grouping
    CONTEXT = "context"        # Folder context
    SKIP = "skip"              # Explicitly skipped
    PROTECTED = "protected"    # Protected root


@dataclass(frozen=True)
class FileNode:
    """
    Immutable representation of a file or folder in the filesystem tree.
    
    Built by DeepScanner in a single recursive pass.
    """
    path: Path
    is_dir: bool
    size: int
    mtime: float
    parent: Optional['FileNode'] = None
    children: Tuple['FileNode', ...] = field(default_factory=tuple)
    depth: int = 0                    # Depth from scan root
    root_distance: int = 0            # Hops from detected root boundary
    
    def __post_init__(self):
        """Validate node data."""
        if self.size < 0:
            raise ValueError(f"Size cannot be negative: {self.size}")
        if self.mtime < 0:
            raise ValueError(f"Modification time cannot be negative: {self.mtime}")
        if self.depth < 0:
            raise ValueError(f"Depth cannot be negative: {self.depth}")
    
    @property
    def name(self) -> str:
        """File/folder name."""
        return self.path.name
    
    @property
    def extension(self) -> str:
        """File extension (lowercase, with dot)."""
        return self.path.suffix.lower()
    
    @property
    def is_file(self) -> bool:
        """Is this a file (not directory)?"""
        return not self.is_dir
    
    def iter_files(self) -> List['FileNode']:
        """Recursively iterate all file nodes."""
        files = []
        if self.is_file:
            files.append(self)
        else:
            for child in self.children:
                files.extend(child.iter_files())
        return files
    
    def iter_dirs(self) -> List['FileNode']:
        """Recursively iterate all directory nodes."""
        dirs = []
        if self.is_dir:
            dirs.append(self)
            for child in self.children:
                dirs.extend(child.iter_dirs())
        return dirs
    
    def __hash__(self):
        """Hash based on path for set/dict usage."""
        return hash(self.path)
    
    def __repr__(self):
        """Human-readable representation."""
        type_str = "DIR" if self.is_dir else "FILE"
        return f"<FileNode {type_str} {self.path.name} depth={self.depth}>"


@dataclass(frozen=True)
class RootInfo:
    """
    Information about a detected protected root.
    
    Protected roots are never reorganized internally.
    Examples: project folders, game installations, VM disks.
    """
    path: Path
    root_type: RootType
    confidence: float            # 0.0-1.0
    markers: Tuple[str, ...]     # Files/folders that triggered detection
    protect: bool = True         # Never reorganize inside
    
    def __post_init__(self):
        """Validate root info."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0: {self.confidence}")
        if not self.path.is_absolute():
            raise ValueError(f"Path must be absolute: {self.path}")
    
    def __repr__(self):
        """Human-readable representation."""
        return f"<RootInfo {self.root_type.value} {self.path.name} conf={self.confidence:.2f}>"


@dataclass(frozen=True)
class RuleResult:
    """
    Result of rule-based classification.
    
    Rules match by extension, magic bytes, or content analysis.
    """
    file: FileNode
    category: str                    # e.g., "Documents", "Images", "Code"
    subcategory: Optional[str]       # e.g., "PDF", "Python", "JPG"
    confidence: float                # 0.0-1.0
    matched_rule: str                # Rule that matched (for audit)
    context_hint: Optional[str] = None  # Folder context for AI
    
    def __post_init__(self):
        """Validate rule result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0: {self.confidence}")
        if not self.category:
            raise ValueError("Category cannot be empty")
    
    @property
    def is_high_confidence(self) -> bool:
        """Is this a high-confidence rule match?"""
        return self.confidence >= 0.8
    
    def __repr__(self):
        """Human-readable representation."""
        return f"<RuleResult {self.file.name} → {self.category}/{self.subcategory or 'N/A'} conf={self.confidence:.2f}>"


@dataclass(frozen=True)
class AIResult:
    """
    Result of AI semantic grouping.
    
    AI groups uncategorized files by semantic similarity.
    """
    file: FileNode
    group: str                       # Human-readable group name
    confidence: float                # 0.0-1.0
    similar_files: Tuple[FileNode, ...]  # Files in same group
    embedding: Optional[Tuple[float, ...]] = None  # Optional: store embedding
    context_used: str = ""           # Context string used for grouping
    
    def __post_init__(self):
        """Validate AI result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0: {self.confidence}")
        if len(self.similar_files) < 2:
            raise ValueError(f"AI groups must have ≥2 files: {len(self.similar_files)}")
        if not self.group:
            raise ValueError("Group name cannot be empty")
    
    @property
    def group_size(self) -> int:
        """Number of files in this group."""
        return len(self.similar_files)
    
    @property
    def is_large_group(self) -> bool:
        """Is this a large group (≥5 files)?"""
        return self.group_size >= 5
    
    def __repr__(self):
        """Human-readable representation."""
        return f"<AIResult {self.file.name} → {self.group} ({self.group_size} files) conf={self.confidence:.2f}>"


@dataclass(frozen=True)
class PlacementDecision:
    """
    Final decision about where to move a file.
    
    Includes full reasoning trail for audit/undo.
    """
    file: FileNode
    target: Path                     # Where to move
    reason: str                      # Human-readable explanation
    source: DecisionSource           # How decision was made
    conflicts: Tuple[str, ...] = field(default_factory=tuple)
    safe: bool = True                # Passes all safety checks
    
    # Optional: store original results for debugging
    rule_result: Optional[RuleResult] = None
    ai_result: Optional[AIResult] = None
    
    def __post_init__(self):
        """Validate placement decision."""
        if not self.target.is_absolute():
            raise ValueError(f"Target must be absolute path: {self.target}")
        if not self.reason:
            raise ValueError("Reason cannot be empty")
    
    @property
    def will_move(self) -> bool:
        """Will this file actually be moved?"""
        return self.target != self.file.path and self.safe
    
    @property
    def has_conflicts(self) -> bool:
        """Are there any conflicts?"""
        return len(self.conflicts) > 0
    
    def __repr__(self):
        """Human-readable representation."""
        action = "MOVE" if self.will_move else "SKIP"
        return f"<PlacementDecision {action} {self.file.name} → {self.target.name} via {self.source.value}>"


@dataclass
class PreviewResult:
    """
    User-facing preview of what will happen.
    
    Mutable because we build it incrementally.
    """
    total_files: int
    will_move: int
    will_skip: int
    conflicts: List[PlacementDecision] = field(default_factory=list)
    tree_preview: Dict[str, Any] = field(default_factory=dict)
    decisions: List[PlacementDecision] = field(default_factory=list)
    
    # Statistics
    by_category: Dict[str, int] = field(default_factory=dict)
    by_source: Dict[str, int] = field(default_factory=dict)
    protected_roots: List[RootInfo] = field(default_factory=list)
    
    # Performance metrics
    scan_time: float = 0.0
    classify_time: float = 0.0
    ai_time: float = 0.0
    resolve_time: float = 0.0
    
    def __post_init__(self):
        """Validate preview result."""
        if self.total_files < 0:
            raise ValueError(f"Total files cannot be negative: {self.total_files}")
        if self.will_move < 0:
            raise ValueError(f"Will move cannot be negative: {self.will_move}")
        if self.will_skip < 0:
            raise ValueError(f"Will skip cannot be negative: {self.will_skip}")
    
    @property
    def total_time(self) -> float:
        """Total processing time."""
        return self.scan_time + self.classify_time + self.ai_time + self.resolve_time
    
    @property
    def conflict_count(self) -> int:
        """Number of conflicts."""
        return len(self.conflicts)
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Total files: {self.total_files}",
            f"Will move: {self.will_move}",
            f"Will skip: {self.will_skip}",
            f"Conflicts: {self.conflict_count}",
            f"Protected roots: {len(self.protected_roots)}",
            f"Total time: {self.total_time:.2f}s"
        ]
        return "\n".join(lines)
    
    def __repr__(self):
        """Human-readable representation."""
        return f"<PreviewResult {self.will_move}/{self.total_files} files to move, {self.conflict_count} conflicts>"


# Validation helpers

def validate_path_safe(path: Path) -> bool:
    """Check if path is safe to operate on."""
    # No path length issues (Windows limit)
    if len(str(path)) > 260:
        return False
    
    # No invalid characters
    invalid_chars = '<>:"|?*'
    if any(char in str(path) for char in invalid_chars):
        return False
    
    # Not a system path
    system_paths = [
        Path("C:/Windows"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
    ]
    try:
        for sys_path in system_paths:
            path.relative_to(sys_path)
            return False  # Path is under system folder
    except ValueError:
        pass  # Not under system folder, good
    
    return True


def calculate_file_hash(path: Path, algorithm: str = "sha256") -> Optional[str]:
    """Calculate hash of file (for duplicate detection)."""
    try:
        hasher = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None
