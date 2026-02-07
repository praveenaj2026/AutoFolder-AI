"""
AutoFolder AI v2.0 - Root Detector

Detects protected roots (PROJECT, MEDIA, ARCHIVE, BACKUP, GAME, VM)
with confidence scores. Prevents organizing files out of these roots.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass

from .models import RootInfo, RootType, FileNode

logger = logging.getLogger(__name__)


@dataclass
class RootMarker:
    """Marker that indicates a specific root type."""
    pattern: str          # File/folder name or pattern
    root_type: RootType   # Type of root this indicates
    weight: float         # How strong this marker is (0.0-1.0)
    must_be_file: bool = False      # Must be a file (not folder)
    must_be_folder: bool = False    # Must be a folder (not file)
    is_extension: bool = False      # Match as file extension (e.g., .vbox)


# Root detection markers
# Higher weight = stronger indicator
ROOT_MARKERS = [
    # Project markers
    RootMarker(".git", RootType.PROJECT, 1.0, must_be_folder=True),
    RootMarker(".gitignore", RootType.PROJECT, 0.8, must_be_file=True),
    RootMarker("pyproject.toml", RootType.PROJECT, 0.9, must_be_file=True),
    RootMarker("package.json", RootType.PROJECT, 0.9, must_be_file=True),
    RootMarker("Cargo.toml", RootType.PROJECT, 0.9, must_be_file=True),
    RootMarker("pom.xml", RootType.PROJECT, 0.9, must_be_file=True),
    RootMarker("build.gradle", RootType.PROJECT, 0.8, must_be_file=True),
    RootMarker(".vscode", RootType.PROJECT, 0.6, must_be_folder=True),
    RootMarker(".idea", RootType.PROJECT, 0.6, must_be_folder=True),
    RootMarker("CMakeLists.txt", RootType.PROJECT, 0.8, must_be_file=True),
    RootMarker("Makefile", RootType.PROJECT, 0.7, must_be_file=True),
    RootMarker("requirements.txt", RootType.PROJECT, 0.7, must_be_file=True),
    RootMarker("setup.py", RootType.PROJECT, 0.8, must_be_file=True),
    RootMarker("composer.json", RootType.PROJECT, 0.8, must_be_file=True),
    RootMarker(".env", RootType.PROJECT, 0.5, must_be_file=True),
    RootMarker("src", RootType.PROJECT, 0.4, must_be_folder=True),
    RootMarker("node_modules", RootType.PROJECT, 0.6, must_be_folder=True),
    
    # Media collection markers
    RootMarker("iTunes", RootType.MEDIA, 0.7, must_be_folder=True),
    RootMarker("Music", RootType.MEDIA, 0.5, must_be_folder=True),
    RootMarker("Videos", RootType.MEDIA, 0.5, must_be_folder=True),
    RootMarker("Photos", RootType.MEDIA, 0.5, must_be_folder=True),
    RootMarker("Pictures", RootType.MEDIA, 0.5, must_be_folder=True),
    RootMarker("Movies", RootType.MEDIA, 0.5, must_be_folder=True),
    RootMarker(".nomedia", RootType.MEDIA, 0.6, must_be_file=True),
    
    # Archive markers
    RootMarker("Archives", RootType.ARCHIVE, 0.6, must_be_folder=True),
    RootMarker("Old Files", RootType.ARCHIVE, 0.5, must_be_folder=True),
    RootMarker("Archive", RootType.ARCHIVE, 0.6, must_be_folder=True),
    
    # Backup markers
    RootMarker("Backups", RootType.BACKUP, 0.7, must_be_folder=True),
    RootMarker("Backup", RootType.BACKUP, 0.7, must_be_folder=True),
    RootMarker(".backup", RootType.BACKUP, 0.6, must_be_folder=True),
    RootMarker("backup.log", RootType.BACKUP, 0.5, must_be_file=True),
    
    # Game installation markers
    RootMarker("steamapps", RootType.GAME, 0.9, must_be_folder=True),
    RootMarker("Steam", RootType.GAME, 0.7, must_be_folder=True),
    RootMarker("Games", RootType.GAME, 0.6, must_be_folder=True),
    RootMarker("game.exe", RootType.GAME, 0.5, must_be_file=True),
    RootMarker("launcher.exe", RootType.GAME, 0.4, must_be_file=True),
    
    # Virtual Machine markers
    RootMarker(".vbox", RootType.VM, 0.9, must_be_file=True, is_extension=True),
    RootMarker(".vmx", RootType.VM, 0.9, must_be_file=True, is_extension=True),
    RootMarker(".vdi", RootType.VM, 0.8, must_be_file=True, is_extension=True),
    RootMarker(".vmdk", RootType.VM, 0.8, must_be_file=True, is_extension=True),
    RootMarker("VirtualBox VMs", RootType.VM, 0.9, must_be_folder=True),
    RootMarker("VMware", RootType.VM, 0.8, must_be_folder=True),
]


class RootDetector:
    """
    Detects protected roots in directory tree.
    
    Uses marker-based heuristics with confidence scoring.
    """
    
    def __init__(self, min_confidence: float = 0.7):
        """
        Initialize root detector.
        
        Args:
            min_confidence: Minimum confidence to consider a root (0.7 = 70%)
        """
        self.min_confidence = min_confidence
        self._detected_roots: List[RootInfo] = []
    
    def detect_roots(self, tree: FileNode) -> List[RootInfo]:
        """
        Detect all protected roots in tree.
        
        Args:
            tree: FileNode tree from scanner
            
        Returns:
            List of detected roots with confidence scores
        """
        logger.info(f"Starting root detection from: {tree.path}")
        self._detected_roots = []
        
        # Recursively check each directory
        self._detect_recursive(tree)
        
        # Sort by confidence (highest first)
        self._detected_roots.sort(key=lambda r: r.confidence, reverse=True)
        
        logger.info(f"Detected {len(self._detected_roots)} protected roots")
        for root in self._detected_roots:
            logger.info(f"  {root.root_type.value}: {root.path} (confidence={root.confidence:.2f})")
        
        return self._detected_roots
    
    def _detect_recursive(self, node: FileNode):
        """Recursively detect roots in tree."""
        if not node.is_dir:
            return
        
        # Check if this directory is a root
        root_info = self._check_directory(node)
        if root_info and root_info.confidence >= self.min_confidence:
            self._detected_roots.append(root_info)
            logger.debug(f"Found {root_info.root_type.value} root: {node.path} (conf={root_info.confidence:.2f})")
            # Don't recurse into detected roots (they protect their children)
            return
        
        # Recurse into child directories only (not node itself)
        for child in node.children:
            if child.is_dir:
                self._detect_recursive(child)
    
    def _check_directory(self, node: FileNode) -> Optional[RootInfo]:
        """
        Check if directory is a protected root.
        
        Args:
            node: Directory to check
            
        Returns:
            RootInfo if root detected, None otherwise
        """
        # Collect child names for matching
        child_names = {child.name.lower() for child in node.children}
        
        # Score each root type
        type_scores: dict[RootType, float] = {}
        type_markers: dict[RootType, List[str]] = {}
        
        for marker in ROOT_MARKERS:
            pattern_lower = marker.pattern.lower()
            
            # Check if marker exists in children
            matched = False
            
            if marker.is_extension:
                # Match by file extension
                matched = any(
                    child.is_file and child.path.suffix.lower() == pattern_lower
                    for child in node.children
                )
            elif marker.must_be_file:
                # Must be a file
                matched = any(
                    child.name.lower() == pattern_lower and child.is_file
                    for child in node.children
                )
            elif marker.must_be_folder:
                # Must be a folder
                matched = any(
                    child.name.lower() == pattern_lower and child.is_dir
                    for child in node.children
                )
            else:
                # Can be either
                matched = pattern_lower in child_names
            
            if matched:
                # Add to score
                if marker.root_type not in type_scores:
                    type_scores[marker.root_type] = 0.0
                    type_markers[marker.root_type] = []
                
                type_scores[marker.root_type] += marker.weight
                type_markers[marker.root_type].append(marker.pattern)
        
        # Find best match
        if not type_scores:
            return None
        
        best_type = max(type_scores.keys(), key=lambda t: type_scores[t])
        raw_score = type_scores[best_type]
        
        # Normalize confidence to 0-1 range
        # Multiple strong markers can push confidence > 1, so cap it
        confidence = min(raw_score, 1.0)
        
        # Only return if meets minimum confidence
        if confidence < self.min_confidence:
            return None
        
        return RootInfo(
            path=node.path,
            root_type=best_type,
            confidence=confidence,
            markers=tuple(type_markers[best_type]),
            protect=True  # Always protect detected roots
        )
    
    def is_protected(self, path: Path) -> bool:
        """
        Check if path is within a protected root.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is protected
        """
        for root in self._detected_roots:
            try:
                path.relative_to(root.path)
                return True
            except ValueError:
                continue
        return False
    
    def get_root_for_path(self, path: Path) -> Optional[RootInfo]:
        """
        Get the root info for a path (if protected).
        
        Args:
            path: Path to check
            
        Returns:
            RootInfo if path is in a protected root, None otherwise
        """
        for root in self._detected_roots:
            try:
                path.relative_to(root.path)
                return root
            except ValueError:
                continue
        return None
    
    @property
    def detected_roots(self) -> List[RootInfo]:
        """Get list of detected roots."""
        return self._detected_roots.copy()


def detect_protected_roots(
    tree: FileNode,
    min_confidence: float = 0.7
) -> List[RootInfo]:
    """
    Convenience function to detect protected roots.
    
    Args:
        tree: FileNode tree from scanner
        min_confidence: Minimum confidence threshold (default 0.7)
        
    Returns:
        List of detected protected roots
    """
    detector = RootDetector(min_confidence=min_confidence)
    return detector.detect_roots(tree)
