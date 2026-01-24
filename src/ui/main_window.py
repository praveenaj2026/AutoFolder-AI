"""
Main Window - AutoFolder AI v2.0

Modern blueish theme UI with multi-level organization.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QGroupBox, QHeaderView, QCheckBox, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor

try:
    from ..core import FileOrganizer
    from ..ai import AIClassifier
    from ..utils.config_manager import ConfigManager
    from .duplicate_dialog import DuplicateDialog
    from .stats_dialog import StatsDialog
except ImportError:
    from core import FileOrganizer
    from ai import AIClassifier
    from utils.config_manager import ConfigManager
    from ui.duplicate_dialog import DuplicateDialog
    from ui.stats_dialog import StatsDialog


logger = logging.getLogger(__name__)


class OrganizeThread(QThread):
    """Background thread for organization operations."""
    
    progress = Signal(int, int)  # current, total
    finished = Signal(dict)  # result
    error = Signal(str)  # error message
    
    def __init__(self, organizer, folder_path, dry_run=False):
        super().__init__()
        self.organizer = organizer
        self.folder_path = folder_path
        self.dry_run = dry_run
    
    def run(self):
        try:
            result = self.organizer.organize_folder(
                self.folder_path,
                profile='downloads',
                dry_run=self.dry_run
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Organization error: {e}", exc_info=True)
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window with modern blueish theme."""
    
    # File type to icon mapping
    FILE_TYPE_ICONS = {
        # Documents
        'pdf': '📕',
        'doc': '📘',
        'docx': '📘',
        'txt': '📄',
        'rtf': '📄',
        'odt': '📄',
        # Spreadsheets
        'xls': '📊',
        'xlsx': '📊',
        'csv': '📊',
        'ods': '📊',
        # Presentations
        'ppt': '📽️',
        'pptx': '📽️',
        'odp': '📽️',
        # Images
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'bmp': '🖼️',
        'svg': '🖼️',
        'webp': '🖼️',
        'ico': '🖼️',
        # Videos
        'mp4': '🎬',
        'avi': '🎬',
        'mkv': '🎬',
        'mov': '🎬',
        'wmv': '🎬',
        'flv': '🎬',
        'webm': '🎬',
        # Audio
        'mp3': '🎵',
        'wav': '🎵',
        'flac': '🎵',
        'aac': '🎵',
        'm4a': '🎵',
        'ogg': '🎵',
        'wma': '🎵',
        # Archives
        'zip': '📦',
        'rar': '📦',
        '7z': '📦',
        'tar': '📦',
        'gz': '📦',
        'bz2': '📦',
        # Code
        'py': '🐍',
        'js': '📜',
        'html': '🌐',
        'css': '🎨',
        'java': '☕',
        'cpp': '⚙️',
        'c': '⚙️',
        'php': '🐘',
        'rb': '💎',
        'go': '🔵',
        'rs': '🦀',
        'ts': '📜',
        'json': '📋',
        'xml': '📋',
        'yaml': '📋',
        'yml': '📋',
        # Executables
        'exe': '⚡',
        'msi': '⚡',
        'dmg': '⚡',
        'app': '⚡',
        'deb': '⚡',
        'rpm': '⚡',
        # Default
        'default': '📄'
    }
    
    def __init__(self, config: ConfigManager):
        super().__init__()
        
        self.config = config
        config.config['ai']['enabled'] = True
        
        self.organizer = FileOrganizer(config.config)
        self.ai_classifier = AIClassifier(config.config)
        
        # Connect AI classifier to organizer for semantic grouping
        self.organizer.set_ai_classifier(self.ai_classifier)
        
        self.current_folder: Optional[Path] = None
        self.current_preview = []
        self.current_stats = None
        self.organize_thread: Optional[OrganizeThread] = None
        # AI semantic grouping is ALWAYS enabled - no toggle needed
        
        self._init_ui()
        self._apply_blue_theme()
        
        logger.info("Main window initialized with blueish theme")
    
    def _init_ui(self):
        """Initialize the modern blueish-themed user interface."""
        
        app_config = self.config.get('app', {})
        self.setWindowTitle(f"{app_config.get('name', 'AutoFolder AI')} - v{app_config.get('version', '1.0.0')}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(900, 650)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        header = self._create_header()
        main_layout.addWidget(header)
        
        folder_group = self._create_folder_selection()
        main_layout.addWidget(folder_group)
        
        preview_group = self._create_preview_area()
        main_layout.addWidget(preview_group, stretch=1)
        
        ai_options = self._create_ai_options()
        main_layout.addWidget(ai_options)
        
        button_layout = self._create_action_buttons()
        main_layout.addLayout(button_layout)
        
        self.statusBar().showMessage("🚀 Ready • AI-Powered Multi-Level Organization")
        
    def _create_header(self) -> QWidget:
        """Create modern header."""
        header_widget = QWidget()
        header_widget.setFixedHeight(110)
        
        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)
        
        title = QLabel("AutoFolder AI")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1E3A8A;")  # Dark blue
        layout.addWidget(title)
        
        subtitle = QLabel("🤖 AI-Powered Multi-Level Smart Organization")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #3B82F6;")  # Bright blue
        layout.addWidget(subtitle)
        
        return header_widget
    
    def _create_folder_selection(self) -> QGroupBox:
        """Create folder selection group."""
        
        group = QGroupBox("📁 Select Folder to Organize")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 18px;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                margin-top: 12px;
                background-color: #EFF6FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 8px;
                background-color: #EFF6FF;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        self.folder_label = QLabel("No folder selected - Click Browse to get started")
        self.folder_label.setStyleSheet("""
            QLabel {
                padding: 14px;
                background-color: #DBEAFE;
                border: 1px solid #93C5FD;
                border-radius: 8px;
                font-size: 13px;
                color: #1E40AF;
            }
        """)
        layout.addWidget(self.folder_label, stretch=1)
        
        self.browse_btn = QPushButton("📂 Browse")
        self.browse_btn.clicked.connect(self._browse_and_analyze)
        self.browse_btn.setFixedHeight(48)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #60A5FA;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QPushButton:pressed {
                background-color: #2563EB;
            }
        """)
        layout.addWidget(self.browse_btn)
        
        # Duplicate scan button
        self.scan_duplicates_btn = QPushButton("🔍 Scan Duplicates")
        self.scan_duplicates_btn.clicked.connect(self._scan_duplicates)
        self.scan_duplicates_btn.setFixedHeight(48)
        self.scan_duplicates_btn.setEnabled(False)  # Enabled after folder selection
        self.scan_duplicates_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
            QPushButton:pressed {
                background-color: #B45309;
            }
            QPushButton:disabled {
                background-color: #D1D5DB;
                color: #9CA3AF;
            }
        """)
        layout.addWidget(self.scan_duplicates_btn)
        
        # View Stats button
        self.view_stats_btn = QPushButton("📊 View Stats")
        self.view_stats_btn.clicked.connect(self._show_stats)
        self.view_stats_btn.setFixedHeight(48)
        self.view_stats_btn.setEnabled(False)  # Enabled after preview
        self.view_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:pressed {
                background-color: #6D28D9;
            }
            QPushButton:disabled {
                background-color: #D1D5DB;
                color: #9CA3AF;
            }
        """)
        layout.addWidget(self.view_stats_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_preview_area(self) -> QGroupBox:
        """Create preview area with table."""
        
        group = QGroupBox("📋 Preview - Multi-Level Smart Organization")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 18px;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                margin-top: 12px;
                background-color: #EFF6FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 8px;
                background-color: #EFF6FF;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.info_label = QLabel("Browse a folder to see intelligent organization preview")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #1E40AF;
                padding: 14px;
                background-color: #DBEAFE;
                border-radius: 8px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.info_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels(["📦 Type", "📄 Original Name", "✏️ New Name", "🏷️ Category", "📦 Size", "📁 Destination"])
        
        # Blueish theme table styling
        self.preview_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #93C5FD;
                border-radius: 8px;
                background-color: #FFFFFF;
                gridline-color: #BFDBFE;
                color: #1E40AF;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E0F2FE;
            }
            QTableWidget::item:selected {
                background-color: #BFDBFE;
                color: #1E3A8A;
            }
            QHeaderView::section {
                background-color: #DBEAFE;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #93C5FD;
                font-weight: bold;
                color: #1E3A8A;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #EFF6FF;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #93C5FD;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #60A5FA;
            }
        """)
        
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Configure selection behavior - select entire rows, no vertical header
        self.preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.preview_table.setSelectionMode(QTableWidget.SingleSelection)
        self.preview_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.preview_table)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #93C5FD;
                border-radius: 8px;
                text-align: center;
                height: 28px;
                background-color: #EFF6FF;
                color: #1E3A8A;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #60A5FA, stop:1 #3B82F6);
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def _create_ai_options(self) -> QWidget:
        """Create AI status panel - AI is always enabled."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # AI Status label (always enabled)
        ai_status_label = QLabel("🤖 AI Semantic Grouping: ALWAYS ENABLED")
        ai_status_label.setStyleSheet("""
            QLabel {
                color: #059669;
                font-size: 13px;
                font-weight: bold;
                padding: 8px;
                background-color: #D1FAE5;
                border-radius: 6px;
                border: 2px solid #10B981;
            }
        """)
        layout.addWidget(ai_status_label)
        
        # Info label
        ai_info_label = QLabel("✨ Intelligently groups similar files using AI embeddings")
        ai_info_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 11px;
                font-style: italic;
                padding-left: 10px;
            }
        """)
        layout.addWidget(ai_info_label)
        layout.addStretch()
        
        return widget
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        
        layout = QHBoxLayout()
        layout.setSpacing(18)
        
        self.undo_btn = QPushButton("⟲ Undo Last")
        self.undo_btn.clicked.connect(self._undo_last)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(55)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #60A5FA;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 14px 35px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QPushButton:pressed {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #BFDBFE;
                color: #93C5FD;
            }
        """)
        layout.addWidget(self.undo_btn)
        
        layout.addStretch()
        
        self.organize_btn = QPushButton("✨ Smart Organize")
        self.organize_btn.clicked.connect(self._organize_folder)
        self.organize_btn.setEnabled(False)
        self.organize_btn.setFixedHeight(55)
        self.organize_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #2563EB, stop:1 #1E40AF);
                color: white;
                font-size: 17px;
                font-weight: bold;
                padding: 14px 55px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1E40AF, stop:1 #1E3A8A);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1E3A8A, stop:1 #172554);
            }
            QPushButton:disabled {
                background-color: #BFDBFE;
                color: #93C5FD;
            }
        """)
        layout.addWidget(self.organize_btn)
        
        return layout
    
    def _apply_blue_theme(self):
        """Apply blueish theme to entire application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F9FF;
            }
            QStatusBar {
                background-color: #DBEAFE;
                color: #1E40AF;
                border-top: 1px solid #93C5FD;
                font-size: 12px;
                padding: 5px;
            }
            QMessageBox {
                background-color: #EFF6FF;
                color: #1E3A8A;
            }
            QMessageBox QPushButton {
                background-color: #60A5FA;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
    
    def _browse_and_analyze(self):
        """Browse for folder and immediately analyze."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Organize",
            str(self.current_folder) if self.current_folder else str(Path.home() / 'Downloads')
        )
        
        if folder:
            self.current_folder = Path(folder)
            self.folder_label.setText(str(self.current_folder))
            self.folder_label.setStyleSheet("""
                QLabel {
                    padding: 14px;
                    background-color: #DBEAFE;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #1E3A8A;
                    font-weight: bold;
                }
            """)
            logger.info(f"Folder selected: {self.current_folder}")
            
            self._analyze_folder()
    
    def _analyze_folder(self):
        """Analyze the selected folder with AI."""
        if not self.current_folder:
            return
        
        try:
            self.statusBar().showMessage("🤖 AI analyzing folder and subfolders...")
            self.browse_btn.setEnabled(False)
            
            analysis = self.organizer.analyze_folder(self.current_folder)
            
            self.info_label.setText(
                f"✅ Found {analysis['total_files']} files "
                f"({self._format_size(analysis['total_size'])}) • "
                f"Multi-Level AI Organization Ready"
            )
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #065F46;
                    padding: 14px;
                    background-color: #D1FAE5;
                    border: 1px solid #34D399;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
            
            # Show progress dialog for large folders or AI processing
            if analysis['total_files'] > 100:
                progress = QProgressDialog(
                    "Analyzing files and creating organization preview...\n\n🤖 AI Semantic Grouping: Generating embeddings and clustering files",
                    None,
                    0,
                    0,
                    self
                )
                progress.setWindowTitle("Processing...")
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()
                QTimer.singleShot(100, lambda: self._run_preview_analysis(progress))
            else:
                self._run_preview_analysis(None)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
    
    def _run_preview_analysis(self, progress_dialog):
        """Run preview analysis and update UI."""
        try:
            self.current_preview, self.current_stats = self.organizer.preview_organization(
                self.current_folder,
                profile='downloads'
            )
            
            if progress_dialog:
                progress_dialog.close()
            
            self._update_preview_table(self.current_preview)
            
            # Enable organize and stats buttons after preview is ready
            self.organize_btn.setEnabled(len(self.current_preview) > 0)
            self.view_stats_btn.setEnabled(self.current_stats is not None)
            
            # Update status message - AI is always active
            self.statusBar().showMessage(
                f"✅ Ready to organize {len(self.current_preview)} items • 🤖 AI Semantic Grouping Active"
            )
            
        except Exception as e:
            if progress_dialog:
                progress_dialog.close()
            logger.error(f"Preview generation error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to generate preview: {str(e)}"
            )
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("❌ Analysis Error")
            error_msg.setText(f"<h2 style='color:#DC2626;'>Failed to analyze folder</h2>")
            error_msg.setInformativeText(
                f"<p style='font-size:14px; color:#1E3A8A;'><b>Error:</b> {str(e)}</p>"
            )
            error_msg.setStandardButtons(QMessageBox.Ok)
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    font-size: 14px;
                    min-width: 400px;
                }
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            error_msg.exec_()
        finally:
            self.browse_btn.setEnabled(True)
            # Enable duplicate scan button after folder selection
            self.scan_duplicates_btn.setEnabled(True)
    
    def _scan_duplicates(self):
        """Scan for duplicate files in selected folder."""
        if not self.current_folder:
            QMessageBox.warning(
                self,
                "No Folder Selected",
                "Please select a folder first using the Browse button."
            )
            return
        
        try:
            # Show progress dialog
            progress = QProgressDialog(
                "Scanning for duplicate files...\n\nThis may take a few minutes for large folders.",
                "Cancel",
                0,
                0,
                self
            )
            progress.setWindowTitle("🔍 Scanning Duplicates")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            
            # Get hash algorithm from config
            algorithm = self.config.config.get('duplicates', {}).get('hash_algorithm', 'sha256')
            
            # Scan for duplicates
            duplicates, stats = self.organizer.scan_for_duplicates(
                self.current_folder,
                algorithm=algorithm
            )
            
            progress.close()
            
            if not duplicates:
                QMessageBox.information(
                    self,
                    "No Duplicates Found",
                    f"No duplicate files found in {self.current_folder.name}.\n\n"
                    f"All files are unique!"
                )
                return
            
            # Show duplicate management dialog
            dialog = DuplicateDialog(duplicates, stats, self)
            dialog.duplicates_processed.connect(self._handle_duplicate_result)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Duplicate scan error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Scan Error",
                f"Failed to scan for duplicates:\n\n{str(e)}"
            )
    
    def _handle_duplicate_result(self, result: dict):
        """Handle duplicate processing result from dialog."""
        action = result['action']
        duplicates = result['duplicates']
        stats = result['stats']
        
        if action == 'skip':
            logger.info("User chose to skip duplicate handling")
            return
        
        try:
            # Show progress
            progress = QProgressDialog(
                f"Processing {stats['total_duplicate_files']} duplicate files...",
                None,
                0,
                0,
                self
            )
            progress.setWindowTitle("Processing Duplicates")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()
            
            # Get target folder for 'keep_all' action
            target_folder = None
            if action == 'keep_all':
                target_name = self.config.config.get('duplicates', {}).get(
                    'move_duplicates_to', 
                    'Duplicates'
                )
                target_folder = self.current_folder / target_name
            
            # Handle duplicates
            result = self.organizer.handle_duplicates(
                duplicates,
                action,
                target_folder
            )
            
            progress.close()
            
            # Build detailed message
            if action == 'keep_all':
                message = f"✅ Duplicate Processing Complete!\n\n"
                message += f"📁 {result['files_moved']} duplicate files moved to:\n{target_folder}\n\n"
                
                if result['kept_files']:
                    message += f"📌 Kept {len(result['kept_files'])} original files in place\n\n"
                
                # Show first few moved files
                if result['moved_files']:
                    message += "📦 Files Moved:\n"
                    for i, (src, dest) in enumerate(result['moved_files'][:5]):
                        src_name = Path(src).name
                        message += f"  • {src_name} → Duplicates folder\n"
                    if len(result['moved_files']) > 5:
                        message += f"  ... and {len(result['moved_files']) - 5} more\n"
            else:
                message = f"✅ Duplicate Processing Complete!\n\n"
                message += f"🗑️ {result['files_deleted']} duplicate files deleted\n"
                message += f"💾 {result['space_freed_mb']:.2f} MB freed\n\n"
                
                if result['kept_files']:
                    message += f"📌 Kept {len(result['kept_files'])} files based on '{action}' strategy\n\n"
                
                # Show first few deleted files
                if result['deleted_files']:
                    message += "🗑️ Files Deleted:\n"
                    for i, deleted in enumerate(result['deleted_files'][:8]):
                        file_name = Path(deleted).name
                        message += f"  • {file_name}\n"
                    if len(result['deleted_files']) > 8:
                        message += f"  ... and {len(result['deleted_files']) - 8} more\n"
            
            # Show message with scrollable text
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Duplicate Processing Complete")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    font-size: 13px;
                    min-width: 500px;
                    min-height: 200px;
                }
                QPushButton {
                    background-color: #10B981;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            msg_box.exec_()
            
            # Refresh analysis
            if self.current_folder:
                self._analyze_folder()
            
        except Exception as e:
            logger.error(f"Duplicate handling error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Processing Error",
                f"Failed to process duplicates:\n\n{str(e)}"
            )
    
    def _show_stats(self):
        """Show organization statistics dashboard."""
        if not self.current_stats:
            QMessageBox.information(
                self,
                "No Statistics",
                "No statistics available. Please analyze a folder first."
            )
            return
        
        try:
            dialog = StatsDialog(self.current_stats, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing stats: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Stats Error",
                f"Failed to show statistics:\n\n{str(e)}"
            )
    
    def _update_preview_table(self, operations):
        """Update the preview table with operations."""
        
        # Validate operations is a list
        if not isinstance(operations, list):
            logger.error(f"Operations must be a list, got {type(operations)}")
            raise ValueError(f"Invalid operations type: {type(operations)}. Expected list of dictionaries.")
        
        # Limit display to first 1000 items for performance
        display_limit = 1000
        display_ops = operations[:display_limit]
        
        self.preview_table.setRowCount(len(display_ops))
        
        for i, op in enumerate(display_ops):
            # Validate operation is a dictionary
            if not isinstance(op, dict):
                logger.error(f"Operation at index {i} must be a dict, got {type(op)}")
                continue
            
            # File type icon
            ext = op['source'].suffix.lower().lstrip('.')
            icon = self.FILE_TYPE_ICONS.get(ext, self.FILE_TYPE_ICONS['default'])
            icon_item = QTableWidgetItem(icon)
            icon_item.setFont(QFont("Segoe UI Emoji", 16))
            icon_item.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(i, 0, icon_item)
            
            # Original name - sanitize to remove problematic characters
            filename = op['source'].name
            # Remove non-printable characters, box-drawing, and control characters
            cleaned = []
            for char in filename:
                code = ord(char)
                # Skip control chars (0-31, 127-159), box-drawing (9472-9599), and other special ranges
                if (code < 32 or (127 <= code < 160) or (9472 <= code < 9600)):
                    continue
                if char.isprintable():
                    cleaned.append(char)
            filename = ''.join(cleaned)
            
            name_item = QTableWidgetItem(filename)
            name_item.setForeground(QColor("#1E3A8A"))
            self.preview_table.setItem(i, 1, name_item)
            
            # Suggested new name (if different from original)
            suggested_name = op.get('suggested_name', op['source'].name)
            original_name = op.get('original_name', op['source'].name)
            
            if suggested_name != original_name:
                # Show suggested name in green (rename happening)
                suggested_item = QTableWidgetItem(suggested_name)
                suggested_item.setForeground(QColor("#059669"))
                suggested_item.setToolTip(f"Will be renamed from: {original_name}")
            else:
                # Show "No change" in gray
                suggested_item = QTableWidgetItem("(no change)")
                suggested_item.setForeground(QColor("#9CA3AF"))
            
            self.preview_table.setItem(i, 2, suggested_item)
            
            # Category
            category_item = QTableWidgetItem(op['category'].title())
            category_item.setForeground(QColor("#2563EB"))
            self.preview_table.setItem(i, 3, category_item)
            
            # Size
            size_item = QTableWidgetItem(self._format_size(op['size']))
            size_item.setForeground(QColor("#7C3AED"))
            self.preview_table.setItem(i, 4, size_item)
            
            # Target folder (showing nested structure)
            target_path = str(op['target'].relative_to(self.current_folder))
            target_item = QTableWidgetItem(target_path)
            target_item.setForeground(QColor("#059669"))
            self.preview_table.setItem(i, 5, target_item)
        
        # Resize icon column to fit content
        self.preview_table.setColumnWidth(0, 60)
        
        # Disable selection highlight on icon column to prevent black box
        for i in range(len(display_ops)):
            icon_item = self.preview_table.item(i, 0)
            if icon_item:
                icon_item.setFlags(icon_item.flags() & ~Qt.ItemIsSelectable)
        
        # Show message if there are more items
        if len(operations) > display_limit:
            logger.info(f"Showing first {display_limit} of {len(operations)} items in preview")
    
    def _organize_folder(self):
        """Execute smart organization."""
        if not self.current_folder or not self.current_preview:
            return
        
        reply = QMessageBox.question(
            self,
            "✨ Confirm Smart Organization",
            f"<b style='color:#1E3A8A;'>Smart Organize {len(self.current_preview)} items?</b><br><br>"
            f"<span style='color:#3B82F6;'>Multi-level organization: Category → Type → Date</span><br>"
            f"<span style='color:#059669;'><i>You can undo this anytime.</i></span>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self._set_controls_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.current_preview))
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("🚀 Organizing with multi-level sorting...")
        
        self.organize_thread = OrganizeThread(
            self.organizer,
            self.current_folder,
            dry_run=False
        )
        self.organize_thread.finished.connect(self._on_organize_finished)
        self.organize_thread.error.connect(self._on_organize_error)
        self.organize_thread.start()
    
    def _on_organize_finished(self, result):
        """Handle organization completion with popup."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        if result['success']:
            QMessageBox.information(
                self,
                "✅ Success!",
                f"<h3 style='color:#059669;'>Successfully organized {result['completed']} items!</h3>"
                f"<p style='color:#1E3A8A;'>Multi-level organization complete (including subfolders).</p>"
                f"<p style='color:#3B82F6;'><i>Click 'Undo Last' if you want to revert.</i></p>"
            )
            
            self.undo_btn.setEnabled(result['can_undo'])
            self.statusBar().showMessage(
                f"✅ Organization complete: {result['completed']} items organized!"
            )
            
            self.current_preview = []
            self.preview_table.setRowCount(0)
            self.organize_btn.setEnabled(False)
            self.info_label.setText("🎉 Organization complete! Browse another folder to continue.")
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #1E40AF;
                    padding: 14px;
                    background-color: #DBEAFE;
                    border-radius: 8px;
                    font-size: 13px;
                }
            """)
            
        else:
            # Build detailed error message
            error_details = ""
            if result.get('failed_items'):
                error_details = "<br><br><b style='color:#DC2626;'>Failed items:</b><ul style='color:#7C2D12;'>"
                for item_name, error_msg in result['failed_items'][:10]:  # Show first 10 errors
                    # Truncate long error messages
                    short_error = error_msg[:80] + "..." if len(error_msg) > 80 else error_msg
                    error_details += f"<li><b>{item_name}</b>: {short_error}</li>"
                
                if len(result['failed_items']) > 10:
                    error_details += f"<li><i>...and {len(result['failed_items']) - 10} more</i></li>"
                error_details += "</ul>"
            
            success_details = ""
            if result.get('completed_items'):
                success_details = f"<br><b style='color:#059669;'>Successfully organized:</b> {', '.join(result['completed_items'][:5])}"
                if len(result['completed_items']) > 5:
                    success_details += f" <i>(+{len(result['completed_items']) - 5} more)</i>"
            
            QMessageBox.warning(
                self,
                "⚠️ Partial Success",
                f"<h3 style='color:#D97706;'>Partially completed</h3>"
                f"<p style='color:#1E3A8A;'>Organized {result['completed']} items.</p>"
                f"<p style='color:#DC2626;'>{result['failed']} items could not be organized.</p>"
                f"{success_details}"
                f"{error_details}"
            )
    
    def _on_organize_error(self, error):
        """Handle organization error with popup."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("❌ Error")
        error_box.setText("<h3 style='color:#DC2626;'>Organization Failed</h3>")
        error_box.setInformativeText(f"<p style='color:#000000; font-size:13px;'><b>Error:</b> {error}</p>")
        error_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #000000;
                min-width: 400px;
            }
        """)
        error_box.exec_()
        self.statusBar().showMessage("❌ Organization failed")
    
    def _undo_last(self):
        """Undo last organization with improved feedback."""
        reply = QMessageBox.question(
            self,
            "⟲ Confirm Undo",
            "<b style='color:#1E3A8A;'>Undo the last organization?</b><br><br>"
            "<span style='color:#3B82F6;'>Items will be moved back to original locations.</span><br>"
            "<span style='color:#D97706;'>Empty folders will be removed.</span>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.statusBar().showMessage("⟲ Undoing organization...")
            
            undo_manager = self.organizer.undo_manager
            if undo_manager.can_undo():
                last_operation = undo_manager.get_last_operation()
                file_count = len(last_operation.get('operations', []))
                
                # Perform undo
                success = self.organizer.undo_last_operation()
                
                if success and self.current_folder:
                    # PROPERLY clean up empty folders
                    deleted_count = self._cleanup_empty_folders_recursive(self.current_folder)
                    
                    QMessageBox.information(
                        self, 
                        "✅ Undo Complete", 
                        f"<h3 style='color:#059669;'>Successfully undone!</h3>"
                        f"<p style='color:#1E3A8A;'>• Moved {file_count} items back</p>"
                        f"<p style='color:#1E3A8A;'>• Removed {deleted_count} empty folders</p>"
                    )
                    self.undo_btn.setEnabled(False)
                    self.statusBar().showMessage(f"✅ Undo complete: {file_count} items restored")
                else:
                    QMessageBox.warning(
                        self, 
                        "⚠️ Warning", 
                        "<p style='color:#D97706;'>Undo partially completed.</p>"
                    )
            else:
                QMessageBox.information(
                    self, 
                    "ℹ️ Info", 
                    "<p style='color:#3B82F6;'>Nothing to undo.</p>"
                )
                
        except Exception as e:
            logger.error(f"Undo error: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "❌ Error", 
                f"<h3 style='color:#DC2626;'>Failed to undo</h3>"
                f"<p style='color:#1E3A8A;'>{e}</p>"
            )
    
    def _cleanup_empty_folders_recursive(self, base_folder: Path) -> int:
        """Remove empty folders recursively. Handles OneDrive locked folders. Returns count of deleted folders."""
        import subprocess
        import time
        
        deleted_count = 0
        max_attempts = 20  # More attempts for OneDrive sync
        base_str = str(base_folder)
        
        for attempt in range(max_attempts):
            attempt_deleted = 0
            folders_to_remove = []
            
            try:
                # Collect all empty folders first
                for dirpath, dirnames, filenames in os.walk(base_str, topdown=False):
                    if dirpath == base_str:
                        continue
                    
                    try:
                        # Check if directory is empty
                        contents = os.listdir(dirpath)
                        if len(contents) == 0:
                            folders_to_remove.append(dirpath)
                    except (PermissionError, FileNotFoundError):
                        pass
                    except Exception as e:
                        logger.debug(f"Error checking {dirpath}: {e}")
                
                # Try to remove each empty folder
                for folder_path in folders_to_remove:
                    try:
                        # First try normal removal
                        os.rmdir(folder_path)
                        logger.info(f"Removed empty folder: {folder_path}")
                        attempt_deleted += 1
                    except PermissionError:
                        # OneDrive locked - try Windows rmdir with force
                        try:
                            # Use Windows rmdir command which can handle OneDrive better
                            result = subprocess.run(
                                ['cmd', '/c', 'rmdir', '/q', folder_path],
                                capture_output=True,
                                timeout=5
                            )
                            if result.returncode == 0:
                                logger.info(f"Force-removed folder: {folder_path}")
                                attempt_deleted += 1
                            else:
                                logger.debug(f"OneDrive locked (skipping): {folder_path}")
                        except Exception as e:
                            logger.debug(f"Force remove failed for {folder_path}: {e}")
                    except FileNotFoundError:
                        # Already deleted
                        attempt_deleted += 1
                    except Exception as e:
                        logger.debug(f"Could not remove {folder_path}: {e}")
            
            except Exception as e:
                logger.warning(f"Error during cleanup pass {attempt + 1}: {e}")
            
            deleted_count += attempt_deleted
            
            if attempt_deleted > 0:
                logger.info(f"Cleanup pass {attempt + 1}: Deleted {attempt_deleted} empty folders")
                # Small delay to let OneDrive sync
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
            else:
                logger.debug(f"Cleanup pass {attempt + 1}: No empty folders found")
                break
        
        if deleted_count > 0:
            logger.info(f"Total empty folders removed: {deleted_count}")
        else:
            logger.info("Note: Some empty folders may be locked by OneDrive and cannot be removed")
        
        return deleted_count
    
    def _set_controls_enabled(self, enabled: bool):
        """Enable/disable controls during operation."""
        self.browse_btn.setEnabled(enabled)
        self.organize_btn.setEnabled(enabled and len(self.current_preview) > 0)
        if enabled:
            self.undo_btn.setEnabled(self.organizer.undo_manager.can_undo())
        else:
            self.undo_btn.setEnabled(False)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def closeEvent(self, event):
        """Handle window close."""
        logger.info("Application closing")
        event.accept()
