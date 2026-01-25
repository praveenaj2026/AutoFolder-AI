"""
Smart Compressor - Compress old and large files to save storage space.

Phase 3.7 Feature: Auto-compress files based on age, size, or category.
"""

import logging
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class SmartCompressor:
    """
    Smart file compression for storage optimization.
    
    Features:
    - Compress files older than X months
    - Compress files larger than X MB
    - Group compression by category or AI group
    - Multiple compression formats (zip, 7z)
    """
    
    # Extensions that shouldn't be compressed (already compressed or binary)
    SKIP_EXTENSIONS = {
        '.zip', '.7z', '.rar', '.gz', '.tar', '.bz2', '.xz',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mkv',
        '.mp3', '.aac', '.flac', '.exe', '.dll', '.msi'
    }
    
    def __init__(self, config: Dict = None):
        """
        Initialize smart compressor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.compression_config = self.config.get('compression', {})
        
        # Settings
        self.enabled = self.compression_config.get('enabled', True)
        self.age_months = self.compression_config.get('criteria', {}).get('age_months', 6)
        self.size_mb = self.compression_config.get('criteria', {}).get('size_mb', 100)
        self.method = self.compression_config.get('method', 'zip')
        self.level = self.compression_config.get('level', 'normal')
        self.keep_originals = self.compression_config.get('keep_originals', True)
        self.archive_location = self.compression_config.get('archive_location', 'Archives')
        
        # Check for 7z support
        self._7z_available = False
        self._check_7z_support()
        
        logger.info(f"SmartCompressor initialized: method={self.method}, 7z_available={self._7z_available}")
    
    def _check_7z_support(self):
        """Check if py7zr is available for 7z compression."""
        try:
            import py7zr
            self._7z_available = True
        except ImportError:
            logger.info("py7zr not installed. Using ZIP compression. Install with: pip install py7zr")
    
    def find_compressible_files(
        self, 
        folder: Path, 
        days_old: int = None,
        min_size_mb: float = None
    ) -> List[Dict]:
        """
        Find files that are good candidates for compression.
        
        Args:
            folder: Root folder to scan
            days_old: Minimum age in days (files older than this)
            min_size_mb: Minimum size in MB (files larger than this)
            
        Returns:
            List of file info dictionaries
        """
        if days_old is None:
            days_old = self.age_months * 30  # Convert default months to days
        if min_size_mb is None:
            min_size_mb = self.size_mb
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        min_size_bytes = min_size_mb * 1024 * 1024
        
        compressible = []
        
        try:
            for file_path in folder.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Skip already compressed files
                if file_path.suffix.lower() in self.SKIP_EXTENSIONS:
                    continue
                
                # Skip files in Archives folder
                if self.archive_location in file_path.parts:
                    continue
                
                try:
                    stat = file_path.stat()
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    size_bytes = stat.st_size
                    
                    # Check criteria - file must be BOTH old AND large
                    is_old = modified_time < cutoff_date
                    is_large = size_bytes >= min_size_bytes
                    
                    if is_old and is_large:
                        compressible.append({
                            'path': file_path,
                            'name': file_path.name,
                            'size_bytes': size_bytes,
                            'size_mb': size_bytes / (1024 * 1024),
                            'modified': modified_time,
                            'age_days': (datetime.now() - modified_time).days,
                            'is_old': is_old,
                            'is_large': is_large,
                            'category': self._get_category(file_path)
                        })
                except (PermissionError, OSError) as e:
                    logger.debug(f"Cannot access {file_path}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scanning for compressible files: {e}")
        
        # Sort by size (largest first)
        compressible.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        logger.info(f"Found {len(compressible)} compressible files in {folder}")
        return compressible
    
    def _get_category(self, file_path: Path) -> str:
        """Get file category from extension."""
        ext = file_path.suffix.lower()
        
        categories = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
            'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h'],
            'Data': ['.csv', '.json', '.xml', '.sql', '.db']
        }
        
        for category, extensions in categories.items():
            if ext in extensions:
                return category
        
        return 'Other'
    
    def analyze_compression_potential(self, files: List[Dict]) -> Dict:
        """
        Analyze potential space savings from compression.
        
        Args:
            files: List of file info from find_compressible_files
            
        Returns:
            Analysis summary
        """
        if not files:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'estimated_savings_mb': 0,
                'by_category': {}
            }
        
        total_size = sum(f['size_bytes'] for f in files)
        
        # Estimate compression ratios by category
        compression_ratios = {
            'Documents': 0.7,  # 70% size after compression (30% savings)
            'Code': 0.3,       # Code compresses very well
            'Data': 0.4,       # Data compresses well
            'Images': 0.95,    # Already compressed, minimal savings
            'Videos': 0.98,    # Already compressed
            'Audio': 0.95,     # Already compressed
            'Other': 0.7
        }
        
        by_category = {}
        estimated_after = 0
        
        for f in files:
            cat = f['category']
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'size_mb': 0}
            
            by_category[cat]['count'] += 1
            by_category[cat]['size_mb'] += f['size_mb']
            
            ratio = compression_ratios.get(cat, 0.7)
            estimated_after += f['size_bytes'] * ratio
        
        return {
            'total_files': len(files),
            'total_size_mb': total_size / (1024 * 1024),
            'estimated_after_mb': estimated_after / (1024 * 1024),
            'estimated_savings_mb': (total_size - estimated_after) / (1024 * 1024),
            'savings_percent': ((total_size - estimated_after) / total_size * 100) if total_size > 0 else 0,
            'by_category': by_category
        }
    
    def compress_files(
        self, 
        files: List[Path], 
        archive_name: str,
        output_folder: Path,
        delete_originals: bool = False,
        progress_callback = None
    ) -> Dict:
        """
        Compress multiple files into a single archive.
        
        Args:
            files: List of file paths to compress
            archive_name: Name for the archive (without extension)
            output_folder: Where to save the archive
            delete_originals: Whether to delete original files after compression
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Result dictionary with stats
        """
        if not files:
            return {'success': False, 'error': 'No files to compress'}
        
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate readable archive name with date/time
        # Format: AutoFolder_AI_Archive_25Jan_9PM
        now = datetime.now()
        readable_date = now.strftime('%d%b_%I%p').replace('AM', 'AM').replace('PM', 'PM')
        
        # Clean archive name and add readable timestamp
        clean_name = archive_name.replace('_20', '_').split('_')[0]  # Remove numeric timestamps
        readable_name = f"AutoFolder_AI_{clean_name}_{readable_date}"
        
        # Determine archive path
        if self.method == '7z' and self._7z_available:
            archive_path = output_folder / f"{readable_name}.7z"
        else:
            archive_path = output_folder / f"{readable_name}.zip"
        
        # Handle existing archive - add seconds if duplicate
        if archive_path.exists():
            seconds = now.strftime('%S')
            if self.method == '7z' and self._7z_available:
                archive_path = output_folder / f"{readable_name}_{seconds}s.7z"
            else:
                archive_path = output_folder / f"{readable_name}_{seconds}s.zip"
        
        original_size = 0
        compressed_count = 0
        failed = []
        
        try:
            if self.method == '7z' and self._7z_available:
                # Use py7zr for 7z compression
                import py7zr
                
                with py7zr.SevenZipFile(str(archive_path), 'w') as archive:
                    for i, file_path in enumerate(files):
                        if progress_callback:
                            progress_callback(i + 1, len(files), file_path.name)
                        
                        try:
                            original_size += file_path.stat().st_size
                            archive.write(file_path, file_path.name)
                            compressed_count += 1
                            
                            if delete_originals and not self.keep_originals:
                                file_path.unlink()
                                
                        except Exception as e:
                            logger.error(f"Failed to compress {file_path.name}: {e}")
                            failed.append((str(file_path), str(e)))
            else:
                # Use zipfile for ZIP compression
                compression = zipfile.ZIP_DEFLATED
                if self.level == 'fast':
                    compresslevel = 1
                elif self.level == 'maximum':
                    compresslevel = 9
                else:
                    compresslevel = 6
                
                with zipfile.ZipFile(archive_path, 'w', compression, compresslevel=compresslevel) as archive:
                    for i, file_path in enumerate(files):
                        if progress_callback:
                            progress_callback(i + 1, len(files), file_path.name)
                        
                        try:
                            original_size += file_path.stat().st_size
                            archive.write(file_path, file_path.name)
                            compressed_count += 1
                            
                            if delete_originals and not self.keep_originals:
                                file_path.unlink()
                                
                        except Exception as e:
                            logger.error(f"Failed to compress {file_path.name}: {e}")
                            failed.append((str(file_path), str(e)))
            
            # Get compressed size
            compressed_size = archive_path.stat().st_size
            
            result = {
                'success': True,
                'archive_path': str(archive_path),
                'archive_name': archive_path.name,
                'files_compressed': compressed_count,
                'files_failed': len(failed),
                'failed_files': failed,
                'original_size_mb': original_size / (1024 * 1024),
                'compressed_size_mb': compressed_size / (1024 * 1024),
                'savings_mb': (original_size - compressed_size) / (1024 * 1024),
                'compression_ratio': compressed_size / original_size if original_size > 0 else 1
            }
            
            logger.info(
                f"Compression complete: {compressed_count} files → {archive_path.name} "
                f"({result['original_size_mb']:.1f} MB → {result['compressed_size_mb']:.1f} MB, "
                f"saved {result['savings_mb']:.1f} MB)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'files_compressed': compressed_count,
                'failed_files': failed
            }
    
    def compress_by_category(
        self, 
        folder: Path,
        categories: List[str] = None,
        progress_callback = None
    ) -> List[Dict]:
        """
        Compress files grouped by category.
        
        Args:
            folder: Root folder to scan
            categories: Specific categories to compress (None = all)
            progress_callback: Progress callback
            
        Returns:
            List of compression results
        """
        files = self.find_compressible_files(folder)
        
        if not files:
            return []
        
        # Group by category
        by_category = {}
        for f in files:
            cat = f['category']
            if categories and cat not in categories:
                continue
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f['path'])
        
        # Compress each category
        results = []
        archive_folder = folder / self.archive_location
        
        for category, file_list in by_category.items():
            if len(file_list) < 2:  # Skip if only 1 file
                continue
            
            timestamp = datetime.now().strftime('%Y-%m')
            archive_name = f"{category}_Archive_{timestamp}"
            
            result = self.compress_files(
                file_list, 
                archive_name, 
                archive_folder,
                progress_callback=progress_callback
            )
            result['category'] = category
            results.append(result)
        
        return results
    
    def extract_archive(self, archive_path: Path, output_folder: Path = None) -> Dict:
        """
        Extract files from an archive.
        
        Args:
            archive_path: Path to archive file
            output_folder: Where to extract (None = same folder as archive)
            
        Returns:
            Result dictionary
        """
        if output_folder is None:
            output_folder = archive_path.parent / archive_path.stem
        
        output_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            if archive_path.suffix.lower() == '.7z':
                if not self._7z_available:
                    return {'success': False, 'error': 'py7zr not installed'}
                
                import py7zr
                with py7zr.SevenZipFile(str(archive_path), 'r') as archive:
                    archive.extractall(str(output_folder))
                    extracted = archive.getnames()
            else:
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    archive.extractall(output_folder)
                    extracted = archive.namelist()
            
            return {
                'success': True,
                'output_folder': str(output_folder),
                'files_extracted': len(extracted),
                'files': extracted
            }
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        """Get compressor status."""
        return {
            'enabled': self.enabled,
            'method': self.method,
            '7z_available': self._7z_available,
            'age_months': self.age_months,
            'size_mb_threshold': self.size_mb,
            'keep_originals': self.keep_originals
        }


# Standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    compressor = SmartCompressor()
    print(f"Status: {compressor.get_status()}")
    
    # Test finding compressible files
    test_folder = Path(r"C:\Users\Praveen\OneDrive\Documents")
    if test_folder.exists():
        files = compressor.find_compressible_files(test_folder, days_old=365, min_size_mb=1)
        print(f"\nFound {len(files)} compressible files")
        
        analysis = compressor.analyze_compression_potential(files)
        print(f"Analysis: {analysis}")
