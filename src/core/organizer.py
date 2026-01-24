"""
File Organizer Engine

Core logic for analyzing, categorizing, and organizing files.
This is the heart of AutoFolder AI.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

from .rules import RuleEngine
from .file_analyzer import FileAnalyzer
from .undo_manager import UndoManager


logger = logging.getLogger(__name__)


class FileOrganizer:
    """Main file organization engine."""
    
    def __init__(self, config: dict):
        """
        Initialize the file organizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.rule_engine = RuleEngine()
        self.file_analyzer = FileAnalyzer()
        self.undo_manager = UndoManager(
            max_history=config.get('safety', {}).get('max_undo_history', 10)
        )
        
        self.dry_run = config.get('safety', {}).get('dry_run_default', True)
        self.never_delete = config.get('safety', {}).get('never_delete', True)
        
    def analyze_folder(self, folder_path: Path) -> Dict:
        """
        Analyze a folder and return statistics.
        
        Args:
            folder_path: Path to folder to analyze
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing folder: {folder_path}")
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        if not folder_path.is_dir():
            raise ValueError(f"Path is not a folder: {folder_path}")
        
        files = list(folder_path.glob('*'))
        files = [f for f in files if f.is_file()]
        
        # Ignore hidden files if configured
        if self.config.get('organization', {}).get('ignore_hidden_files', True):
            files = [f for f in files if not f.name.startswith('.')]
        
        analysis = {
            'total_files': len(files),
            'total_size': sum(f.stat().st_size for f in files),
            'by_extension': {},
            'by_date': {},
            'by_size_range': {
                'tiny': 0,      # < 1MB
                'small': 0,     # 1-10MB
                'medium': 0,    # 10-100MB
                'large': 0,     # 100MB-1GB
                'huge': 0       # > 1GB
            },
            'files': files
        }
        
        # Categorize files
        for file_path in files:
            # By extension
            ext = file_path.suffix.lower()
            analysis['by_extension'][ext] = analysis['by_extension'].get(ext, 0) + 1
            
            # By date (month)
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                month_key = mtime.strftime('%Y-%m')
                analysis['by_date'][month_key] = analysis['by_date'].get(month_key, 0) + 1
            except:
                pass
            
            # By size
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            if size_mb < 1:
                analysis['by_size_range']['tiny'] += 1
            elif size_mb < 10:
                analysis['by_size_range']['small'] += 1
            elif size_mb < 100:
                analysis['by_size_range']['medium'] += 1
            elif size_mb < 1024:
                analysis['by_size_range']['large'] += 1
            else:
                analysis['by_size_range']['huge'] += 1
        
        logger.info(f"Analysis complete: {analysis['total_files']} files found")
        return analysis
    
    def preview_organization(
        self, 
        folder_path: Path, 
        profile: str = None,
        custom_rules: List[Dict] = None
    ) -> List[Dict]:
        """
        Preview what organization will do without making changes.
        
        Args:
            folder_path: Folder to organize
            profile: Profile name to use (e.g., 'downloads', 'media')
            custom_rules: Custom rule list
            
        Returns:
            List of planned operations
        """
        logger.info(f"Generating preview for: {folder_path}")
        
        analysis = self.analyze_folder(folder_path)
        files = analysis['files']
        
        # Get rules from profile or custom
        if profile:
            rules = self.rule_engine.get_profile_rules(profile)
        elif custom_rules:
            rules = custom_rules
        else:
            rules = self.rule_engine.get_default_rules()
        
        operations = []
        
        for file_path in files:
            # Determine target location based on rules
            target_folder = self._determine_target_folder(
                file_path, 
                folder_path, 
                rules
            )
            
            if target_folder:
                target_path = target_folder / file_path.name
                
                # Handle conflicts
                if target_path.exists():
                    conflict_resolution = self.config.get('organization', {}).get('handle_conflicts', 'rename')
                    if conflict_resolution == 'rename':
                        target_path = self._get_unique_path(target_path)
                    elif conflict_resolution == 'skip':
                        continue
                
                operations.append({
                    'source': file_path,
                    'target': target_path,
                    'action': 'move',
                    'category': target_folder.name,
                    'size': file_path.stat().st_size,
                    'status': 'pending'
                })
        
        logger.info(f"Preview generated: {len(operations)} operations planned")
        return operations
    
    def organize_folder(
        self,
        folder_path: Path,
        profile: str = None,
        custom_rules: List[Dict] = None,
        dry_run: bool = None
    ) -> Dict:
        """
        Organize files in a folder based on rules.
        
        Args:
            folder_path: Folder to organize
            profile: Profile name to use
            custom_rules: Custom rule list
            dry_run: If True, don't actually move files
            
        Returns:
            Dictionary with results
        """
        if dry_run is None:
            dry_run = self.dry_run
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Organizing folder: {folder_path}")
        
        # Get preview of operations
        operations = self.preview_organization(folder_path, profile, custom_rules)
        
        if dry_run:
            logger.info(f"Dry run complete: {len(operations)} operations would be performed")
            return {
                'success': True,
                'dry_run': True,
                'operations': operations,
                'total': len(operations),
                'completed': 0
            }
        
        # Execute operations
        completed = []
        failed = []
        
        for op in operations:
            try:
                # Create target folder if needed
                op['target'].parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(op['source']), str(op['target']))
                
                op['status'] = 'completed'
                completed.append(op)
                logger.debug(f"Moved: {op['source'].name} -> {op['target']}")
                
            except Exception as e:
                op['status'] = 'failed'
                op['error'] = str(e)
                failed.append(op)
                logger.error(f"Failed to move {op['source'].name}: {e}")
        
        # Save to undo history
        if completed:
            self.undo_manager.save_operation({
                'timestamp': datetime.now(),
                'folder': str(folder_path),
                'operations': completed
            })
        
        result = {
            'success': len(failed) == 0,
            'dry_run': False,
            'operations': operations,
            'total': len(operations),
            'completed': len(completed),
            'failed': len(failed),
            'can_undo': len(completed) > 0
        }
        
        logger.info(f"Organization complete: {len(completed)} succeeded, {len(failed)} failed")
        return result
    
    def undo_last_operation(self) -> bool:
        """
        Undo the last organization operation.
        
        Returns:
            True if successful
        """
        logger.info("Attempting to undo last operation...")
        
        last_op = self.undo_manager.get_last_operation()
        if not last_op:
            logger.warning("No operation to undo")
            return False
        
        success_count = 0
        operations = last_op.get('operations', [])
        
        for op in operations:
            try:
                # Move file back to original location
                shutil.move(str(op['target']), str(op['source']))
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to undo move for {op['target'].name}: {e}")
        
        if success_count == len(operations):
            self.undo_manager.remove_last_operation()
            logger.info(f"Successfully undid {success_count} operations")
            return True
        else:
            logger.warning(f"Partially undid operation: {success_count}/{len(operations)}")
            return False
    
    def _determine_target_folder(
        self, 
        file_path: Path, 
        base_folder: Path, 
        rules: List[Dict]
    ) -> Optional[Path]:
        """Determine target folder based on rules."""
        
        for rule in rules:
            if self.rule_engine.matches_rule(file_path, rule):
                target_name = rule.get('target_folder', 'Other')
                return base_folder / target_name
        
        return None
    
    def _get_unique_path(self, path: Path) -> Path:
        """Generate unique path if file exists."""
        
        if not path.exists():
            return path
        
        counter = 1
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        while True:
            new_name = f"{stem} ({counter}){suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
