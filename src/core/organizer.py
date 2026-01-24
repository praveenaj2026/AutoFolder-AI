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
from .duplicate_detector import DuplicateDetector
from .smart_renamer import SmartRenamer


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
        # AI classifier for semantic grouping (REQUIRED - always enabled)
        self.ai_classifier = None
        self.semantic_groups = {}  # Cache for semantic groups
        
        # Duplicate detector for finding duplicate files
        self.duplicate_detector = DuplicateDetector()
        self.duplicates = {}  # Cache for found duplicates
        self.duplicate_action = None  # Action to take on duplicates
        
        # Smart renamer for AI-based filename suggestions
        self.smart_renamer = SmartRenamer(config)
        self.rename_suggestions = {}  # Cache for rename suggestions        
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
        
        # Get all items recursively
        all_items = list(folder_path.glob('*'))
        files = [f for f in all_items if f.is_file()]
        folders = [f for f in all_items if f.is_dir()]
        
        # Also collect files from subfolders for total count
        all_files_recursive = [f for f in folder_path.rglob('*') if f.is_file()]
        
        logger.debug(f"Found {len(files)} root files, {len(folders)} folders, {len(all_files_recursive)} total files (recursive)")
        
        # Ignore hidden files if configured
        if self.config.get('organization', {}).get('ignore_hidden_files', True):
            files = [f for f in files if not f.name.startswith('.')]
            folders = [f for f in folders if not f.name.startswith('.')]
        
        # Skip common organized folder names to avoid recursive moves
        organized_folder_names = {
            'Documents', 'Images', 'Videos', 'Audio', 'Archives', 
            'Code', 'Installers', 'Gaming', 'Other', 'Compressed'
        }
        
        # Skip common system/app/game folders that should not be organized
        system_folder_patterns = [
            'WindowsPowerShell', 'KingsoftData', 'WPS Cloud Files',
            'Custom Office Templates', 'Rockstar Games', 'My Games',
            'FIFA', 'FC ', 'WWE', 'GTA', 'Gameloft',  # Games
            'pyinstaller', 'venv', 'node_modules', '.git', '__pycache__'  # Dev folders
        ]
        
        # Peek inside folders and treat them as files for organization
        folder_items = []
        for folder in folders:
            # Skip if it's likely an already-organized folder
            if folder.name in organized_folder_names:
                logger.debug(f"Skipping already-organized folder: {folder.name}")
                continue
            
            # Skip system/app/game folders
            if any(pattern in folder.name for pattern in system_folder_patterns):
                logger.debug(f"Skipping system/app folder: {folder.name}")
                continue
                
            try:
                # Peek at first few files to determine folder type (look deeper if needed)
                folder_files = []
                # First, try root level files
                root_files = [f for f in folder.glob('*') if f.is_file()]
                folder_files.extend(root_files[:10])
                
                # If not enough files at root, peek into subdirectories
                if len(folder_files) < 3:
                    for subdir in [d for d in folder.glob('*') if d.is_dir()][:5]:
                        try:
                            subdir_files = [f for f in subdir.glob('*') if f.is_file()]
                            folder_files.extend(subdir_files[:5])
                            if len(folder_files) >= 10:
                                break
                        except:
                            continue
                
                logger.debug(f"Peeked into '{folder.name}': found {len(folder_files)} sample files")
                
                if folder_files:
                    # Calculate folder size
                    folder_size = sum(f.stat().st_size for f in folder_files)
                    # Use first file's extension as representative
                    folder_items.append({
                        'path': folder,
                        'is_folder': True,
                        'size': folder_size,
                        'sample_files': folder_files
                    })
                    logger.debug(f"Added folder '{folder.name}' to organization queue")
                else:
                    logger.debug(f"Folder '{folder.name}' has no files, skipping")
            except Exception as e:
                logger.warning(f"Could not peek into folder {folder}: {e}")
        
        analysis = {
            'total_files': len(all_files_recursive),  # Count all files recursively
            'root_files': len(files),
            'total_folders': len(folder_items),
            'total_size': sum(f.stat().st_size for f in all_files_recursive),  # Size of all files
            'by_extension': {},
            'by_date': {},
            'by_size_range': {
                'tiny': 0,      # < 1MB
                'small': 0,     # 1-10MB
                'medium': 0,    # 10-100MB
                'large': 0,     # 100MB-1GB
                'huge': 0       # > 1GB
            },
            'files': files,
            'folders': folder_items
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
    
    def scan_for_duplicates(
        self,
        folder_path: Path,
        algorithm: str = 'sha256'
    ) -> Tuple[Dict[str, List[Path]], Dict]:
        """
        Scan folder for duplicate files.
        
        Args:
            folder_path: Path to folder to scan
            algorithm: Hash algorithm (sha256, md5)
            
        Returns:
            Tuple of (duplicates_dict, stats_dict)
        """
        logger.info(f"Scanning for duplicates in: {folder_path}")
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Get all files recursively
        all_files = [
            f for f in folder_path.rglob('*') 
            if f.is_file() and not self._should_skip_file(f)
        ]
        
        logger.info(f"Found {len(all_files)} files to scan")
        
        # Find duplicates
        duplicates = self.duplicate_detector.find_duplicates(all_files, algorithm)
        
        # Analyze duplicates
        stats = self.duplicate_detector.analyze_duplicates(duplicates)
        
        # Cache results
        self.duplicates = duplicates
        
        logger.info(
            f"Duplicate scan complete: {stats['duplicate_groups']} groups, "
            f"{stats['wasted_space_mb']:.2f} MB wasted space"
        )
        
        return duplicates, stats
    
    def handle_duplicates(
        self, 
        duplicates: Dict[str, List[Path]], 
        action: str,
        target_folder: Path = None
    ) -> Dict:
        """
        Handle duplicate files based on action.
        
        Args:
            duplicates: Dict from scan_for_duplicates
            action: Action to take (keep_newest, keep_oldest, keep_all, skip)
            target_folder: Target folder for 'keep_all' action
            
        Returns:
            Dictionary with results including detailed file lists
        """
        if action == 'skip':
            logger.info("Skipping duplicate handling")
            return {
                'files_deleted': 0, 
                'files_moved': 0, 
                'space_freed': 0,
                'deleted_files': [],
                'moved_files': [],
                'kept_files': []
            }
        
        files_deleted = 0
        files_moved = 0
        space_freed = 0
        deleted_files = []
        moved_files = []
        kept_files = []
        
        if action == 'keep_all':
            # Move all duplicates to target folder
            if not target_folder:
                target_folder = Path(self.config.get('duplicates', {}).get(
                    'move_duplicates_to', 'Duplicates'
                ))
            
            target_folder.mkdir(parents=True, exist_ok=True)
            
            for hash_val, file_list in duplicates.items():
                # Keep the first one, move the rest
                if file_list:
                    kept_files.append(str(file_list[0]))
                    logger.info(f"Kept original: {file_list[0].name}")
                
                # Move all but the first one
                for file_path in file_list[1:]:
                    try:
                        dest = target_folder / file_path.name
                        # Handle name conflicts
                        counter = 1
                        while dest.exists():
                            stem = file_path.stem
                            suffix = file_path.suffix
                            dest = target_folder / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        shutil.move(str(file_path), str(dest))
                        files_moved += 1
                        moved_files.append((str(file_path), str(dest)))
                        logger.info(f"Moved duplicate: {file_path.name} → {dest}")
                    except Exception as e:
                        logger.error(f"Error moving duplicate {file_path}: {e}")
        
        elif action in ['keep_newest', 'keep_oldest']:
            # Delete duplicates based on strategy
            for hash_val, file_list in duplicates.items():
                keep, remove = self.duplicate_detector.select_files_to_keep(
                    file_list, 
                    strategy=action.replace('keep_', '')
                )
                
                if keep:
                    kept_files.append(str(keep))
                    logger.info(f"Kept: {keep.name}")
                
                for file_path in remove:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        files_deleted += 1
                        space_freed += file_size
                        deleted_files.append(str(file_path))
                        logger.info(f"Deleted duplicate: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Error deleting duplicate {file_path}: {e}")
        
        space_freed_mb = space_freed / (1024 * 1024)
        logger.info(
            f"Duplicate handling complete: {files_deleted} deleted, "
            f"{files_moved} moved, {space_freed_mb:.2f} MB freed"
        )
        
        return {
            'files_deleted': files_deleted,
            'files_moved': files_moved,
            'space_freed': space_freed,
            'space_freed_mb': space_freed_mb,
            'deleted_files': deleted_files,
            'moved_files': moved_files,
            'kept_files': kept_files
        }
    
    def preview_organization(
        self, 
        folder_path: Path, 
        profile: str = None,
        custom_rules: List[Dict] = None
    ) -> List[Dict]:
        """
        Preview what organization will do without making changes.
        AI semantic grouping is ALWAYS enabled.
        
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
        folders = analysis.get('folders', [])
        
        # Get rules from profile or custom
        if profile:
            rules = self.rule_engine.get_profile_rules(profile)
        elif custom_rules:
            rules = custom_rules
        else:
            rules = self.rule_engine.get_default_rules()
        
        # AI Semantic Grouping - ALWAYS ENABLED
        if self.ai_classifier:
            logger.info("Creating AI semantic groups...")
            try:
                # Collect all files for AI analysis (root + subfolders)
                all_files_for_ai = list(files)  # Start with root files
                
                # Add subfolder files
                organized_folder_names = {
                    'Documents', 'Images', 'Videos', 'Audio', 'Archives', 
                    'Code', 'Installers', 'Gaming', 'Other', 'Compressed'
                }
                system_folder_patterns = [
                    'WindowsPowerShell', 'KingsoftData', 'WPS Cloud Files',
                    'Custom Office Templates', 'Rockstar Games', 'My Games',
                    'FIFA', 'FC ', 'WWE', 'GTA', 'Gameloft',
                    'pyinstaller', 'venv', 'node_modules', '.git', '__pycache__'
                ]
                
                for subfolder_file in folder_path.rglob('*'):
                    if not subfolder_file.is_file():
                        continue
                    if subfolder_file.parent == folder_path:
                        continue
                    
                    # Skip system folders
                    skip_file = False
                    try:
                        rel_path = subfolder_file.relative_to(folder_path)
                        for part in rel_path.parts:
                            if any(pattern in part for pattern in system_folder_patterns):
                                skip_file = True
                                break
                    except:
                        skip_file = True
                    
                    if not skip_file:
                        all_files_for_ai.append(subfolder_file)
                
                # Create semantic groups using AI
                groups_raw = self.ai_classifier.create_semantic_groups(
                    all_files_for_ai, 
                    min_group_size=2
                )
                
                # Convert Path objects to strings for reliable comparison
                self.semantic_groups = {}
                for group_name, files_list in groups_raw.items():
                    self.semantic_groups[group_name] = [str(f) for f in files_list]
                
                if self.semantic_groups:
                    logger.info(f"AI created {len(self.semantic_groups)} semantic groups")
                    for group_name, group_files in self.semantic_groups.items():
                        logger.debug(f"  Group '{group_name}': {len(group_files)} files")
                else:
                    logger.info("AI grouping: No groups created (files too different)")
            except Exception as e:
                logger.error(f"AI semantic grouping FAILED: {e}", exc_info=True)
                logger.error("AI grouping is REQUIRED. Cannot proceed without AI analysis.")
                raise RuntimeError(f"AI semantic grouping failed: {e}") from e
        else:
            error_msg = "AI classifier not initialized. AI grouping is REQUIRED for operation."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        operations = []
        
        # Process files
        for file_path in files:
            logger.debug(f"Processing file: {file_path.name} (ext: {file_path.suffix})")
            target_folder = self._determine_target_folder(
                file_path, 
                folder_path, 
                rules
            )
            
            if target_folder:
                logger.debug(f"  -> Target: {target_folder}")
                
                # Get category and AI group for this file
                category = self._get_category_from_path(target_folder, folder_path)
                ai_group = self._get_ai_group_for_file(file_path)
                
                # Generate smart rename suggestion
                suggested_name = file_path.name  # Default to original
                if self.smart_renamer.enabled:
                    try:
                        file_metadata = {
                            'date': datetime.fromtimestamp(file_path.stat().st_mtime),
                            'size': file_path.stat().st_size
                        }
                        suggested_name = self.smart_renamer.suggest_filename(
                            file_path,
                            ai_group=ai_group,
                            category=category,
                            file_metadata=file_metadata
                        )
                        logger.debug(f"  -> Rename suggestion: {file_path.name} → {suggested_name}")
                    except Exception as e:
                        logger.error(f"Error generating rename suggestion: {e}")
                        suggested_name = file_path.name
                
                target_path = target_folder / suggested_name
                
                # Handle conflicts
                if target_path.exists():
                    conflict_resolution = self.config.get('organization', {}).get('handle_conflicts', 'rename')
                    if conflict_resolution == 'rename':
                        target_path = self._get_unique_path(target_path)
                    elif conflict_resolution == 'skip':
                        logger.debug(f"  -> Skipping (conflict, skip mode)")
                        continue
                
                operations.append({
                    'source': file_path,
                    'target': target_path,
                    'action': 'move',
                    'category': category,
                    'ai_group': ai_group,
                    'original_name': file_path.name,
                    'suggested_name': suggested_name,
                    'size': file_path.stat().st_size,
                    'status': 'pending'
                })
                logger.debug(f"  -> Added to operations")
            else:
                logger.debug(f"  -> No matching rule, skipping")
        
        # Process folders (based on peeked content)
        for folder_info in folders:
            folder_path_item = folder_info['path']
            sample_files = folder_info.get('sample_files', [])
            
            if sample_files:
                # Use first file to determine folder category
                representative_file = sample_files[0]
                target_folder = self._determine_target_folder(
                    representative_file,
                    folder_path,
                    rules
                )
                
                if target_folder:
                    target_path = target_folder / folder_path_item.name
                    
                    # Check if we're trying to move folder into itself (recursive move)
                    try:
                        # This will raise ValueError if target_path is relative to source
                        target_path.relative_to(folder_path_item)
                        logger.warning(f"Skipping recursive move: {folder_path_item.name} -> {target_path}")
                        continue
                    except ValueError:
                        # Good - target is not inside source
                        pass
                    
                    if target_path.exists():
                        conflict_resolution = self.config.get('organization', {}).get('handle_conflicts', 'rename')
                        if conflict_resolution == 'rename':
                            target_path = self._get_unique_path_folder(target_path)
                        elif conflict_resolution == 'skip':
                            continue
                    
                    operations.append({
                        'source': folder_path_item,
                        'target': target_path,
                        'action': 'move',
                        'category': self._get_category_from_path(target_folder, folder_path),
                        'size': folder_info['size'],
                        'status': 'pending',
                        'is_folder': True
                    })
        
        # Also preview files from subfolders (for display purposes)
        organized_folder_names = {
            'Documents', 'Images', 'Videos', 'Audio', 'Archives', 
            'Code', 'Installers', 'Gaming', 'Other', 'Compressed'
        }
        system_folder_patterns = [
            'WindowsPowerShell', 'KingsoftData', 'WPS Cloud Files',
            'Custom Office Templates', 'Rockstar Games', 'My Games',
            'FIFA', 'FC ', 'WWE', 'GTA', 'Gameloft',
            'pyinstaller', 'venv', 'node_modules', '.git', '__pycache__'
        ]
        
        # Find subfolder files to include in preview
        for subfolder_file in folder_path.rglob('*'):
            if not subfolder_file.is_file():
                continue
            
            # Skip if it's a root file (already processed)
            if subfolder_file.parent == folder_path:
                continue
            
            # Skip if in system/app folder (but NOT organized folders - we want to reorganize those)
            skip_this_file = False
            try:
                rel_path = subfolder_file.relative_to(folder_path)
                for part in rel_path.parts:
                    if any(pattern in part for pattern in system_folder_patterns):
                        skip_this_file = True
                        break
            except:
                skip_this_file = True
            
            if skip_this_file:
                continue
            
            # Process this subfolder file
            target_folder = self._determine_target_folder(subfolder_file, folder_path, rules)
            if target_folder:
                target_path = target_folder / subfolder_file.name
                
                # Handle conflicts
                if target_path.exists():
                    conflict_resolution = self.config.get('organization', {}).get('handle_conflicts', 'rename')
                    if conflict_resolution == 'rename':
                        target_path = self._get_unique_path(target_path)
                    elif conflict_resolution == 'skip':
                        continue
                
                operations.append({
                    'source': subfolder_file,
                    'target': target_path,
                    'action': 'move',
                    'category': self._get_category_from_path(target_folder, folder_path),
                    'size': subfolder_file.stat().st_size,
                    'status': 'pending',
                    'from_subfolder': True
                })
        
        logger.info(f"Preview generated: {len(operations)} operations planned")
        
        # Build statistics for dashboard
        stats = self._build_preview_stats(operations, folder_path)
        
        return operations, stats
    
    def _build_preview_stats(self, operations: List[Dict], folder_path: Path) -> Dict:
        """Build comprehensive statistics from preview operations."""
        stats = {
            'total_files': len(operations),
            'total_size': sum(op['size'] for op in operations),
            'by_category': {},
            'by_extension': {},
            'by_size_range': {
                'tiny': 0, 'small': 0, 'medium': 0, 'large': 0, 'huge': 0
            },
            'ai_groups': {},
            'rename_count': 0,
            'folder_path': str(folder_path)
        }
        
        for op in operations:
            # Category stats
            category = op.get('category', 'Other')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Extension stats
            ext = op['source'].suffix.lower().lstrip('.')
            if ext:
                stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
            
            # Size range stats
            size_mb = op['size'] / (1024 * 1024)
            if size_mb < 1:
                stats['by_size_range']['tiny'] += 1
            elif size_mb < 10:
                stats['by_size_range']['small'] += 1
            elif size_mb < 100:
                stats['by_size_range']['medium'] += 1
            elif size_mb < 1024:
                stats['by_size_range']['large'] += 1
            else:
                stats['by_size_range']['huge'] += 1
            
            # AI group stats
            ai_group = op.get('ai_group')
            if ai_group:
                stats['ai_groups'][ai_group] = stats['ai_groups'].get(ai_group, 0) + 1
            
            # Rename stats
            if op.get('suggested_name') != op.get('original_name'):
                stats['rename_count'] += 1
        
        return stats
    
    def organize_folder(
        self,
        folder_path: Path,
        profile: str = None,
        custom_rules: List[Dict] = None,
        dry_run: bool = None,
        recursive: bool = True
    ) -> Dict:
        """
        Organize files in a folder based on rules.
        
        Args:
            folder_path: Folder to organize
            profile: Profile name to use
            custom_rules: Custom rule list
            dry_run: If True, don't actually move files
            recursive: If True, also organize subfolders
            
        Returns:
            Dictionary with results
        """
        if dry_run is None:
            dry_run = self.dry_run
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Organizing folder: {folder_path} {'(recursive)' if recursive else ''}")
        
        # Get preview of operations (returns tuple: operations, stats)
        result = self.preview_organization(folder_path, profile, custom_rules)
        
        # Handle tuple return from preview_organization
        if isinstance(result, tuple) and len(result) == 2:
            operations, stats = result
        else:
            # Fallback for old return format
            operations = result
        
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
            'can_undo': len(completed) > 0,
            'completed_items': [Path(op['source']).name if isinstance(op['source'], str) else op['source'].name for op in completed],
            'failed_items': [(Path(op['source']).name if isinstance(op['source'], str) else op['source'].name, op.get('error', 'Unknown error')) for op in failed]
        }
        
        logger.info(f"Organization complete: {len(completed)} files organized, {len(failed)} failed")
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
    
    def set_ai_classifier(self, classifier):
        """Set AI classifier for semantic grouping."""
        self.ai_classifier = classifier
        logger.info("AI classifier configured for semantic grouping")
    
    def _determine_target_folder(
        self, 
        file_path: Path, 
        base_folder: Path, 
        rules: List[Dict]
    ) -> Optional[Path]:
        """Determine target folder with multi-level sorting (Category → AI Group → Type → Date).
        AI semantic grouping is ALWAYS applied when available."""
        
        # First level: Category (Documents, Images, etc.)
        category_folder = None
        for rule in rules:
            if self.rule_engine.matches_rule(file_path, rule):
                target_name = rule.get('target_folder', 'Other')
                category_folder = base_folder / target_name
                break
        
        if not category_folder:
            return None
        
        # AI-based semantic grouping level (ALWAYS ENABLED)
        if self.semantic_groups:
            # Find which group this file belongs to (compare as strings)
            file_path_str = str(file_path)
            ai_group_name = None
            for group_name, group_files in self.semantic_groups.items():
                if file_path_str in group_files:
                    ai_group_name = group_name
                    break  # Stop searching once found
            
            # Log result after loop completes
            if ai_group_name:
                logger.debug(f"File {file_path.name} -> AI Group: {ai_group_name}")
                category_folder = category_folder / ai_group_name
            else:
                logger.debug(f"File {file_path.name} not in any AI group")
        
        # Second level: File Type (PDF, DOCX, etc.)
        ext = file_path.suffix.lower().lstrip('.')
        if ext:
            type_folder = category_folder / ext.upper()
        else:
            type_folder = category_folder / "No Extension"
        
        # Third level: Date (Jan-26, Dec-25, etc.)
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            date_folder_name = mtime.strftime('%b-%y')  # e.g., "Jan-26"
            final_folder = type_folder / date_folder_name
        except:
            final_folder = type_folder / "Unknown Date"
        
        return final_folder
    
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
    
    def _get_unique_path_folder(self, path: Path) -> Path:
        """Generate unique path if folder exists."""
        
        if not path.exists():
            return path
        
        counter = 1
        name = path.name
        parent = path.parent
        
        while True:
            new_name = f"{name} ({counter})"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _get_category_from_path(self, target_folder: Path, base_folder: Path) -> str:
        """Extract category name from nested path."""
        try:
            relative = target_folder.relative_to(base_folder)
            parts = relative.parts
            return parts[0] if parts else "Other"
        except:
            return "Other"
    
    def _get_ai_group_for_file(self, file_path: Path) -> Optional[str]:
        """Get AI semantic group name for a file."""
        if not self.semantic_groups:
            return None
        
        file_path_str = str(file_path)
        for group_name, group_files in self.semantic_groups.items():
            if file_path_str in group_files:
                return group_name
        
        return None
