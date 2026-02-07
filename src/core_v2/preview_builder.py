"""Preview Builder v2 - Generate user-facing organization previews.

This module creates comprehensive, visual previews of proposed file organization
before execution. Shows folder structure, AI groupings, confidence scores, and statistics.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict

from .models import PlacementDecision, AIResult, DecisionSource


@dataclass
class PreviewConfig:
    """Configuration for preview generation."""
    show_confidence: bool = True
    show_ai_groups: bool = True
    max_files_per_folder: int = 10  # Show first N files, then "..."
    show_hidden: bool = False
    color_output: bool = True
    export_path: Optional[Path] = None


@dataclass
class PreviewStats:
    """Statistics about the organization preview."""
    total_files: int = 0
    total_folders: int = 0
    files_moved: int = 0
    folders_created: int = 0
    ai_groups_found: int = 0
    avg_confidence: float = 0.0
    protected_files: int = 0


class PreviewBuilderV2:
    """Builds user-facing preview of file organization."""
    
    # ANSI color codes for terminal output
    COLORS = {
        'high': '\033[92m',      # Green (confidence >= 0.85)
        'medium': '\033[93m',    # Yellow (0.70 <= confidence < 0.85)
        'low': '\033[91m',       # Red (confidence < 0.70)
        'ai_group': '\033[94m',  # Blue (AI grouped files)
        'protected': '\033[95m', # Magenta (protected files)
        'bold': '\033[1m',       # Bold text
        'reset': '\033[0m'       # Reset color
    }
    
    def __init__(self, config: Optional[PreviewConfig] = None):
        """Initialize preview builder.
        
        Args:
            config: Optional configuration for preview generation
        """
        self.config = config or PreviewConfig()
    
    def build_preview(
        self,
        placements: List[PlacementDecision],
        ai_results: Optional[List[AIResult]] = None,
        base_path: Optional[Path] = None
    ) -> str:
        """Generate comprehensive preview of organization.
        
        Args:
            placements: List of placement decisions
            ai_results: Optional list of AI grouping results
            base_path: Optional base path for relative display
            
        Returns:
            Formatted preview string
        """
        if not placements:
            return self._format_empty_preview()
        
        # Calculate statistics
        stats = self._calculate_stats(placements, ai_results or [])
        
        # Build tree structure
        tree = self._build_tree(placements)
        
        # Format sections
        sections = []
        sections.append(self._format_header())
        sections.append(self._format_stats(stats))
        sections.append(self._format_tree_section(tree))
        
        if ai_results and self.config.show_ai_groups:
            sections.append(self._format_ai_groups_section(ai_results, placements))
        
        sections.append(self._format_notes(stats))
        sections.append(self._format_footer())
        
        return '\n\n'.join(sections)
    
    def _build_tree(self, placements: List[PlacementDecision]) -> Dict:
        """Build nested tree structure from flat placements.
        
        Args:
            placements: List of placement decisions
            
        Returns:
            Nested dictionary representing folder tree
        """
        tree = {}
        
        for placement in placements:
            parts = placement.target.parts
            current = tree
            
            # Navigate/create nested structure (folders)
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {'_files': [], '_metadata': {}}
                current = current[part]
            
            # Add file
            if '_files' not in current:
                current['_files'] = []
            
            # Derive confidence from safe flag and conflicts
            confidence = 1.0 if placement.safe and not placement.has_conflicts else 0.5
            
            current['_files'].append({
                'name': parts[-1],
                'confidence': confidence,
                'ai_group': placement.ai_result.group if placement.ai_result else None,
                'protected': placement.source == DecisionSource.PROTECTED,
                'original_path': placement.file.path
            })
        
        return tree
    
    def _format_tree_section(self, tree: Dict) -> str:
        """Format tree structure section.
        
        Args:
            tree: Tree dictionary from _build_tree
            
        Returns:
            Formatted tree section
        """
        lines = [
            self._colorize("📁 Folder Structure", 'bold'),
            "─" * 65
        ]
        
        tree_lines = self._format_tree(tree, indent=0)
        lines.extend(tree_lines)
        
        return '\n'.join(lines)
    
    def _format_tree(
        self,
        tree: Dict,
        indent: int = 0,
        prefix: str = "",
        is_last: bool = True
    ) -> List[str]:
        """Format tree structure with ASCII art.
        
        Args:
            tree: Tree dictionary
            indent: Current indentation level
            prefix: Prefix for current line
            is_last: Whether this is the last item in parent
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Get folders and files
        folders = {k: v for k, v in tree.items() if k not in ('_files', '_metadata')}
        files = tree.get('_files', [])
        
        # Process folders
        folder_items = list(folders.items())
        for i, (folder_name, folder_data) in enumerate(folder_items):
            is_last_folder = (i == len(folder_items) - 1) and not files
            
            # Format folder line
            connector = "└── " if is_last_folder else "├── "
            line = f"{prefix}{connector}{folder_name}/"
            lines.append(line)
            
            # Recurse into subfolder
            new_prefix = prefix + ("    " if is_last_folder else "│   ")
            subfolder_lines = self._format_tree(
                folder_data,
                indent + 1,
                new_prefix,
                is_last_folder
            )
            lines.extend(subfolder_lines)
        
        # Process files
        if files:
            # Check if we need to truncate
            display_files = files[:self.config.max_files_per_folder]
            truncated = len(files) > self.config.max_files_per_folder
            
            for i, file_info in enumerate(display_files):
                is_last_file = (i == len(display_files) - 1) and not truncated
                connector = "└── " if is_last_file else "├── "
                
                # Format filename with indicators
                filename = file_info['name']
                indicators = []
                
                # Add confidence indicator
                if self.config.show_confidence:
                    conf_pct = f"{file_info['confidence'] * 100:.0f}%"
                    conf_color = self._get_confidence_color(file_info['confidence'])
                    indicators.append(self._colorize(f"[{conf_pct}]", conf_color))
                
                # Add AI group indicator
                if file_info.get('ai_group'):
                    indicators.append(self._colorize("[AI]", 'ai_group'))
                
                # Add protected indicator
                if file_info.get('protected'):
                    indicators.append(self._colorize("[Protected]", 'protected'))
                
                # Combine filename and indicators
                indicator_str = " ".join(indicators) if indicators else ""
                line = f"{prefix}{connector}{filename} {indicator_str}".rstrip()
                lines.append(line)
            
            # Add truncation indicator
            if truncated:
                remaining = len(files) - self.config.max_files_per_folder
                connector = "└── "
                line = f"{prefix}{connector}... ({remaining} more files)"
                lines.append(line)
        
        return lines
    
    def _calculate_stats(
        self,
        placements: List[PlacementDecision],
        ai_results: List[AIResult]
    ) -> PreviewStats:
        """Calculate organization statistics.
        
        Args:
            placements: List of placement decisions
            ai_results: List of AI grouping results
            
        Returns:
            Statistics object
        """
        stats = PreviewStats()
        
        stats.total_files = len(placements)
        
        # Count unique folders
        folders = set()
        for placement in placements:
            for i in range(1, len(placement.target.parts)):
                folder_path = Path(*placement.target.parts[:i])
                folders.add(folder_path)
        stats.total_folders = len(folders)
        
        # Count files that will be moved (original != final)
        stats.files_moved = sum(1 for p in placements if p.will_move)
        
        # Count folders to create (estimate - would need original structure)
        stats.folders_created = stats.total_folders
        
        # Count AI groups
        if ai_results:
            ai_groups = set(r.group for r in ai_results if r.group)
            stats.ai_groups_found = len(ai_groups)
        
        # Calculate average confidence (safe placements = 1.0, conflicts = 0.5)
        if placements:
            confidences = [1.0 if p.safe and not p.has_conflicts else 0.5 for p in placements]
            stats.avg_confidence = sum(confidences) / len(placements)
        
        # Count protected files
        stats.protected_files = sum(1 for p in placements if p.source == DecisionSource.PROTECTED)
        
        return stats
    
    def _format_header(self) -> str:
        """Format preview header."""
        lines = [
            "╔" + "═" * 64 + "╗",
            "║" + "AutoFolder AI - Organization Preview".center(64) + "║",
            "╚" + "═" * 64 + "╝"
        ]
        return '\n'.join(lines)
    
    def _format_footer(self) -> str:
        """Format preview footer."""
        return "═" * 66
    
    def _format_stats(self, stats: PreviewStats) -> str:
        """Format statistics section.
        
        Args:
            stats: Statistics object
            
        Returns:
            Formatted statistics section
        """
        lines = [
            self._colorize("📊 Statistics", 'bold'),
            "─" * 65,
            f"  Total Files:          {stats.total_files}",
            f"  Total Folders:        {stats.total_folders}",
            f"  Files to Move:        {stats.files_moved}",
            f"  Folders to Create:    {stats.folders_created}",
            f"  AI Groups Found:      {stats.ai_groups_found}",
            f"  Avg Confidence:       {stats.avg_confidence * 100:.0f}%",
            f"  Protected Files:      {stats.protected_files}"
        ]
        return '\n'.join(lines)
    
    def _format_ai_groups_section(
        self,
        ai_results: List[AIResult],
        placements: List[PlacementDecision]
    ) -> str:
        """Format AI groupings section.
        
        Args:
            ai_results: List of AI grouping results
            placements: List of placement decisions
            
        Returns:
            Formatted AI groups section
        """
        lines = [
            self._colorize("🤖 AI Groupings", 'bold'),
            "─" * 65
        ]
        
        # Group AI results by group name
        groups = defaultdict(list)
        for result in ai_results:
            if result.group:
                groups[result.group].append(result)
        
        if not groups:
            lines.append("  No AI groups found")
            return '\n'.join(lines)
        
        # Create placement lookup for finding target folders
        placement_map = {p.file.path: p for p in placements}
        
        # Format each group
        for i, (group_name, group_results) in enumerate(sorted(groups.items()), 1):
            # Calculate group confidence
            avg_conf = sum(r.confidence for r in group_results) / len(group_results)
            
            # Find target folder (from first result)
            target_folder = "Unknown"
            if group_results[0].file in placement_map:
                target_folder = placement_map[group_results[0].file].target.parent
            
            # Format group entry
            conf_str = f"{avg_conf * 100:.0f}%"
            lines.append(
                f"  {i}. {self._colorize(group_name, 'ai_group')} "
                f"({len(group_results)} files, {conf_str} confidence)"
            )
            lines.append(f"     → {target_folder}")
            
            if i < len(groups):
                lines.append("")  # Blank line between groups
        
        return '\n'.join(lines)
    
    def _format_notes(self, stats: PreviewStats) -> str:
        """Format notes section.
        
        Args:
            stats: Statistics object
            
        Returns:
            Formatted notes section
        """
        lines = [
            self._colorize("⚠️  Notes", 'bold'),
            "─" * 65
        ]
        
        if stats.protected_files > 0:
            lines.append(f"  • {stats.protected_files} files are protected and will remain in place")
        
        lines.append("  • Files with confidence < 70% should be reviewed")
        
        if stats.ai_groups_found > 0:
            lines.append("  • AI groups are suggestions based on semantic similarity")
        
        lines.append("  • You can modify this organization before applying")
        
        return '\n'.join(lines)
    
    def _format_empty_preview(self) -> str:
        """Format preview for empty placements."""
        return (
            f"{self._format_header()}\n\n"
            f"{self._colorize('No files to organize', 'bold')}\n\n"
            f"{self._format_footer()}"
        )
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color name based on confidence level.
        
        Args:
            confidence: Confidence value (0-1)
            
        Returns:
            Color name for _colorize
        """
        if confidence >= 0.85:
            return 'high'
        elif confidence >= 0.70:
            return 'medium'
        else:
            return 'low'
    
    def _colorize(self, text: str, color: str) -> str:
        """Add terminal color codes to text.
        
        Args:
            text: Text to colorize
            color: Color name from COLORS dict
            
        Returns:
            Colorized text (or plain if colors disabled)
        """
        if not self.config.color_output:
            return text
        
        color_code = self.COLORS.get(color, '')
        reset_code = self.COLORS['reset']
        return f"{color_code}{text}{reset_code}"
    
    def export_preview(self, preview: str, path: Path):
        """Export preview to text file (strips color codes).
        
        Args:
            preview: Preview string (may contain color codes)
            path: Output file path
        """
        # Strip ANSI color codes
        import re
        clean_preview = re.sub(r'\033\[[0-9;]+m', '', preview)
        
        # Write to file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(clean_preview, encoding='utf-8')


# Convenience function
def build_preview(
    placements: List[PlacementDecision],
    ai_results: Optional[List[AIResult]] = None,
    config: Optional[PreviewConfig] = None
) -> str:
    """Convenience function to build preview.
    
    Args:
        placements: List of placement decisions
        ai_results: Optional list of AI grouping results
        config: Optional preview configuration
        
    Returns:
        Formatted preview string
    """
    builder = PreviewBuilderV2(config)
    return builder.build_preview(placements, ai_results)
