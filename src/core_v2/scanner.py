"""
AutoFolder AI v2.0 - Deep Scanner

Single-pass recursive scanner that builds complete FileNode tree.
Handles errors gracefully, detects symlink loops, respects permissions.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Set, Callable
from datetime import datetime

from .models import FileNode

logger = logging.getLogger(__name__)


class DeepScanner:
    """
    Deep filesystem scanner.
    
    Builds complete FileNode tree in single recursive pass.
    Much faster than v1's multi-pass approach.
    """
    
    def __init__(
        self,
        follow_symlinks: bool = False,
        max_depth: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ):
        """
        Initialize scanner.
        
        Args:
            follow_symlinks: Follow symbolic links (dangerous, can loop)
            max_depth: Maximum depth to scan (None = unlimited)
            progress_callback: Optional callback(files_scanned, current_path)
        """
        self.follow_symlinks = follow_symlinks
        self.max_depth = max_depth
        self.progress_callback = progress_callback
        
        # Track visited inodes to detect symlink loops
        self._visited_inodes: Set[tuple] = set()
        
        # Statistics
        self._files_scanned = 0
        self._dirs_scanned = 0
        self._errors = 0
        self._skipped_permission = 0
        self._skipped_symlink = 0
    
    def scan(self, root_path: Path) -> FileNode:
        """
        Scan directory tree and build FileNode structure.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            FileNode representing entire tree
            
        Raises:
            ValueError: If root_path doesn't exist or isn't a directory
        """
        if not root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
        
        logger.info(f"Starting deep scan of: {root_path}")
        start_time = datetime.now()
        
        # Reset statistics
        self._files_scanned = 0
        self._dirs_scanned = 0
        self._errors = 0
        self._visited_inodes.clear()
        
        # Build tree
        try:
            root_node = self._scan_recursive(root_path, depth=0, parent=None)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Scan complete: {self._files_scanned} files, "
                f"{self._dirs_scanned} dirs in {elapsed:.2f}s"
            )
            logger.info(
                f"Errors: {self._errors}, "
                f"Skipped (permission): {self._skipped_permission}, "
                f"Skipped (symlink): {self._skipped_symlink}"
            )
            
            return root_node
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise
    
    def _scan_recursive(
        self,
        path: Path,
        depth: int,
        parent: Optional[FileNode]
    ) -> FileNode:
        """
        Recursively scan directory.
        
        Args:
            path: Current path
            depth: Current depth from root
            parent: Parent FileNode
            
        Returns:
            FileNode for this path
        """
        # Check depth limit
        if self.max_depth is not None and depth > self.max_depth:
            logger.debug(f"Max depth reached at: {path}")
            # Return directory node without children
            return self._create_node(path, depth, parent, children=tuple())
        
        # Progress callback
        if self.progress_callback and self._files_scanned % 100 == 0:
            self.progress_callback(self._files_scanned, str(path))
        
        # Check for symlink loops (if following symlinks)
        if self.follow_symlinks:
            try:
                stat = path.stat()
                inode_key = (stat.st_dev, stat.st_ino)
                if inode_key in self._visited_inodes:
                    logger.warning(f"Symlink loop detected at: {path}")
                    self._skipped_symlink += 1
                    return self._create_node(path, depth, parent, children=tuple())
                self._visited_inodes.add(inode_key)
            except OSError as e:
                logger.warning(f"Cannot stat {path}: {e}")
                self._errors += 1
                return self._create_node(path, depth, parent, children=tuple())
        
        # Scan directory contents
        try:
            # Use os.scandir for performance (faster than Path.iterdir)
            children = []
            
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        entry_path = Path(entry.path)
                        
                        # Skip if symlink and not following
                        if entry.is_symlink() and not self.follow_symlinks:
                            logger.debug(f"Skipping symlink: {entry_path}")
                            self._skipped_symlink += 1
                            continue
                        
                        # Recurse into directories
                        if entry.is_dir(follow_symlinks=self.follow_symlinks):
                            child_node = self._scan_recursive(
                                entry_path,
                                depth + 1,
                                None  # Will set parent after
                            )
                            children.append(child_node)
                            self._dirs_scanned += 1
                        
                        # Add files
                        elif entry.is_file(follow_symlinks=self.follow_symlinks):
                            child_node = self._create_file_node(
                                entry_path,
                                entry,
                                depth + 1,
                                None
                            )
                            children.append(child_node)
                            self._files_scanned += 1
                    
                    except PermissionError:
                        logger.debug(f"Permission denied: {entry.path}")
                        self._skipped_permission += 1
                    except OSError as e:
                        logger.warning(f"Error scanning {entry.path}: {e}")
                        self._errors += 1
            
            # Create directory node with children
            return self._create_node(path, depth, parent, children=tuple(children))
        
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
            self._skipped_permission += 1
            return self._create_node(path, depth, parent, children=tuple())
        
        except OSError as e:
            logger.error(f"Error scanning {path}: {e}")
            self._errors += 1
            return self._create_node(path, depth, parent, children=tuple())
    
    def _create_node(
        self,
        path: Path,
        depth: int,
        parent: Optional[FileNode],
        children: tuple
    ) -> FileNode:
        """Create directory FileNode."""
        try:
            stat = path.stat()
            size = stat.st_size
            mtime = stat.st_mtime
        except OSError:
            size = 0
            mtime = 0.0
        
        return FileNode(
            path=path,
            is_dir=True,
            size=size,
            mtime=mtime,
            parent=parent,
            children=children,
            depth=depth,
            root_distance=0  # Will be calculated later if needed
        )
    
    def _create_file_node(
        self,
        path: Path,
        entry: os.DirEntry,
        depth: int,
        parent: Optional[FileNode]
    ) -> FileNode:
        """Create file FileNode from os.DirEntry (faster)."""
        try:
            stat = entry.stat(follow_symlinks=self.follow_symlinks)
            size = stat.st_size
            mtime = stat.st_mtime
        except OSError:
            size = 0
            mtime = 0.0
        
        return FileNode(
            path=path,
            is_dir=False,
            size=size,
            mtime=mtime,
            parent=parent,
            children=tuple(),  # Files have no children
            depth=depth,
            root_distance=0
        )
    
    @property
    def statistics(self) -> dict:
        """Get scan statistics."""
        return {
            'files_scanned': self._files_scanned,
            'dirs_scanned': self._dirs_scanned,
            'errors': self._errors,
            'skipped_permission': self._skipped_permission,
            'skipped_symlink': self._skipped_symlink
        }


# Convenience function
def scan_folder(
    path: Path,
    max_depth: Optional[int] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> FileNode:
    """
    Convenience function to scan a folder.
    
    Args:
        path: Path to scan
        max_depth: Maximum depth (None = unlimited)
        progress_callback: Optional progress callback
        
    Returns:
        FileNode representing tree
    """
    scanner = DeepScanner(
        follow_symlinks=False,  # Never follow symlinks for safety
        max_depth=max_depth,
        progress_callback=progress_callback
    )
    return scanner.scan(path)
