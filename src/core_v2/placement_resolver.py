"""
AutoFolder AI v2.0 - Placement Resolver

Makes intelligent placement decisions with anti-redundancy rules.
This is the CRITICAL component that implements the quality guarantee.

5 Anti-Redundancy Rules:
1. Collection Folder Prevention - Detect "MP3 Collection/MP3/" patterns
2. Minimum Group Size - Require 5+ files per folder (up from 3)
3. Depth Limit - Maximum 3 levels deep
4. Sibling Analysis - Merge small adjacent folders
5. Context Collapse - Prevent duplicate naming in path
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict

from .models import FileNode, RootInfo, RuleResult, AIResult, PlacementDecision, DecisionSource
from .root_detector import RootDetector
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


@dataclass
class PlacementConfig:
    """Configuration for placement resolver."""
    
    # Anti-redundancy rules
    min_group_size: int = 5  # Minimum files per folder (Rule 2)
    max_depth: int = 3       # Maximum folder depth (Rule 3)
    merge_threshold: int = 3 # Merge folders with ≤ this many files (Rule 4)
    
    # Context awareness
    respect_roots: bool = True  # Don't move files out of protected roots
    prevent_redundancy: bool = True  # Use context builder to prevent redundant nesting
    
    # Decision preferences
    prefer_existing_structure: bool = True  # Keep files in existing folders when possible
    allow_mixed_folders: bool = False  # Allow Documents/mixed/ with PDFs + DOCXs


class PlacementResolver:
    """
    Resolves final file placements with anti-redundancy guarantees.
    
    This is the core component that prevents v1.0's excessive nesting problems.
    """
    
    def __init__(
        self,
        target_root: Path,
        config: Optional[PlacementConfig] = None
    ):
        """
        Initialize placement resolver.
        
        Args:
            target_root: Root directory for organization
            config: Configuration (uses defaults if None)
        """
        self.target_root = target_root
        self.config = config or PlacementConfig()
        
        # Initialize components
        self.root_detector = RootDetector()
        self.context_builder = ContextBuilder()
        
        # Cache for performance
        self._protected_roots: Optional[List[RootInfo]] = None
        self._folder_contexts: Dict[Path, 'FolderContext'] = {}
    
    def resolve_placements(
        self,
        root_node: FileNode,
        rule_results: List[RuleResult],
        ai_results: Optional[List[AIResult]] = None
    ) -> List[PlacementDecision]:
        """
        Resolve placements for all files.
        
        Args:
            root_node: Root of scanned file tree
            rule_results: Classification results from rule engine
            ai_results: Optional AI grouping results
            
        Returns:
            List of placement decisions
        """
        logger.info(f"Resolving placements for {len(rule_results)} files")
        
        # Step 1: Detect protected roots
        if self.config.respect_roots:
            self._protected_roots = self.root_detector.detect_roots(root_node)
            logger.info(f"Found {len(self._protected_roots)} protected roots")
        else:
            self._protected_roots = []
        
        # Step 2: Build initial placement map
        placement_map = self._build_placement_map(rule_results, ai_results)
        
        # Step 3: Apply anti-redundancy rules
        placement_map = self._apply_redundancy_prevention(placement_map, rule_results)
        placement_map = self._apply_minimum_group_size(placement_map)
        placement_map = self._apply_depth_limit(placement_map)
        placement_map = self._apply_sibling_merge(placement_map)
        placement_map = self._apply_context_collapse(placement_map, rule_results)
        
        # Step 4: Convert to placement decisions
        decisions = self._create_decisions(placement_map, rule_results)
        
        # Step 5: Validate decisions
        decisions = self._validate_decisions(decisions)
        
        logger.info(f"Resolved {len(decisions)} placements")
        return decisions
    
    def _build_placement_map(
        self,
        rule_results: List[RuleResult],
        ai_results: Optional[List[AIResult]]
    ) -> Dict[FileNode, Path]:
        """
        Build initial placement map from classifications.
        
        Returns:
            Map of file -> target_path
        """
        placement_map: Dict[FileNode, Path] = {}
        
        for result in rule_results:
            # Check if file is in protected root
            if self._is_in_protected_root(result.file):
                # Don't move files out of protected roots
                placement_map[result.file] = result.file.path
                continue
            
            # Build target path from category/subcategory
            target_path = self._build_target_path(result)
            placement_map[result.file] = target_path
        
        # TODO: Incorporate AI grouping (Week 7)
        # For now, we only use rule-based classifications
        
        return placement_map
    
    def _build_target_path(self, result: RuleResult) -> Path:
        """Build target path from classification result."""
        # Start with target root
        path = self.target_root
        
        # Add category
        path = path / result.category
        
        # Add subcategory if different from category
        if result.subcategory and result.subcategory != result.category:
            path = path / result.subcategory
        
        # Add filename
        path = path / result.file.path.name
        
        return path
    
    def _is_in_protected_root(self, file_node: FileNode) -> bool:
        """Check if file is inside a protected root."""
        if not self._protected_roots:
            return False
        
        for root_info in self._protected_roots:
            # Check if file is inside this root
            try:
                file_node.path.relative_to(root_info.path)
                return True
            except ValueError:
                continue
        
        return False
    
    def _get_root_name(self, file_node: FileNode) -> str:
        """Get the name of the protected root containing this file."""
        if not self._protected_roots:
            return "Unknown"
        
        for root_info in self._protected_roots:
            try:
                file_node.path.relative_to(root_info.path)
                return f"{root_info.path.name} ({root_info.root_type.value})"
            except ValueError:
                continue
        
        return "Unknown"
    
    # =========================================================================
    # Anti-Redundancy Rules
    # =========================================================================
    
    def _apply_redundancy_prevention(
        self,
        placement_map: Dict[FileNode, Path],
        rule_results: List[RuleResult]
    ) -> Dict[FileNode, Path]:
        """
        Rule 1: Collection Folder Prevention
        
        Prevents "MP3 Collection/MP3/" by detecting redundant parent folders.
        """
        if not self.config.prevent_redundancy:
            return placement_map
        
        logger.debug("Applying Rule 1: Collection Folder Prevention")
        
        updated_map = {}
        result_map = {r.file: r for r in rule_results}
        
        for file_node, target_path in placement_map.items():
            # Get the parent folder (before the filename)
            parent_folder = target_path.parent
            
            # Check if we have category/subcategory structure
            # Path structure is: target_root/category/subcategory/filename
            # We want to check if subcategory is redundant with category
            rule_result = result_map.get(file_node)
            
            if rule_result and rule_result.subcategory:
                # Get just the category folder (parent's parent)
                # e.g., for "Audio/MP3/song.mp3", category folder is "Audio/"
                category_folder = parent_folder.parent
                
                # Build context for category folder only
                mock_category = FileNode(
                    path=category_folder,
                    is_dir=True,
                    size=0,
                    mtime=0.0,
                    parent=None,
                    children=tuple(),
                    depth=0,
                    root_distance=0
                )
                
                category_context = self.context_builder.build_context(mock_category)
                
                # Check if category folder already implies the subcategory
                # Example: "Audio/" folder already means audio files, so "MP3/" is redundant
                if self.context_builder.would_create_redundancy(
                    parent_context=category_context,
                    rule_result=rule_result
                ):
                    # Remove the redundant subcategory level
                    # e.g., "Audio/MP3/file.mp3" -> "Audio/file.mp3"
                    new_path = category_folder / target_path.name
                    logger.debug(
                        f"Redundancy detected: {rule_result.category}/{rule_result.subcategory}/ -> {rule_result.category}/"
                    )
                    updated_map[file_node] = new_path
                else:
                    updated_map[file_node] = target_path
            else:
                updated_map[file_node] = target_path
        
        return updated_map
    
    def _apply_minimum_group_size(
        self,
        placement_map: Dict[FileNode, Path]
    ) -> Dict[FileNode, Path]:
        """
        Rule 2: Minimum Group Size
        
        Requires 5+ files per folder. Merge smaller groups to parent.
        """
        logger.debug("Applying Rule 2: Minimum Group Size")
        
        # Count files per folder (only for paths under target_root)
        folder_counts: Counter = Counter()
        for file_node, target_path in placement_map.items():
            # Skip files in protected roots
            if self._is_in_protected_root(file_node):
                continue
            folder_counts[target_path.parent] += 1
        
        # Find folders with too few files
        small_folders = {
            folder for folder, count in folder_counts.items()
            if count < self.config.min_group_size
        }
        
        if not small_folders:
            return placement_map
        
        logger.debug(f"Found {len(small_folders)} folders with <{self.config.min_group_size} files")
        
        # Merge small folders to parent
        updated_map = {}
        for file_node, target_path in placement_map.items():
            # Skip files in protected roots
            if self._is_in_protected_root(file_node):
                updated_map[file_node] = target_path
                continue
            
            if target_path.parent in small_folders:
                # Move to parent folder
                new_path = target_path.parent.parent / target_path.name
                logger.debug(f"Merging small folder: {target_path.parent.name}/ -> {new_path.parent.name}/")
                updated_map[file_node] = new_path
            else:
                updated_map[file_node] = target_path
        
        return updated_map
    
    def _apply_depth_limit(
        self,
        placement_map: Dict[FileNode, Path]
    ) -> Dict[FileNode, Path]:
        """
        Rule 3: Depth Limit
        
        Enforces maximum 3 levels deep from target root.
        """
        logger.debug("Applying Rule 3: Depth Limit")
        
        updated_map = {}
        
        for file_node, target_path in placement_map.items():
            # Calculate depth relative to target root
            try:
                relative_path = target_path.relative_to(self.target_root)
                depth = len(relative_path.parts) - 1  # -1 for filename
                
                if depth > self.config.max_depth:
                    # Flatten to max depth
                    # e.g., "Root/A/B/C/D/file.ext" -> "Root/A/B/C/file.ext"
                    parts = list(relative_path.parts)
                    new_parts = parts[:self.config.max_depth] + [parts[-1]]
                    new_path = self.target_root / Path(*new_parts)
                    
                    logger.debug(
                        f"Depth limit exceeded ({depth} > {self.config.max_depth}): "
                        f"{relative_path} -> {new_path.relative_to(self.target_root)}"
                    )
                    updated_map[file_node] = new_path
                else:
                    updated_map[file_node] = target_path
            except ValueError:
                # Path not relative to target root, keep as is
                updated_map[file_node] = target_path
        
        return updated_map
    
    def _apply_sibling_merge(
        self,
        placement_map: Dict[FileNode, Path]
    ) -> Dict[FileNode, Path]:
        """
        Rule 4: Sibling Analysis
        
        Merges small adjacent folders with similar content.
        """
        logger.debug("Applying Rule 4: Sibling Analysis")
        
        # Group files by parent folder
        parent_groups: Dict[Path, List[Tuple[FileNode, Path]]] = defaultdict(list)
        for file_node, target_path in placement_map.items():
            parent_groups[target_path.parent].append((file_node, target_path))
        
        # Find sibling folders (same grandparent)
        grandparent_groups: Dict[Path, List[Path]] = defaultdict(list)
        for parent in parent_groups.keys():
            if parent.parent != self.target_root:  # Skip top-level folders
                grandparent_groups[parent.parent].append(parent)
        
        # Check for mergeable siblings
        updated_map = dict(placement_map)
        
        for grandparent, siblings in grandparent_groups.items():
            if len(siblings) < 2:
                continue
            
            # Find siblings with ≤ merge_threshold files
            small_siblings = [
                sibling for sibling in siblings
                if len(parent_groups[sibling]) <= self.config.merge_threshold
            ]
            
            if len(small_siblings) >= 2:
                # Merge all small siblings to grandparent
                logger.debug(
                    f"Merging {len(small_siblings)} small sibling folders in {grandparent.name}/"
                )
                
                for sibling in small_siblings:
                    for file_node, target_path in parent_groups[sibling]:
                        new_path = grandparent / target_path.name
                        updated_map[file_node] = new_path
        
        return updated_map
    
    def _apply_context_collapse(
        self,
        placement_map: Dict[FileNode, Path],
        rule_results: List[RuleResult]
    ) -> Dict[FileNode, Path]:
        """
        Rule 5: Context Collapse
        
        Prevents duplicate naming in path (e.g., "Python/Python/", "PDF/PDF/").
        """
        logger.debug("Applying Rule 5: Context Collapse")
        
        updated_map = {}
        
        for file_node, target_path in placement_map.items():
            # Get path parts relative to target root
            try:
                relative_path = target_path.relative_to(self.target_root)
                parts = list(relative_path.parts[:-1])  # Exclude filename
                
                # Check for duplicate folder names
                seen_names = set()
                collapsed_parts = []
                
                for part in parts:
                    part_lower = part.lower()
                    if part_lower not in seen_names:
                        collapsed_parts.append(part)
                        seen_names.add(part_lower)
                    else:
                        logger.debug(f"Collapsing duplicate: {part}")
                
                # Rebuild path
                if len(collapsed_parts) < len(parts):
                    new_path = self.target_root / Path(*collapsed_parts) / target_path.name
                    updated_map[file_node] = new_path
                else:
                    updated_map[file_node] = target_path
            except ValueError:
                # Path not relative to target root
                updated_map[file_node] = target_path
        
        return updated_map
    
    # =========================================================================
    # Decision Creation & Validation
    # =========================================================================
    
    def _create_decisions(
        self,
        placement_map: Dict[FileNode, Path],
        rule_results: List[RuleResult]
    ) -> List[PlacementDecision]:
        """Convert placement map to decision objects."""
        decisions = []
        result_map = {r.file: r for r in rule_results}
        
        for file_node, target_path in placement_map.items():
            rule_result = result_map.get(file_node)
            
            # Determine if file needs to move
            current_path = file_node.path
            will_move = current_path != target_path
            
            # Determine source
            if file_node in [r.file for r in rule_results]:
                source = DecisionSource.RULE
            else:
                source = DecisionSource.CONTEXT
            
            # Build reason
            if self._is_in_protected_root(file_node):
                reason = f"Protected root: {self._get_root_name(file_node)}"
            elif not will_move:
                reason = "Already in correct location"
            elif rule_result:
                reason = f"Classified as {rule_result.category}/{rule_result.subcategory}"
            else:
                reason = "Rule-based organization"
            
            decision = PlacementDecision(
                file=file_node,
                target=target_path,
                reason=reason,
                source=source,
                conflicts=tuple(),  # Will be populated during validation
                safe=True,
                rule_result=rule_result,
                ai_result=None
            )
            
            decisions.append(decision)
        
        return decisions
    
    def _validate_decisions(
        self,
        decisions: List[PlacementDecision]
    ) -> List[PlacementDecision]:
        """
        Validate decisions and detect conflicts.
        
        Conflicts occur when multiple files would move to the same target path.
        """
        # Group by target path
        target_groups: Dict[Path, List[PlacementDecision]] = defaultdict(list)
        for decision in decisions:
            target_groups[decision.target].append(decision)
        
        # Check for conflicts
        validated = []
        for target_path, group in target_groups.items():
            if len(group) > 1:
                # Conflict detected
                logger.warning(f"Conflict: {len(group)} files targeting {target_path}")
                
                # Mark all as conflicted
                for decision in group:
                    conflicted_decision = PlacementDecision(
                        file=decision.file,
                        target=decision.target,
                        reason=decision.reason,
                        source=decision.source,
                        conflicts=tuple([str(d.file.path) for d in group if d.file != decision.file]),
                        safe=False,  # Not safe due to conflict
                        rule_result=decision.rule_result,
                        ai_result=decision.ai_result
                    )
                    validated.append(conflicted_decision)
            else:
                validated.append(group[0])
        
        return validated
    
    def _get_root_name(self, file_node: FileNode) -> str:
        """Get the name of the protected root containing this file."""
        if not self._protected_roots:
            return "Unknown"
        
        for root_info in self._protected_roots:
            try:
                file_node.path.relative_to(root_info.path)
                return f"{root_info.root_type.value}: {root_info.path.name}"
            except ValueError:
                continue
        
        return "Unknown"


# Convenience function
def resolve_file_placements(
    root_node: FileNode,
    rule_results: List[RuleResult],
    target_root: Path,
    ai_results: Optional[List[AIResult]] = None,
    config: Optional[PlacementConfig] = None
) -> List[PlacementDecision]:
    """
    Convenience function to resolve file placements.
    
    Args:
        root_node: Root of scanned file tree
        rule_results: Classification results
        target_root: Target organization root
        ai_results: Optional AI grouping results
        config: Optional configuration
        
    Returns:
        List of placement decisions
    """
    resolver = PlacementResolver(target_root, config)
    return resolver.resolve_placements(root_node, rule_results, ai_results)
