"""
Compression Dialog - UI for Smart Compression feature.

Phase 3.7: Compress old/large files to save storage space.

**THEME RULE - CRITICAL:**
NEVER use default QMessageBox (white background).
ALWAYS use ThemeHelper.style_message_box() with blue theme (#EFF6FF).
ALL dialogs, progress bars, and message boxes MUST use blue theme.
NO white/black/grey dialogs allowed anywhere in the application.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar, QSpinBox, QComboBox,
    QCheckBox, QHeaderView, QMessageBox, QFileDialog, QSplitter,
    QWidget, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

try:
    from ..core.compressor import SmartCompressor
    from .theme_helper import ThemeHelper
except ImportError:
    from core.compressor import SmartCompressor

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Worker thread for scanning files."""
    
    progress = Signal(int, str)
    finished = Signal(list, dict)
    error = Signal(str)
    
    def __init__(self, compressor: SmartCompressor, folder: Path, 
                 days_old: int, min_size_mb: float):
        super().__init__()
        self.compressor = compressor
        self.folder = folder
        self.days_old = days_old
        self.min_size_mb = min_size_mb
    
    def run(self):
        try:
            logger.info(f"Compression scan started: folder={self.folder}, days_old={self.days_old}, min_size_mb={self.min_size_mb}")
            self.progress.emit(10, "Scanning for compressible files...")
            
            # Find compressible files
            files = self.compressor.find_compressible_files(
                folder=self.folder,
                days_old=self.days_old,
                min_size_mb=self.min_size_mb
            )
            
            logger.info(f"Compression scan found {len(files)} files matching criteria")
            self.progress.emit(60, f"Analyzing {len(files)} files...")
            
            # Analyze potential savings
            analysis = self.compressor.analyze_compression_potential(files)
            logger.info(f"Compression analysis: {analysis}")
            
            self.progress.emit(100, "Scan complete")
            self.finished.emit(files, analysis)
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            self.error.emit(str(e))


class CompressWorker(QThread):
    """Worker thread for compression."""
    
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, compressor: SmartCompressor, files: List[Path],
                 output_folder: Path, method: str, by_category: bool):
        super().__init__()
        self.compressor = compressor
        self.files = files
        self.output_folder = output_folder
        self.method = method
        self.by_category = by_category
    
    def run(self):
        try:
            def progress_callback(current: int, total: int, filename: str):
                percent = int((current / total) * 100) if total > 0 else 0
                self.progress.emit(percent, f"Compressing: {filename}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            logger.info(f"CompressWorker starting: {len(self.files)} files, by_category={self.by_category}")
            
            if self.by_category:
                self.progress.emit(0, "Grouping files by category...")
                # Group files by category first
                from collections import defaultdict
                by_cat = defaultdict(list)
                for file_path in self.files:
                    # Simple category detection based on extension
                    ext = file_path.suffix.lower()
                    category = "Other"
                    if ext in ['.pdf', '.doc', '.docx', '.txt']:
                        category = "Documents"
                    elif ext in ['.jpg', '.png', '.gif', '.bmp']:
                        category = "Images"
                    elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                        category = "Videos"
                    elif ext in ['.zip', '.rar', '.7z', '.tar']:
                        category = "Archives"
                    by_cat[category].append(file_path)
                
                # Compress each category separately
                results = []
                for category, cat_files in by_cat.items():
                    logger.info(f"Compressing {len(cat_files)} files in category: {category}")
                    result = self.compressor.compress_files(
                        files=cat_files,
                        archive_name=f"{category}_{timestamp}",
                        output_folder=self.output_folder,
                        progress_callback=progress_callback
                    )
                    results.append(result)
                
                # Sum up all results
                self.finished.emit({
                    'success': True,
                    'results': results,
                    'files_compressed': sum(r.get('files_compressed', 0) for r in results),
                    'original_size_mb': sum(r.get('original_size_mb', 0) for r in results),
                    'compressed_size_mb': sum(r.get('compressed_size_mb', 0) for r in results)
                })
            else:
                logger.info(f"Compressing {len(self.files)} files into single archive")
                result = self.compressor.compress_files(
                    files=self.files,
                    archive_name=f"compressed_{timestamp}",
                    output_folder=self.output_folder,
                    progress_callback=progress_callback
                )
                logger.info(f"Compression result: {result}")
                self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"Compression error: {e}", exc_info=True)
            self.error.emit(str(e))


class CompressionDialog(QDialog):
    """
    Dialog for smart compression of old/large files.
    """
    
    def __init__(self, parent=None, config: Dict = None, target_folder: Path = None):
        super().__init__(parent)
        self.config = config or {}
        self.target_folder = target_folder
        self.compressor = SmartCompressor(config)
        
        self.scanned_files: List[Dict] = []  # List of file info dicts
        self.analysis: Dict = {}
        self.worker = None
        
        self._init_ui()
        
        if target_folder:
            self._start_scan()
    
    def _init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("📦 Smart Compression")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Settings section
        settings_group = self._create_settings_section()
        layout.addWidget(settings_group)
        
        # Results section (splitter)
        splitter = QSplitter(Qt.Vertical)
        
        # Files table
        files_widget = self._create_files_section()
        splitter.addWidget(files_widget)
        
        # Analysis section
        analysis_widget = self._create_analysis_section()
        splitter.addWidget(analysis_widget)
        
        splitter.setSizes([350, 150])
        layout.addWidget(splitter)
        
        # Progress section
        progress_layout = self._create_progress_section()
        layout.addLayout(progress_layout)
        
        # Button section
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)
    
    def _create_settings_section(self) -> QGroupBox:
        """Create settings controls."""
        group = QGroupBox("⚙️ Scan Settings")
        layout = QHBoxLayout(group)
        
        # Folder selection
        layout.addWidget(QLabel("Folder:"))
        self.folder_label = QLabel(str(self.target_folder or "Not selected"))
        self.folder_label.setStyleSheet("color: #3498db; font-weight: bold;")
        layout.addWidget(self.folder_label, 1)
        
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.clicked.connect(self._browse_folder)
        layout.addWidget(self.browse_btn)
        
        layout.addWidget(QLabel("  |  "))
        
        # Age filter
        layout.addWidget(QLabel("Files older than:"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(0, 3650)
        self.days_spin.setValue(90)
        self.days_spin.setSuffix(" days")
        layout.addWidget(self.days_spin)
        
        # Size filter
        layout.addWidget(QLabel("Min size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(0, 10000)
        self.size_spin.setValue(1)
        self.size_spin.setSuffix(" MB")
        layout.addWidget(self.size_spin)
        
        # Scan button
        self.scan_btn = QPushButton("🔍 Scan")
        self.scan_btn.clicked.connect(self._start_scan)
        layout.addWidget(self.scan_btn)
        
        return group
    
    def _create_files_section(self) -> QWidget:
        """Create files table."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("📄 Compressible Files")
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(header)
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels([
            "✓", "File Name", "Size", "Age", "Category"
        ])
        
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.files_table.setColumnWidth(0, 30)
        self.files_table.setColumnWidth(2, 100)
        self.files_table.setColumnWidth(3, 100)
        self.files_table.setColumnWidth(4, 120)
        
        self.files_table.setAlternatingRowColors(True)
        layout.addWidget(self.files_table)
        
        # Select all / none buttons
        select_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑ Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = QPushButton("☐ Select None")
        self.select_none_btn.clicked.connect(self._select_none)
        select_layout.addWidget(self.select_none_btn)
        
        select_layout.addStretch()
        
        self.selected_label = QLabel("Selected: 0 files (0 MB)")
        select_layout.addWidget(self.selected_label)
        
        layout.addLayout(select_layout)
        
        return widget
    
    def _create_analysis_section(self) -> QWidget:
        """Create analysis display."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("📊 Compression Analysis")
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(header)
        
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame { 
                background-color: #f8f9fa; 
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        
        # Stats labels
        self.total_files_label = QLabel("Total Files: 0")
        self.total_size_label = QLabel("Total Size: 0 MB")
        self.estimated_savings_label = QLabel("Est. Savings: 0 MB (0%)")
        
        for label in [self.total_files_label, self.total_size_label, self.estimated_savings_label]:
            label.setStyleSheet("font-weight: bold; font-size: 12px; color: #1E3A8A;")
            info_layout.addWidget(label)
            info_layout.addStretch()
        
        layout.addWidget(info_frame)
        
        # Compression options
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("Compression Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["zip", "zip_max"])
        
        # Check for 7z support
        try:
            import py7zr
            self.method_combo.addItems(["7z", "7z_max"])
        except ImportError:
            pass
        
        options_layout.addWidget(self.method_combo)
        
        self.by_category_check = QCheckBox("Group by category")
        self.by_category_check.setChecked(True)
        options_layout.addWidget(self.by_category_check)
        
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        return widget
    
    def _create_progress_section(self) -> QHBoxLayout:
        """Create progress bar."""
        layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        self.progress_label.setMinimumWidth(200)
        layout.addWidget(self.progress_label)
        
        return layout
    
    def _create_button_section(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        
        self.compress_btn = QPushButton("📦 Compress Selected")
        self.compress_btn.setEnabled(False)
        self.compress_btn.clicked.connect(self._start_compression)
        self.compress_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        layout.addWidget(self.compress_btn)
        
        layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
        return layout
    
    def _browse_folder(self):
        """Browse for folder to compress."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Compress",
            str(self.target_folder or Path.home())
        )
        
        if folder:
            self.target_folder = Path(folder)
            self.folder_label.setText(str(self.target_folder))
    
    def _start_scan(self):
        """Start scanning for compressible files."""
        if not self.target_folder:
            QMessageBox.warning(self, "No Folder", "Please select a folder to scan.")
            return
        
        self.scan_btn.setEnabled(False)
        self.compress_btn.setEnabled(False)
        self.files_table.setRowCount(0)
        
        self.worker = ScanWorker(
            compressor=self.compressor,
            folder=self.target_folder,
            days_old=self.days_spin.value(),
            min_size_mb=self.size_spin.value()
        )
        
        self.worker.progress.connect(self._on_scan_progress)
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.error.connect(self._on_error)
        
        self.worker.start()
    
    def _on_scan_progress(self, percent: int, message: str):
        """Handle scan progress updates."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
    
    def _on_scan_finished(self, files: List[Dict], analysis: Dict):
        """Handle scan completion."""
        # files is a list of dicts with 'path', 'size_bytes', 'category', etc.
        self.scanned_files = files
        self.analysis = analysis
        
        self.scan_btn.setEnabled(True)
        self.compress_btn.setEnabled(len(files) > 0)
        
        self._populate_files_table()
        self._update_analysis_display()
        
        self.progress_label.setText(f"Found {len(files)} compressible files")
    
    def _populate_files_table(self):
        """Populate the files table."""
        self.files_table.setRowCount(len(self.scanned_files))
        
        for row, file_info in enumerate(self.scanned_files):
            file_path = file_info['path']
            
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._update_selected_count)
            self.files_table.setCellWidget(row, 0, checkbox)
            
            # File name
            name_item = QTableWidgetItem(file_path.name)
            name_item.setToolTip(str(file_path))
            self.files_table.setItem(row, 1, name_item)
            
            # Size - use from dict
            size_str = f"{file_info.get('size_mb', 0):.1f} MB"
            self.files_table.setItem(row, 2, QTableWidgetItem(size_str))
            
            # Age - use from dict
            age_days = file_info.get('age_days', 0)
            age_str = f"{age_days} days"
            self.files_table.setItem(row, 3, QTableWidgetItem(age_str))
            
            # Category - use from dict
            category = file_info.get('category', 'Other')
            self.files_table.setItem(row, 4, QTableWidgetItem(category))
        
        self._update_selected_count()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size."""
        if size_bytes >= 1073741824:  # 1 GB
            return f"{size_bytes / 1073741824:.1f} GB"
        elif size_bytes >= 1048576:  # 1 MB
            return f"{size_bytes / 1048576:.1f} MB"
        elif size_bytes >= 1024:  # 1 KB
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes} B"
    
    def _get_category(self, ext: str) -> str:
        """Get category for file extension."""
        categories = {
            '.pdf': 'Documents',
            '.doc': 'Documents', '.docx': 'Documents',
            '.xls': 'Documents', '.xlsx': 'Documents',
            '.ppt': 'Documents', '.pptx': 'Documents',
            '.txt': 'Documents',
            '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images',
            '.gif': 'Images', '.bmp': 'Images',
            '.mp4': 'Videos', '.avi': 'Videos', '.mkv': 'Videos',
            '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio',
            '.py': 'Code', '.js': 'Code', '.java': 'Code',
        }
        return categories.get(ext, 'Other')
    
    def _update_analysis_display(self):
        """Update analysis stats display."""
        if not self.analysis:
            return
        
        self.total_files_label.setText(f"Total Files: {self.analysis.get('total_files', 0)}")
        
        total_mb = self.analysis.get('total_size_mb', 0)
        self.total_size_label.setText(f"Total Size: {total_mb:.1f} MB")
        
        est_savings = self.analysis.get('estimated_savings_mb', 0)
        est_percent = self.analysis.get('savings_percent', 0)
        self.estimated_savings_label.setText(
            f"Est. Savings: {est_savings:.1f} MB ({est_percent:.0f}%)"
        )
    
    def _select_all(self):
        """Select all files."""
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def _select_none(self):
        """Deselect all files."""
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def _update_selected_count(self):
        """Update selected files count."""
        selected_count = 0
        selected_size = 0
        
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
                # Use size from dict
                if row < len(self.scanned_files):
                    selected_size += self.scanned_files[row].get('size_bytes', 0)
        
        size_mb = selected_size / 1048576
        self.selected_label.setText(f"Selected: {selected_count} files ({size_mb:.1f} MB)")
    
    def _get_selected_files(self) -> List[Path]:
        """Get list of selected file paths."""
        selected = []
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                if row < len(self.scanned_files):
                    selected.append(self.scanned_files[row]['path'])
        return selected
    
    def _start_compression(self):
        """Start compression process."""
        selected_files = self._get_selected_files()
        
        if not selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to compress.")
            return
        
        logger.info(f"Starting compression of {len(selected_files)} files")
        
        # Get output folder - user must select where to save archives
        output_folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder for Archives",
            str(self.target_folder)
        )
        
        if not output_folder:
            logger.info("Compression cancelled - no output folder selected")
            return
        
        logger.info(f"Output folder selected: {output_folder}")
        self.compress_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        
        self.worker = CompressWorker(
            compressor=self.compressor,
            files=selected_files,
            output_folder=Path(output_folder),
            method=self.method_combo.currentText(),
            by_category=self.by_category_check.isChecked()
        )
        
        self.worker.progress.connect(self._on_compress_progress)
        self.worker.finished.connect(self._on_compress_finished)
        self.worker.error.connect(self._on_error)
        
        self.worker.start()
    
    def _on_compress_progress(self, percent: int, message: str):
        """Handle compression progress."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
    
    def _on_compress_finished(self, result: Dict):
        """Handle compression completion."""
        # Reset progress bar to 0 (not stuck at 100%)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Ready")
        
        self.compress_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        
        success = result.get('success', False)
        
        if success:
            compressed = result.get('files_compressed', 0)
            original = result.get('original_size_mb', 0)
            final = result.get('compressed_size_mb', 0)
            savings = original - final
            
            # Use blue themed dialog - NEVER use default white QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("✅ Compression Complete")
            msg.setText(f"<h2 style='color:#10B981;'>✅ Compression successful!</h2>")
            msg.setInformativeText(
                f"<p style='font-size:14px; color:#1E3A8A;'>"
                f"<b>Files compressed:</b> {compressed}<br>"
                f"<b>Original size:</b> {original:.1f} MB<br>"
                f"<b>Compressed size:</b> {final:.1f} MB<br>"
                f"<b>Space saved:</b> {savings:.1f} MB"
                f"</p>"
            )
            ThemeHelper.style_message_box(msg, 'success')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            
            self.progress_label.setText(f"Compressed {compressed} files, saved {savings:.1f} MB")
        else:
            error = result.get('error', 'Unknown error')
            
            # Use blue themed warning dialog
            msg = QMessageBox(self)
            msg.setWindowTitle("⚠️ Compression Failed")
            msg.setText(f"<h2 style='color:#F59E0B;'>⚠️ Compression Failed</h2>")
            msg.setInformativeText(
                f"<p style='font-size:14px; color:#1E3A8A;'><b>Error:</b> {error}</p>"
            )
            ThemeHelper.style_message_box(msg, 'warning')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            
            self.progress_label.setText("Compression failed")
    
    def _on_error(self, error: str):
        """Handle worker errors."""
        self.scan_btn.setEnabled(True)
        self.compress_btn.setEnabled(len(self.scanned_files) > 0)
        
        QMessageBox.critical(self, "Error", f"An error occurred:\n{error}")
        self.progress_label.setText("Error")


# Test dialog
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = CompressionDialog(target_folder=Path.home() / "Downloads")
    dialog.show()
    sys.exit(app.exec())
