"""
File Organizer Engine

Core logic for analyzing, categorizing, and organizing files.
This is the heart of AutoFolder AI.
"""

import os
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
from .ai_learning import AILearningSystem


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
        
        # AI learning system to track corrections
        self.ai_learning = AILearningSystem(config)
        
        # Duplicate detector for finding duplicate files
        self.duplicate_detector = DuplicateDetector()
        self.duplicates = {}  # Cache for found duplicates
        self.duplicate_action = None  # Action to take on duplicates
        
        # Smart renamer for AI-based filename suggestions
        self.smart_renamer = SmartRenamer(config)
        self.rename_suggestions = {}  # Cache for rename suggestions
    
    @staticmethod
    def safe_stat(file_path: Path, default_size: int = 0, default_mtime: float = None):
        """
        Safely get file stats, handling inaccessible files.
        
        Args:
            file_path: Path to file
            default_size: Default size if stat fails
            default_mtime: Default modification time if stat fails
            
        Returns:
            os.stat_result or None if inaccessible
        """
        try:
            return file_path.stat()
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.debug(f"Cannot access file stats: {file_path} - {e}")
            return None
    
    @staticmethod
    def safe_get_size(file_path: Path, default: int = 0) -> int:
        """
        Safely get file size, handling inaccessible files.
        
        Args:
            file_path: Path to file
            default: Default size if stat fails
            
        Returns:
            File size in bytes or default
        """
        try:
            return file_path.stat().st_size
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.debug(f"Cannot get file size: {file_path} - {e}")
            return default
    
    @staticmethod
    def safe_get_mtime(file_path: Path, default: float = None) -> Optional[float]:
        """
        Safely get file modification time, handling inaccessible files.
        
        Args:
            file_path: Path to file
            default: Default mtime if stat fails
            
        Returns:
            Modification timestamp or default
        """
        try:
            return file_path.stat().st_mtime
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.debug(f"Cannot get file mtime: {file_path} - {e}")
            return default or datetime.now().timestamp()
        
    def analyze_folder(self, folder_path: Path, max_depth: int = None) -> Dict:
        """
        Analyze a folder and return statistics.
        
        Args:
            folder_path: Path to folder to analyze
            max_depth: Maximum depth to scan (0=no limit, 1=root only, etc.)
            
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
        
        # Also collect files from subfolders for total count (with depth limit)
        if max_depth is None:
            max_depth = self.config.get('organization', {}).get('max_depth', 0)
        
        if max_depth == 0:
            # No limit - collect all files
            all_files_recursive = [f for f in folder_path.rglob('*') if f.is_file()]
        else:
            # Limit depth
            all_files_recursive = []
            for f in folder_path.rglob('*'):
                if f.is_file():
                    try:
                        depth = len(f.relative_to(folder_path).parts)
                        if depth <= max_depth:
                            all_files_recursive.append(f)
                    except:
                        pass
        
        file_count = len(all_files_recursive)
        logger.info(f"📊 Found {len(files)} root files, {len(folders)} folders, {file_count} total files (recursive)")
        
        # Progress feedback for large scans
        if file_count > 10000:
            logger.info(f"⚡ Large folder detected: {file_count:,} files - Processing in chunks for better performance")
        
        # Ignore hidden files if configured
        if self.config.get('organization', {}).get('ignore_hidden_files', True):
            files = [f for f in files if not f.name.startswith('.')]
            folders = [f for f in folders if not f.name.startswith('.')]
        
        # Skip common organized folder names to avoid recursive moves
        organized_folder_names = {
            'Documents', 'Images', 'Videos', 'Audio', 'Archives', 
            'Code', 'Installers', 'Gaming', 'Other', 'Compressed', 'AutoFolder_Logs'
        }
        
        # CRITICAL: Define system folders that should NEVER be organized
        CRITICAL_SYSTEM_FOLDERS = [
            # User Profile Folders (CRITICAL - DO NOT ORGANIZE)
            'Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos',
            'AppData', 'Application Data', 'Local Settings',
            'Contacts', 'Favorites', 'Links', 'Saved Games', 'Searches',
            
            # Windows System Folders (CRITICAL - DO NOT ORGANIZE)
            'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
            'System32', 'SysWOW64', '$Recycle.Bin', 'Recovery',
        ]
        
        # Skip common system/app/game folders that should not be organized
        system_folder_patterns = CRITICAL_SYSTEM_FOLDERS + [
            
            # Cloud Storage Folders
            'OneDrive', 'Google Drive', 'Dropbox', 'iCloud Drive',
            'WPS Cloud Files', 'KingsoftData',
            
            # Development Project Folders (CRITICAL - WILL BREAK PROJECTS)
            'node_modules', 'venv', 'env', '.venv', '.env',  # Package folders
            '__pycache__', '.pytest_cache', '.mypy_cache',  # Python cache
            '.git', '.svn', '.hg', '.bzr',  # Version control
            'dist', 'build', '.gradle', '.idea', '.vscode',  # Build outputs & IDE
            'vendor', 'composer', 'bower_components',  # PHP/Web dependencies
            
            # Development Project Indicators (if folder contains these, skip entire folder)
            'pyinstaller', '.gitignore', 'requirements.txt', 'package.json',
            'setup.py', 'pyproject.toml', 'Cargo.toml', 'go.mod',
            
            # Microsoft Office & Apps
            'WindowsPowerShell', 'Custom Office Templates',
            
            # Games (large, complex folder structures)
            'Rockstar Games', 'My Games', 'Steam', 'Epic Games',
            'FIFA', 'FC ', 'WWE', 'GTA', 'Gameloft', 'EA Games',
            'Ubisoft', 'Battle.net', 'Origin Games'
        ]
        
        # AUTOMATIC RESCUE: Check for misplaced system folders and move them back to root
        # This fixes any previous organizations that happened before the protection was added
        rescued = self._rescue_misplaced_system_folders(folder_path, system_folder_patterns[:16])
        if rescued:
            logger.info(f"🛡️ Auto-rescued {len(rescued)} misplaced system folders back to root")
            for folder_name in rescued:
                logger.info(f"   ✓ Rescued: {folder_name}")
        
        # AUTOMATIC RESCUE: Check for misplaced system folders and move them back to root
        # This fixes any previous organizations that happened before the protection was added
        rescued = self._rescue_misplaced_system_folders(folder_path, CRITICAL_SYSTEM_FOLDERS)
        if rescued:
            logger.info(f"🛡️ Auto-rescued {len(rescued)} misplaced system folders back to root")
            for folder_name in rescued:
                logger.info(f"   ✓ Rescued: {folder_name}")
        
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
            
            # Skip development projects (CRITICAL - will break projects if organized)
            if self._is_development_project(folder):
                logger.info(f"🛡️ Skipping development project: {folder.name}")
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
                    # Calculate folder size (safely handle inaccessible files)
                    folder_size = sum(self.safe_get_size(f) for f in folder_files)
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
            'total_size': self._calculate_safe_total_size(all_files_recursive),  # Safe size calculation
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
            
            # By date (month) - safely
            try:
                mtime_timestamp = self.safe_get_mtime(file_path)
                if mtime_timestamp:
                    mtime = datetime.fromtimestamp(mtime_timestamp)
                    month_key = mtime.strftime('%Y-%m')
                    analysis['by_date'][month_key] = analysis['by_date'].get(month_key, 0) + 1
            except Exception as e:
                logger.debug(f"Could not get date for {file_path}: {e}")
            
            # By size - safely
            size = self.safe_get_size(file_path)
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
            
            # Do not pre-create the target folder here; create when moving to avoid empty folders.
            # target_folder.mkdir(parents=True, exist_ok=True)
            
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
                        
                        # Ensure parent exists only when actually moving a file
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(dest))
                        files_moved += 1
                        moved_files.append((str(file_path), str(dest)))
                        logger.info(f"Moved duplicate: {file_path.name} → {dest}")
                    except Exception as e:
                        logger.error(f"Error moving duplicate {file_path}: {e}")
        
        elif action in ['keep_newest', 'keep_oldest']:
            # Delete duplicates based on strategy
            failed_deletes = []
            
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
                        file_size = self.safe_get_size(file_path)
                        file_path.unlink()
                        files_deleted += 1
                        space_freed += file_size
                        deleted_files.append(str(file_path))
                        logger.info(f"Deleted duplicate: {file_path.name}")
                    except PermissionError as e:
                        error_msg = (
                            f"⚠️ Cannot delete '{file_path.name}' - Permission denied. "
                            f"This is likely a OneDrive synced file. "
                            f"Try: 1) Pause OneDrive sync, 2) Close programs using this file, "
                            f"3) Delete manually in File Explorer"
                        )
                        logger.error(error_msg)
                        failed_deletes.append((str(file_path), "OneDrive locked or in use"))
                    except Exception as e:
                        logger.error(f"Error deleting duplicate {file_path}: {e}")
                        failed_deletes.append((str(file_path), str(e)))
        
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
            'kept_files': kept_files,
            'failed_deletes': failed_deletes if 'failed_deletes' in locals() else []
        }
    
    def preview_organization(
        self, 
        folder_path: Path, 
        profile: str = None,
        custom_rules: List[Dict] = None,
        max_depth: int = None,
        progress_callback = None
    ) -> List[Dict]:
        """
        Preview what organization will do without making changes.
        AI semantic grouping is ALWAYS enabled.
        
        Args:
            folder_path: Folder to organize
            profile: Profile name to use (e.g., 'downloads', 'media')
            custom_rules: Custom rule list
            max_depth: Maximum folder depth to organize (0=no limit)
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of planned operations
        """
        logger.info(f"Generating preview for: {folder_path}")
        
        # Notify user we're indexing
        if progress_callback:
            try:
                progress_callback(0, 1, status="🔍 Indexing files in folder...")
            except:
                pass
        
        analysis = self.analyze_folder(folder_path, max_depth=max_depth)
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
            
            # Notify user about AI grouping phase
            if progress_callback:
                try:
                    progress_callback(0, 1, status="🤖 AI is creating semantic groups...")
                except:
                    pass
            
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
                
                # Smart rename disabled - keep original filename
                suggested_name = file_path.name
                
                target_path = target_folder / suggested_name
                
                # Handle conflicts
                if target_path.exists():
                    conflict_resolution = self.config.get('organization', {}).get('handle_conflicts', 'rename')
                    if conflict_resolution == 'rename':
                        target_path = self._get_unique_path(target_path)
                        if target_path is None:  # Conflict - skip this file
                            logger.info(f"Skipping {file_path.name} due to conflict")
                            continue
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
                    'size': self.safe_get_size(file_path),
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
                            if target_path is None:  # Conflict detected - skip this folder
                                logger.info(f"Skipping folder {folder_path_item.name} due to conflict")
                                continue
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
        
        # Build list of folders that will be moved (to avoid moving their contents twice)
        folders_being_moved = {op['source'] for op in operations if op.get('is_folder', False)}
        
        # Also preview files from subfolders (for display purposes)
        organized_folder_names = {
            'Documents', 'Images', 'Videos', 'Audio', 'Archives', 
            'Code', 'Installers', 'Gaming', 'Other', 'Compressed'
        }
        system_folder_patterns = [
            # Windows System Folders (CRITICAL - DO NOT ORGANIZE)
            'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
            'System32', 'SysWOW64', '$Recycle.Bin', 'Recovery',
            
            # User Profile Folders (CRITICAL - DO NOT ORGANIZE)
            'Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos',
            'AppData', 'Application Data', 'Local Settings',
            'Contacts', 'Favorites', 'Links', 'Saved Games', 'Searches',
            
            # Cloud Storage Folders
            'OneDrive', 'Google Drive', 'Dropbox', 'iCloud Drive',
            'WPS Cloud Files', 'KingsoftData',
            
            # Development Project Folders (CRITICAL - WILL BREAK PROJECTS)
            'node_modules', 'venv', 'env', '.venv', '.env',
            '__pycache__', '.pytest_cache', '.mypy_cache',
            '.git', '.svn', '.hg', '.bzr',
            'dist', 'build', '.gradle', '.idea', '.vscode',
            'vendor', 'composer', 'bower_components',
            
            # Microsoft Office & Apps
            'WindowsPowerShell', 'Custom Office Templates',
            
            # Games (large, complex folder structures)
            'Rockstar Games', 'My Games', 'Steam', 'Epic Games',
            'FIFA', 'FC ', 'WWE', 'GTA', 'Gameloft', 'EA Games',
            'Ubisoft', 'Battle.net', 'Origin Games',
            
            # Development markers
            'pyinstaller', '.gitignore', 'requirements.txt', 'package.json'
        ]
        
        # Find subfolder files to include in preview
        for subfolder_file in folder_path.rglob('*'):
            if not subfolder_file.is_file():
                continue
            
            # Skip if it's a root file (already processed)
            if subfolder_file.parent == folder_path:
                continue
            
            # ✅ CRITICAL FIX: Skip files inside folders that are being moved as a whole unit
            # If the parent folder is in folders_being_moved, the file will be moved with it
            skip_due_to_parent_move = False
            for moving_folder in folders_being_moved:
                try:
                    subfolder_file.relative_to(moving_folder)
                    # If we get here, subfolder_file is inside moving_folder
                    skip_due_to_parent_move = True
                    logger.debug(f"Skipping {subfolder_file.name} - parent folder {moving_folder.name} is being moved")
                    break
                except ValueError:
                    # subfolder_file is not inside moving_folder, continue checking
                    continue
            
            if skip_due_to_parent_move:
                continue
            
            # Skip if in system/app folder or development project
            skip_this_file = False  # Initialize the variable
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
                        if target_path is None:  # Conflict detected - skip this file
                            logger.info(f"Skipping {subfolder_file.name} due to conflict")
                            continue
                    elif conflict_resolution == 'skip':
                        continue
                
                operations.append({
                    'source': subfolder_file,
                    'target': target_path,
                    'action': 'move',
                    'category': self._get_category_from_path(target_folder, folder_path),
                    'size': self.safe_get_size(subfolder_file),
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
        recursive: bool = True,
        max_depth: int = None,
        progress_callback=None
    ) -> Dict:
        """
        Organize files in a folder based on rules.
        
        Args:
            folder_path: Folder to organize
            profile: Profile name to use
            custom_rules: Custom rule list
            dry_run: If True, don't actually move files
            recursive: If True, also organize subfolders
            max_depth: Maximum folder depth to organize (0=no limit)
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Dictionary with results
        """
        if dry_run is None:
            dry_run = self.dry_run
        
        depth_info = f" (max depth: {max_depth})" if max_depth and max_depth > 0 else ""
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Organizing folder: {folder_path} {'(recursive)' if recursive else ''}{depth_info}")
        
        # Get preview of operations (returns tuple: operations, stats)
        result = self.preview_organization(folder_path, profile, custom_rules, max_depth=max_depth)
        
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
        total = len(operations)
        chunk_size = self.config.get('organization', {}).get('progress_chunk_size', 10)  # Update every 10 files
        
        logger.info(f"🚀 Starting organization: {total:,} operations to process")
        
        # Emit initial status
        if progress_callback:
            try:
                progress_callback(0, total, status="📦 Starting file organization...")
            except:
                pass
        
        for i, op in enumerate(operations, 1):
            # Emit detailed progress status messages
            if progress_callback:
                try:
                    # Show which file is being processed
                    file_name = op['source'].name[:30]  # Truncate long names
                    if len(op['source'].name) > 30:
                        file_name += "..."
                    
                    category = op.get('category', 'Other')
                    progress_callback(i, total, status=f"📁 Moving: {file_name} → {category}")
                except Exception as e:
                    logger.debug(f"Progress callback error: {e}")
            
            # Log progress at chunks for performance
            if i == 1 or i == total or i % chunk_size == 0:
                percent = int(i/total*100)
                logger.info(f"📊 Progress: {i:,}/{total:,} ({percent}%) - {len(completed)} completed, {len(failed)} failed")
            try:
                # Safety check: Skip if target is None or invalid
                if not op.get('target') or op['target'] is None:
                    logger.warning(f"Skipping {op['source'].name}: No valid target path")
                    op['status'] = 'skipped'
                    op['error'] = 'No valid target path'
                    failed.append(op)
                    continue
                
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
            if progress_callback:
                try:
                    progress_callback(total, total, status="💾 Saving undo history...")
                except:
                    pass
            
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
        
        # Track in AI learning system
        ai_group_count = len(self.semantic_groups) if self.semantic_groups else 0
        self.ai_learning.record_organization(len(completed), ai_group_count)
        logger.info(f"AI Learning: Recorded {len(completed)} files organized, {ai_group_count} AI groups")
        
        # Customize folder icons (Windows only)
        logger.debug(f"🎨 FOLDER ICONS: Checking if should create icons...")
        logger.debug(f"   - Completed operations: {len(completed)}")
        logger.debug(f"   - OS name: {os.name}")
        logger.debug(f"   - Is Windows: {os.name == 'nt'}")
        
        if completed and os.name == 'nt':
            logger.info("🎨 FOLDER ICONS: Attempting to create Windows folder icons...")
            
            # Notify UI that we're customizing folder icons
            if progress_callback:
                try:
                    progress_callback(total, total, status="🎨 Customizing folder icons...")
                except Exception as e:
                    logger.debug(f"Progress callback error: {e}")
            
            try:
                # Fix import - use absolute import instead of relative
                logger.debug("   - Importing WindowsFolderIconCustomizer...")
                from utils.windows_folder_icons import WindowsFolderIconCustomizer
                logger.debug("   - Import successful!")
                
                logger.debug("   - Creating icon customizer instance...")
                icon_customizer = WindowsFolderIconCustomizer()
                logger.debug("   - Icon customizer created!")
                
                # Get unique folder paths from completed operations
                # Extract top-level category folders (e.g., Documents/Archives, not Documents/Archives/ZIP/Jan-26)
                category_folders = {}
                logger.debug(f"   - Collecting category folders from {len(completed)} completed operations...")
                logger.debug(f"   - Base folder: {folder_path}")
                
                for op in completed:
                    target = op.get('target')
                    category = op.get('category', 'Other')
                    
                    logger.debug(f"     • Processing op: category={category}, target={target}")
                    
                    if target:
                        try:
                            # Convert to Path if it's a string
                            if isinstance(target, str):
                                target = Path(target)
                                logger.debug(f"       - Converted string to Path: {target}")
                            
                            if not isinstance(target, Path):
                                logger.debug(f"       ⚠️ Invalid target type: {type(target)}")
                                continue
                            # Get relative path from base folder to target
                            rel_path = target.relative_to(folder_path)
                            logger.debug(f"       - Relative path: {rel_path}")
                            logger.debug(f"       - Path parts: {rel_path.parts}")
                            
                            # First component is the category folder (e.g., "Archives" or "Documents")
                            category_folder_name = rel_path.parts[0]
                            logger.debug(f"       - Category folder name: {category_folder_name}")
                            
                            # Construct full category folder path
                            category_folder_path = folder_path / category_folder_name
                            logger.debug(f"       - Full category path: {category_folder_path}")
                            
                            # Add to dict if not already present
                            if category not in category_folders:
                                category_folders[category] = category_folder_path
                                logger.debug(f"       ✅ Added: {category} -> {category_folder_path}")
                            else:
                                logger.debug(f"       ⏭️ Already exists: {category}")
                            
                        except (ValueError, IndexError) as e:
                            logger.debug(f"       ❌ Skipped {target}: {e}")
                    else:
                        logger.debug(f"       ⚠️ Invalid target: {target} (type: {type(target)})")
                
                logger.info(f"   - Found {len(category_folders)} unique category folders to customize")
                logger.debug(f"   - Categories: {list(category_folders.keys())}")
                
                # Set icons for all category folders
                logger.info("   - Calling customize_organized_folders()...")
                icon_count = icon_customizer.customize_organized_folders(folder_path, category_folders)
                logger.info(f"✅ FOLDER ICONS: Successfully customized {icon_count} folder icons!")
            except ImportError as e:
                logger.error(f"❌ FOLDER ICONS: Import error - {e}")
                logger.debug(f"   - Full error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"❌ FOLDER ICONS: Could not customize folder icons - {e}")
                logger.debug(f"   - Full error: {e}", exc_info=True)
        elif not completed:
            logger.debug("   - SKIPPED: No completed operations")
        elif os.name != 'nt':
            logger.debug(f"   - SKIPPED: Not Windows (os.name={os.name})")
        
        
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
        """Determine target folder with multi-level sorting (Category → AI Group → Type).
        AI semantic grouping is ALWAYS applied when available.
        Date subfolders REMOVED for simpler navigation."""
        
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
        
        # Return type folder directly (NO DATE SUBFOLDER for simpler navigation)
        return type_folder
    
    def _get_unique_path(self, path: Path) -> Path:
        """Generate unique path if file exists - NO LONGER ADDS (1) AUTOMATICALLY.
        Returns the original path and logs a warning. User must handle conflicts."""
        
        if not path.exists():
            return path
        
        # CHANGED: Do NOT auto-rename. Return original path and warn.
        logger.warning(f"⚠️ CONFLICT: Target already exists: {path.name}")
        logger.warning(f"   This file will be SKIPPED to avoid adding (1) (2) (3) numbers")
        logger.warning(f"   Please manually rename or delete the existing file first")
        return None  # Return None to signal conflict - caller should skip this file
    
    def _get_unique_path_folder(self, path: Path) -> Path:
        """Generate unique path if folder exists - NO LONGER ADDS (1) AUTOMATICALLY.
        Returns None if folder exists to avoid (1) (2) (3) suffixes."""
        
        if not path.exists():
            return path
        
        # CHANGED: Do NOT auto-rename folders. Return None and warn.
        logger.warning(f"⚠️ CONFLICT: Target folder already exists: {path.name}")
        logger.warning(f"   This folder will be SKIPPED to avoid adding (1) (2) (3) numbers")
        return None  # Return None to signal conflict - caller should skip
    
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
    
    def _calculate_safe_total_size(self, files: list) -> int:
        """
        Safely calculate total size of files, skipping inaccessible ones.
        
        Args:
            files: List of Path objects
            
        Returns:
            Total size in bytes
        """
        return sum(self.safe_get_size(f) for f in files)
    
    def _rescue_misplaced_system_folders(self, root_path: Path, system_folders: list) -> list:
        """
        Automatically rescue system folders that were incorrectly moved into category folders.
        This fixes organizations that happened before system folder protection was added.
        
        Args:
            root_path: Root folder being organized (e.g., D:\\)
            system_folders: List of critical system folder names
            
        Returns:
            List of folder names that were rescued
        """
        rescued = []
        category_folders = ['Code', 'Documents', 'Images', 'Videos', 'Audio', 'Archives', 
                           'Installers', 'Gaming', 'Other', 'Compressed', 'Databases']
        
        try:
            for category in category_folders:
                category_path = root_path / category
                if not category_path.exists() or not category_path.is_dir():
                    continue
                
                # Check all subdirectories in this category folder
                for item in category_path.iterdir():
                    if not item.is_dir():
                        continue
                    
                    # Check if this is a misplaced system folder
                    if item.name in system_folders:
                        target = root_path / item.name
                        
                        # If target already exists at root, skip (avoid conflicts)
                        if target.exists():
                            logger.warning(f"Cannot rescue {item.name}: already exists at root")
                            continue
                        
                        try:
                            # Move the entire folder back to root
                            logger.info(f"🚨 Rescuing misplaced system folder: {item.name} from {category}/")
                            shutil.move(str(item), str(target))
                            rescued.append(item.name)
                        except Exception as e:
                            logger.error(f"Failed to rescue {item.name}: {e}")
                            
        except Exception as e:
            logger.error(f"Error during system folder rescue: {e}")
        
        return rescued
    
    def _is_development_project(self, folder_path: Path) -> bool:
        """
        Check if a folder is a development project.
        Returns True if folder contains project marker files/folders.
        """
        # Project marker files that indicate a development project
        project_markers = [
            # Python
            'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock',
            'setup.cfg', 'tox.ini', 'pytest.ini', 'manage.py',
            
            # JavaScript/Node.js
            'package.json', 'package-lock.json', 'yarn.lock', 'npm-shrinkwrap.json',
            'webpack.config.js', 'gulpfile.js', 'gruntfile.js',
            
            # Other languages
            'Cargo.toml', 'Cargo.lock',  # Rust
            'go.mod', 'go.sum',  # Go
            'composer.json', 'composer.lock',  # PHP
            'Gemfile', 'Gemfile.lock',  # Ruby
            'build.gradle', 'pom.xml',  # Java
            'CMakeLists.txt', 'Makefile',  # C/C++
            
            # Version control
            '.gitignore', '.gitattributes',
            
            # IDE/Editor configs
            '.editorconfig', 'tsconfig.json', 'jsconfig.json'
        ]
        
        # Project marker folders
        project_folders = [
            'venv', 'env', '.venv', '.env', 'virtualenv',
            'node_modules', '__pycache__', '.git', '.svn',
            'dist', 'build', 'target', 'out',
            '.idea', '.vscode', '.vs'
        ]
        
        # Check for marker files in root of folder
        try:
            for marker in project_markers:
                if (folder_path / marker).exists():
                    logger.info(f"🛡️ Protected: '{folder_path.name}' is a development project (found {marker})")
                    return True
            
            # Check for marker folders
            for marker_folder in project_folders:
                if (folder_path / marker_folder).exists():
                    logger.info(f"🛡️ Protected: '{folder_path.name}' is a development project (found {marker_folder}/)")
                    return True
        except Exception as e:
            logger.debug(f"Error checking if {folder_path} is dev project: {e}")
        
        return False
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during processing."""
        # Skip hidden files if configured
        if self.config.get('organization', {}).get('ignore_hidden_files', True):
            if file_path.name.startswith('.'):
                return True
        
        # Skip system files
        if file_path.name in ['desktop.ini', 'Thumbs.db', '.DS_Store']:
            return True
        
        return False
