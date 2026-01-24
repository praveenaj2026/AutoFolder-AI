"""
Main Window - AutoFolder AI v2.0

Simplified, modern UI with auto-analysis and smart organization.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor

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
    
    def __init__(self, organizer, folder_path, dry_run=False):
        super().__init__()
        self.organizer = organizer
        self.folder_path = folder_path
        self.dry_run = dry_run
    
    def run(self):
        try:
            # Use downloads profile (most comprehensive)
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
    """Main application window with simplified, modern UI."""
    
    def __init__(self, config: ConfigManager):
        super().__init__()
        
        self.config = config
        
        # Force AI to be enabled
        config.config['ai']['enabled'] = True
        
        self.organizer = FileOrganizer(config.config)
        self.ai_classifier = AIClassifier(config.config)
        
        self.current_folder: Optional[Path] = None
        self.current_preview = []
        self.organize_thread: Optional[OrganizeThread] = None
        
        self._init_ui()
        self._apply_modern_style()
        
        logger.info("Main window initialized with simplified UI")
    
    def _init_ui(self):
        """Initialize the modern, simplified user interface."""
        
        # Window settings
        app_config = self.config.get('app', {})
        self.setWindowTitle(f"{app_config.get('name', 'AutoFolder AI')} - v{app_config.get('version', '1.0.0')}")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Folder selection (simplified - auto-analyzes)
        folder_group = self._create_folder_selection()
        main_layout.addWidget(folder_group)
        
        # Preview area (auto-populated)
        preview_group = self._create_preview_area()
        main_layout.addWidget(preview_group, stretch=1)
        
        # Action buttons (simplified)
        button_layout = self._create_action_buttons()
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready • AI-Powered Smart Organization")
        
    def _create_header(self) -> QWidget:
        """Create modern header."""
        header_widget = QWidget()
        header_widget.setFixedHeight(100)
        
        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("AutoFolder AI")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("🤖 AI-Powered Smart File Organization")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #555;")
        layout.addWidget(subtitle)
        
        return header_widget
    
    def _create_folder_selection(self) -> QGroupBox:
        """Create simplified folder selection (auto-analyzes on browse)."""
        
        group = QGroupBox("📁 Select Folder")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # Folder path display
        self.folder_label = QLabel("No folder selected - Click Browse to get started")
        self.folder_label.setStyleSheet("""
            QLabel {
                padding: 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 13px;
                color: #495057;
            }
        """)
        layout.addWidget(self.folder_label, stretch=1)
        
        # Browse button (triggers auto-analysis)
        self.browse_btn = QPushButton("📂 Browse")
        self.browse_btn.clicked.connect(self._browse_and_analyze)
        self.browse_btn.setFixedHeight(45)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 25px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(self.browse_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_preview_area(self) -> QGroupBox:
        """Create modern preview area."""
        
        group = QGroupBox("📋 Preview - What Will Be Organized")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Info label
        self.info_label = QLabel("Browse a folder to see intelligent organization preview")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                padding: 12px;
                background-color: #f8f9fa;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.info_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(["📄 File Name", "🏷️ Category", "📦 Size", "📁 Destination"])
        
        # Modern table styling
        self.preview_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
        """)
        
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
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create simplified action buttons."""
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Undo button
        self.undo_btn = QPushButton("⟲ Undo Last")
        self.undo_btn.clicked.connect(self._undo_last)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(50)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.undo_btn)
        
        layout.addStretch()
        
        # Organize button (primary action)
        self.organize_btn = QPushButton("✨ Smart Organize")
        self.organize_btn.clicked.connect(self._organize_folder)
        self.organize_btn.setEnabled(False)
        self.organize_btn.setFixedHeight(50)
        self.organize_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #0d6efd, stop:1 #0b5ed7);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 50px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #0b5ed7, stop:1 #0a58ca);
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.organize_btn)
        
        return layout
    
    def _apply_modern_style(self):
        """Apply modern application-wide styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QStatusBar {
                background-color: #f8f9fa;
                color: #495057;
                border-top: 1px solid #dee2e6;
                font-size: 12px;
            }
        """)
    
    def _browse_and_analyze(self):
        """Browse for folder and immediately analyze (simplified single-step)."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Organize",
            str(self.current_folder) if self.current_folder else str(Path.home() / 'Downloads')
        )
        
        if folder:
            self.current_folder = Path(folder)
            self.folder_label.setText(str(self.current_folder))
            logger.info(f"Folder selected: {self.current_folder}")
            
            # Immediately analyze (auto-preview)
            self._analyze_folder()
    
    def _analyze_folder(self):
        """Analyze the selected folder with AI."""
        if not self.current_folder:
            return
        
        try:
            self.statusBar().showMessage("🤖 AI analyzing folder...")
            self.browse_btn.setEnabled(False)
            
            # Get analysis
            analysis = self.organizer.analyze_folder(self.current_folder)
            
            # Update info label
            self.info_label.setText(
                f"✅ Found {analysis['total_files']} files "
                f"({self._format_size(analysis['total_size'])}) • "
                f"AI Smart Organization Ready"
            )
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #155724;
                    padding: 12px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
            
            # Get preview with smart profile
            self.current_preview = self.organizer.preview_organization(
                self.current_folder,
                profile='downloads'
            )
            
            # Update table
            self._update_preview_table(self.current_preview)
            
            # Enable organize button
            self.organize_btn.setEnabled(len(self.current_preview) > 0)
            
            self.statusBar().showMessage(
                f"✅ Ready to organize {len(self.current_preview)} files • AI-Powered Smart Categories"
            )
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            QMessageBox.critical(self, "❌ Error", f"Failed to analyze folder:\n\n{e}")
        finally:
            self.browse_btn.setEnabled(True)
    
    def _update_preview_table(self, operations):
        """Update the preview table with operations."""
        
        self.preview_table.setRowCount(len(operations))
        
        for i, op in enumerate(operations):
            # File name
            name_item = QTableWidgetItem(op['source'].name)
            self.preview_table.setItem(i, 0, name_item)
            
            # Category (capitalized)
            category_item = QTableWidgetItem(op['category'].title())
            category_item.setForeground(QColor("#0d6efd"))
            self.preview_table.setItem(i, 1, category_item)
            
            # Size
            size_item = QTableWidgetItem(self._format_size(op['size']))
            self.preview_table.setItem(i, 2, size_item)
            
            # Target folder
            target_item = QTableWidgetItem(op['target'].parent.name)
            target_item.setForeground(QColor("#28a745"))
            self.preview_table.setItem(i, 3, target_item)
    
    def _organize_folder(self):
        """Execute smart organization."""
        if not self.current_folder or not self.current_preview:
            return
        
        # Always confirm
        reply = QMessageBox.question(
            self,
            "✨ Confirm Smart Organization",
            f"<b>Smart Organize {len(self.current_preview)} files?</b><br><br>"
            f"Files will be organized into intelligent categories using AI.<br>"
            f"<i>You can undo this anytime.</i>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Disable controls
        self._set_controls_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.current_preview))
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("🚀 Organizing files with AI...")
        
        # Start organization in background thread
        self.organize_thread = OrganizeThread(
            self.organizer,
            self.current_folder,
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
                "✅ Success!",
                f"<b>Successfully organized {result['completed']} files!</b><br><br>"
                f"Your files are now smartly categorized.<br>"
                f"<i>Click 'Undo Last' if you want to revert.</i>"
            )
            
            self.undo_btn.setEnabled(result['can_undo'])
            self.statusBar().showMessage(
                f"✅ Organization complete: {result['completed']} files organized perfectly!"
            )
            
            # Clear preview
            self.current_preview = []
            self.preview_table.setRowCount(0)
            self.organize_btn.setEnabled(False)
            self.info_label.setText("Organization complete! Browse another folder to continue.")
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    padding: 12px;
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    font-size: 13px;
                }
            """)
            
        else:
            QMessageBox.warning(
                self,
                "⚠️ Partial Success",
                f"Organized {result['completed']} files.<br>"
                f"{result['failed']} files could not be organized."
            )
    
    def _on_organize_error(self, error):
        """Handle organization error."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        QMessageBox.critical(self, "❌ Error", f"Organization failed:\n\n{error}")
        self.statusBar().showMessage("❌ Organization failed")
    
    def _undo_last(self):
        """Undo last organization with improved feedback."""
        reply = QMessageBox.question(
            self,
            "⟲ Confirm Undo",
            "<b>Undo the last organization?</b><br><br>"
            "Files will be moved back to their original locations.<br>"
            "Empty folders created during organization will be removed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.statusBar().showMessage("⟲ Undoing organization...")
            
            # Get undo info before undoing
            undo_manager = self.organizer.undo_manager
            if undo_manager.can_undo():
                last_operation = undo_manager.operations[-1]
                file_count = len(last_operation.get('files', []))
                
                # Perform undo
                success = self.organizer.undo_last_operation()
                
                if success:
                    # Clean up empty folders
                    self._cleanup_empty_folders(self.current_folder)
                    
                    QMessageBox.information(
                        self, 
                        "✅ Undo Complete", 
                        f"<b>Successfully undone!</b><br><br>"
                        f"• Moved {file_count} files back to original locations<br>"
                        f"• Removed empty folders"
                    )
                    self.undo_btn.setEnabled(False)
                    self.statusBar().showMessage(f"✅ Undo complete: {file_count} files restored")
                else:
                    QMessageBox.warning(
                        self, 
                        "⚠️ Warning", 
                        "Undo partially completed. Some files may not have been restored."
                    )
            else:
                QMessageBox.information(self, "ℹ️ Info", "Nothing to undo.")
                
        except Exception as e:
            logger.error(f"Undo error: {e}", exc_info=True)
            QMessageBox.critical(self, "❌ Error", f"Failed to undo:\n\n{e}")
    
    def _cleanup_empty_folders(self, base_folder: Path):
        """Remove empty folders created during organization."""
        try:
            for item in base_folder.iterdir():
                if item.is_dir():
                    # Recursively clean subdirectories first
                    self._cleanup_empty_folders(item)
                    
                    # Remove if empty
                    if not any(item.iterdir()):
                        logger.info(f"Removing empty folder: {item}")
                        item.rmdir()
        except Exception as e:
            logger.warning(f"Error cleaning up folder {base_folder}: {e}")
    
    def _set_controls_enabled(self, enabled: bool):
        """Enable/disable controls during operation."""
        self.browse_btn.setEnabled(enabled)
        self.organize_btn.setEnabled(enabled and len(self.current_preview) > 0)
        self.undo_btn.setEnabled(enabled and self.organizer.undo_manager.can_undo())
    
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
