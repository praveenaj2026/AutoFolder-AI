"""
Main Window - AutoFolder AI

The primary UI for the application.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QGroupBox, QCheckBox, QTextEdit,
    QSplitter, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont

try:
    from ..core import FileOrganizer
    from ..ai import AIClassifier
    from ..utils.config_manager import ConfigManager
except ImportError:
    from core import FileOrganizer
    from ai import AIClassifier
    from utils.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class OrganizeThread(QThread):
    """Background thread for organization operations."""
    
    progress = Signal(int, int)  # current, total
    finished = Signal(dict)  # result
    error = Signal(str)  # error message
    
    def __init__(self, organizer, folder_path, profile, dry_run=False):
        super().__init__()
        self.organizer = organizer
        self.folder_path = folder_path
        self.profile = profile
        self.dry_run = dry_run
    
    def run(self):
        try:
            result = self.organizer.organize_folder(
                self.folder_path,
                profile=self.profile,
                dry_run=self.dry_run
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Organization error: {e}", exc_info=True)
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, config: ConfigManager):
        super().__init__()
        
        self.config = config
        self.organizer = FileOrganizer(config.config)
        self.ai_classifier = AIClassifier(config.config)
        
        self.current_folder: Optional[Path] = None
        self.current_preview = []
        self.organize_thread: Optional[OrganizeThread] = None
        
        self._init_ui()
        self._set_default_folder()
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        
        # Window settings
        ui_config = self.config.get('ui', {})
        app_config = self.config.get('app', {})
        
        self.setWindowTitle(f"{app_config.get('name', 'AutoFolder AI')} - v{app_config.get('version', '1.0.0')}")
        self.setGeometry(100, 100, ui_config.get('window_width', 1200), ui_config.get('window_height', 800))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("AutoFolder AI")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        subtitle = QLabel("Smart File Organization for Windows")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(subtitle)
        
        # Folder selection group
        folder_group = self._create_folder_selection_group()
        main_layout.addWidget(folder_group)
        
        # Profile and options group
        options_group = self._create_options_group()
        main_layout.addWidget(options_group)
        
        # Preview area
        preview_group = self._create_preview_group()
        main_layout.addWidget(preview_group, stretch=1)
        
        # Action buttons
        button_layout = self._create_action_buttons()
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def _create_folder_selection_group(self) -> QGroupBox:
        """Create folder selection controls."""
        
        group = QGroupBox("Select Folder to Organize")
        layout = QHBoxLayout()
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(self.folder_label, stretch=1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_folder)
        layout.addWidget(self.browse_btn)
        
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self._analyze_folder)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create organization options controls."""
        
        group = QGroupBox("Organization Options")
        layout = QHBoxLayout()
        
        # Profile selection
        profile_label = QLabel("Profile:")
        layout.addWidget(profile_label)
        
        self.profile_combo = QComboBox()
        profiles = self.organizer.rule_engine.get_available_profiles()
        self.profile_combo.addItems([p.title() for p in profiles])
        self.profile_combo.setCurrentText("Downloads")
        layout.addWidget(self.profile_combo)
        
        layout.addStretch()
        
        # Preview checkbox
        self.preview_check = QCheckBox("Preview before organizing")
        self.preview_check.setChecked(True)
        layout.addWidget(self.preview_check)
        
        # AI mode (if available)
        if self.ai_classifier.enabled:
            self.ai_check = QCheckBox("Use AI classification")
            self.ai_check.setChecked(False)
            self.ai_check.setToolTip("Use local AI for smarter categorization (Pro feature)")
            layout.addWidget(self.ai_check)
        
        group.setLayout(layout)
        return group
    
    def _create_preview_group(self) -> QGroupBox:
        """Create preview table."""
        
        group = QGroupBox("Preview")
        layout = QVBoxLayout()
        
        # Info label
        self.info_label = QLabel("Select a folder and click Analyze to see what will be organized")
        self.info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.info_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(["File Name", "Category", "Size", "Target Folder"])
        
        # Set column widths
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.preview_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create main action buttons."""
        
        layout = QHBoxLayout()
        
        # Undo button
        self.undo_btn = QPushButton("⟲ Undo Last")
        self.undo_btn.clicked.connect(self._undo_last)
        self.undo_btn.setEnabled(False)
        layout.addWidget(self.undo_btn)
        
        layout.addStretch()
        
        # Organize button
        self.organize_btn = QPushButton("🗂 Organize Folder")
        self.organize_btn.clicked.connect(self._organize_folder)
        self.organize_btn.setEnabled(False)
        self.organize_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.organize_btn)
        
        return layout
    
    def _set_default_folder(self):
        """Set default folder from config."""
        default = self.config.get('organization', {}).get('default_folder', 'Downloads')
        
        if default == 'Downloads':
            downloads_path = Path.home() / 'Downloads'
            if downloads_path.exists():
                self.current_folder = downloads_path
                self.folder_label.setText(str(self.current_folder))
                self.analyze_btn.setEnabled(True)
    
    def _browse_folder(self):
        """Browse for folder to organize."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Organize",
            str(self.current_folder) if self.current_folder else str(Path.home())
        )
        
        if folder:
            self.current_folder = Path(folder)
            self.folder_label.setText(str(self.current_folder))
            self.analyze_btn.setEnabled(True)
            self.organize_btn.setEnabled(False)
            logger.info(f"Folder selected: {self.current_folder}")
    
    def _analyze_folder(self):
        """Analyze the selected folder."""
        if not self.current_folder:
            return
        
        try:
            self.statusBar().showMessage("Analyzing folder...")
            self.analyze_btn.setEnabled(False)
            
            # Get analysis
            analysis = self.organizer.analyze_folder(self.current_folder)
            
            # Update info label
            self.info_label.setText(
                f"Found {analysis['total_files']} files "
                f"({self._format_size(analysis['total_size'])})"
            )
            
            # Get preview
            profile = self.profile_combo.currentText().lower()
            self.current_preview = self.organizer.preview_organization(
                self.current_folder,
                profile=profile
            )
            
            # Update table
            self._update_preview_table(self.current_preview)
            
            # Enable organize button
            self.organize_btn.setEnabled(len(self.current_preview) > 0)
            
            self.statusBar().showMessage(f"Analysis complete: {len(self.current_preview)} files will be organized")
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to analyze folder:\n{e}")
        finally:
            self.analyze_btn.setEnabled(True)
    
    def _update_preview_table(self, operations):
        """Update the preview table with operations."""
        
        self.preview_table.setRowCount(len(operations))
        
        for i, op in enumerate(operations):
            # File name
            name_item = QTableWidgetItem(op['source'].name)
            self.preview_table.setItem(i, 0, name_item)
            
            # Category
            category_item = QTableWidgetItem(op['category'])
            self.preview_table.setItem(i, 1, category_item)
            
            # Size
            size_item = QTableWidgetItem(self._format_size(op['size']))
            self.preview_table.setItem(i, 2, size_item)
            
            # Target folder
            target_item = QTableWidgetItem(op['target'].parent.name)
            self.preview_table.setItem(i, 3, target_item)
    
    def _organize_folder(self):
        """Execute folder organization."""
        if not self.current_folder or not self.current_preview:
            return
        
        # Confirm if preview is enabled
        if self.preview_check.isChecked():
            reply = QMessageBox.question(
                self,
                "Confirm Organization",
                f"Organize {len(self.current_preview)} files into categorized folders?\n\n"
                "You can undo this operation afterwards.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Disable controls
        self._set_controls_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.current_preview))
        self.statusBar().showMessage("Organizing files...")
        
        # Start organization in background thread
        profile = self.profile_combo.currentText().lower()
        self.organize_thread = OrganizeThread(
            self.organizer,
            self.current_folder,
            profile,
            dry_run=False
        )
        self.organize_thread.finished.connect(self._on_organize_finished)
        self.organize_thread.error.connect(self._on_organize_error)
        self.organize_thread.start()
    
    def _on_organize_finished(self, result):
        """Handle organization completion."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        if result['success']:
            QMessageBox.information(
                self,
                "Success",
                f"Successfully organized {result['completed']} files!\n\n"
                "You can undo this operation if needed."
            )
            
            self.undo_btn.setEnabled(result['can_undo'])
            self.statusBar().showMessage(f"Organization complete: {result['completed']} files organized")
            
            # Clear preview
            self.current_preview = []
            self.preview_table.setRowCount(0)
            self.organize_btn.setEnabled(False)
            
        else:
            QMessageBox.warning(
                self,
                "Partial Success",
                f"Organized {result['completed']} files.\n"
                f"{result['failed']} files failed."
            )
    
    def _on_organize_error(self, error):
        """Handle organization error."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        QMessageBox.critical(self, "Error", f"Organization failed:\n{error}")
        self.statusBar().showMessage("Organization failed")
    
    def _undo_last(self):
        """Undo last organization."""
        reply = QMessageBox.question(
            self,
            "Confirm Undo",
            "Undo the last organization operation?\n\n"
            "Files will be moved back to their original locations.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.statusBar().showMessage("Undoing...")
            success = self.organizer.undo_last_operation()
            
            if success:
                QMessageBox.information(self, "Success", "Operation undone successfully!")
                self.undo_btn.setEnabled(False)
                self.statusBar().showMessage("Undo complete")
            else:
                QMessageBox.warning(self, "Warning", "Failed to undo operation completely.")
                
        except Exception as e:
            logger.error(f"Undo error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to undo:\n{e}")
    
    def _set_controls_enabled(self, enabled: bool):
        """Enable/disable controls during operation."""
        self.browse_btn.setEnabled(enabled)
        self.analyze_btn.setEnabled(enabled)
        self.organize_btn.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)
        self.preview_check.setEnabled(enabled)
    
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
