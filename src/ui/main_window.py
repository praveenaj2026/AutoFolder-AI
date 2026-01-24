"""
Main Window - AutoFolder AI v2.0

Modern dark theme UI with improved functionality.
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
    """Main application window with modern dark theme."""
    
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
        self._apply_dark_theme()
        
        logger.info("Main window initialized with dark theme UI")
    
    def _init_ui(self):
        """Initialize the modern dark-themed user interface."""
        
        # Window settings
        app_config = self.config.get('app', {})
        self.setWindowTitle(f"{app_config.get('name', 'AutoFolder AI')} - v{app_config.get('version', '1.0.0')}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(900, 650)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Folder selection
        folder_group = self._create_folder_selection()
        main_layout.addWidget(folder_group)
        
        # Preview area
        preview_group = self._create_preview_area()
        main_layout.addWidget(preview_group, stretch=1)
        
        # Action buttons
        button_layout = self._create_action_buttons()
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.statusBar().showMessage("🚀 Ready • AI-Powered Smart Organization")
        
    def _create_header(self) -> QWidget:
        """Create modern header."""
        header_widget = QWidget()
        header_widget.setFixedHeight(110)
        
        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)
        
        # Title
        title = QLabel("AutoFolder AI")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("🤖 AI-Powered Smart File & Folder Organization")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #b0b0b0;")
        layout.addWidget(subtitle)
        
        return header_widget
    
    def _create_folder_selection(self) -> QGroupBox:
        """Create folder selection group."""
        
        group = QGroupBox("📁 Select Folder to Organize")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #ffffff;
                padding: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                margin-top: 12px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 8px;
                background-color: #2a2a2a;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Folder path display
        self.folder_label = QLabel("No folder selected - Click Browse to get started")
        self.folder_label.setStyleSheet("""
            QLabel {
                padding: 14px;
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                font-size: 13px;
                color: #c0c0c0;
            }
        """)
        layout.addWidget(self.folder_label, stretch=1)
        
        # Browse button
        self.browse_btn = QPushButton("📂 Browse")
        self.browse_btn.clicked.connect(self._browse_and_analyze)
        self.browse_btn.setFixedHeight(48)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """)
        layout.addWidget(self.browse_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_preview_area(self) -> QGroupBox:
        """Create preview area with table."""
        
        group = QGroupBox("📋 Preview - Smart Organization Plan")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #ffffff;
                padding: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                margin-top: 12px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 8px;
                background-color: #2a2a2a;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Info label
        self.info_label = QLabel("Browse a folder to see intelligent organization preview")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                padding: 14px;
                background-color: #1e1e1e;
                border-radius: 8px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.info_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(["📄 File/Folder Name", "🏷️ Category", "📦 Size", "📁 Destination"])
        
        # Dark theme table styling
        self.preview_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                background-color: #1e1e1e;
                gridline-color: #3d3d3d;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2d2d2d;
            }
            QTableWidget::item:selected {
                background-color: #2d5a8f;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #3d3d3d;
                font-weight: bold;
                color: #ffffff;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #505050;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606060;
            }
        """)
        
        # Set column widths
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Hide row numbers (vertical header) - fixes black box issue
        self.preview_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.preview_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                text-align: center;
                height: 28px;
                background-color: #1e1e1e;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        
        layout = QHBoxLayout()
        layout.setSpacing(18)
        
        # Undo button
        self.undo_btn = QPushButton("⟲ Undo Last")
        self.undo_btn.clicked.connect(self._undo_last)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(55)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 14px 35px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
        """)
        layout.addWidget(self.undo_btn)
        
        layout.addStretch()
        
        # Organize button (primary action)
        self.organize_btn = QPushButton("✨ Smart Organize")
        self.organize_btn.clicked.connect(self._organize_folder)
        self.organize_btn.setEnabled(False)
        self.organize_btn.setFixedHeight(55)
        self.organize_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                font-size: 17px;
                font-weight: bold;
                padding: 14px 55px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1E88E5, stop:1 #1565C0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1565C0, stop:1 #0D47A1);
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
        """)
        layout.addWidget(self.organize_btn)
        
        return layout
    
    def _apply_dark_theme(self):
        """Apply dark theme to entire application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QStatusBar {
                background-color: #2a2a2a;
                color: #b0b0b0;
                border-top: 1px solid #3d3d3d;
                font-size: 12px;
                padding: 5px;
            }
            QMessageBox {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #404040;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #505050;
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
                    background-color: #1e1e1e;
                    border: 1px solid #4CAF50;
                    border-radius: 8px;
                    font-size: 13px;
                    color: #4CAF50;
                    font-weight: bold;
                }
            """)
            logger.info(f"Folder selected: {self.current_folder}")
            
            # Immediately analyze
            self._analyze_folder()
    
    def _analyze_folder(self):
        """Analyze the selected folder with AI."""
        if not self.current_folder:
            return
        
        try:
            self.statusBar().showMessage("🤖 AI analyzing folder and subfolders...")
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
                    color: #4CAF50;
                    padding: 14px;
                    background-color: #1a3a1a;
                    border: 1px solid #4CAF50;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
            
            # Get preview
            self.current_preview = self.organizer.preview_organization(
                self.current_folder,
                profile='downloads'
            )
            
            # Update table
            self._update_preview_table(self.current_preview)
            
            # Enable organize button
            self.organize_btn.setEnabled(len(self.current_preview) > 0)
            
            self.statusBar().showMessage(
                f"✅ Ready to organize {len(self.current_preview)} items • AI-Powered Smart Categories"
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
            # File/Folder name (FIXED - now shows names!)
            name_item = QTableWidgetItem(op['source'].name)
            name_item.setForeground(QColor("#ffffff"))
            self.preview_table.setItem(i, 0, name_item)
            
            # Category
            category_item = QTableWidgetItem(op['category'].title())
            category_item.setForeground(QColor("#64B5F6"))  # Light blue
            self.preview_table.setItem(i, 1, category_item)
            
            # Size
            size_item = QTableWidgetItem(self._format_size(op['size']))
            size_item.setForeground(QColor("#FFB74D"))  # Orange
            self.preview_table.setItem(i, 2, size_item)
            
            # Target folder
            target_item = QTableWidgetItem(op['target'].parent.name)
            target_item.setForeground(QColor("#81C784"))  # Green
            self.preview_table.setItem(i, 3, target_item)
    
    def _organize_folder(self):
        """Execute smart organization."""
        if not self.current_folder or not self.current_preview:
            return
        
        # Always confirm
        reply = QMessageBox.question(
            self,
            "✨ Confirm Smart Organization",
            f"<b style='color:#ffffff;'>Smart Organize {len(self.current_preview)} items?</b><br><br>"
            f"<span style='color:#b0b0b0;'>Files and folders will be organized into intelligent categories using AI.</span><br>"
            f"<span style='color:#81C784;'><i>You can undo this anytime.</i></span>",
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
        self.statusBar().showMessage("🚀 Organizing files and folders with AI...")
        
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
        """Handle organization completion with popup."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        # POPUP CONFIRMATION (as requested!)
        if result['success']:
            QMessageBox.information(
                self,
                "✅ Success!",
                f"<h3 style='color:#4CAF50;'>Successfully organized {result['completed']} items!</h3>"
                f"<p style='color:#ffffff;'>Your files and folders are now smartly categorized.</p>"
                f"<p style='color:#81C784;'><i>Click 'Undo Last' if you want to revert.</i></p>"
            )
            
            self.undo_btn.setEnabled(result['can_undo'])
            self.statusBar().showMessage(
                f"✅ Organization complete: {result['completed']} items organized perfectly!"
            )
            
            # Clear preview
            self.current_preview = []
            self.preview_table.setRowCount(0)
            self.organize_btn.setEnabled(False)
            self.info_label.setText("🎉 Organization complete! Browse another folder to continue.")
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #b0b0b0;
                    padding: 14px;
                    background-color: #1e1e1e;
                    border-radius: 8px;
                    font-size: 13px;
                }
            """)
            
        else:
            # FAILED POPUP (as requested!)
            QMessageBox.warning(
                self,
                "⚠️ Partial Success",
                f"<h3 style='color:#FFA726;'>Partially completed</h3>"
                f"<p style='color:#ffffff;'>Organized {result['completed']} items.</p>"
                f"<p style='color:#EF5350;'>{result['failed']} items could not be organized.</p>"
            )
    
    def _on_organize_error(self, error):
        """Handle organization error with popup."""
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        # ERROR POPUP (as requested!)
        QMessageBox.critical(
            self, 
            "❌ Error", 
            f"<h3 style='color:#EF5350;'>Organization Failed</h3>"
            f"<p style='color:#ffffff;'>{error}</p>"
        )
        self.statusBar().showMessage("❌ Organization failed")
    
    def _undo_last(self):
        """Undo last organization with improved feedback."""
        reply = QMessageBox.question(
            self,
            "⟲ Confirm Undo",
            "<b style='color:#ffffff;'>Undo the last organization?</b><br><br>"
            "<span style='color:#b0b0b0;'>Files and folders will be moved back to their original locations.</span><br>"
            "<span style='color:#FFA726;'>Empty folders created during organization will be removed.</span>",
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
                last_operation = undo_manager.get_last_operation()
                file_count = len(last_operation.get('operations', []))
                
                # Perform undo
                success = self.organizer.undo_last_operation()
                
                if success:
                    # Clean up empty folders
                    if self.current_folder:
                        self._cleanup_empty_folders(self.current_folder)
                    
                    # SUCCESS POPUP
                    QMessageBox.information(
                        self, 
                        "✅ Undo Complete", 
                        f"<h3 style='color:#4CAF50;'>Successfully undone!</h3>"
                        f"<p style='color:#ffffff;'>• Moved {file_count} items back to original locations</p>"
                        f"<p style='color:#ffffff;'>• Removed empty folders</p>"
                    )
                    self.undo_btn.setEnabled(False)
                    self.statusBar().showMessage(f"✅ Undo complete: {file_count} items restored")
                else:
                    QMessageBox.warning(
                        self, 
                        "⚠️ Warning", 
                        "<p style='color:#FFA726;'>Undo partially completed.</p>"
                        "<p style='color:#ffffff;'>Some items may not have been restored.</p>"
                    )
            else:
                QMessageBox.information(
                    self, 
                    "ℹ️ Info", 
                    "<p style='color:#64B5F6;'>Nothing to undo.</p>"
                )
                
        except Exception as e:
            logger.error(f"Undo error: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "❌ Error", 
                f"<h3 style='color:#EF5350;'>Failed to undo</h3>"
                f"<p style='color:#ffffff;'>{e}</p>"
            )
    
    def _cleanup_empty_folders(self, base_folder: Path):
        """Remove empty folders created during organization."""
        try:
            for item in base_folder.iterdir():
                if item.is_dir():
                    # Recursively clean subdirectories first
                    self._cleanup_empty_folders(item)
                    
                    # Remove if empty
                    try:
                        if not any(item.iterdir()):
                            logger.info(f"Removing empty folder: {item}")
                            item.rmdir()
                    except:
                        pass  # Skip if can't remove
        except Exception as e:
            logger.warning(f"Error cleaning up folder {base_folder}: {e}")
    
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
