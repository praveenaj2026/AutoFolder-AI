"""
Main Window - AutoFolder AI v2.0

Modern blueish theme UI with multi-level organization.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QGroupBox, QHeaderView, QCheckBox, QProgressDialog,
    QFileIconProvider, QMenuBar, QMenu, QTabWidget, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QFileInfo
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QAction

try:
    from ..core import FileOrganizer
    from ..ai import AIClassifier
    from ..utils.config_manager import ConfigManager
    from ..utils.icon_manager import IconManager
    from ..utils.folder_icon_manager import FolderIconManager
    from .theme_helper import ThemeHelper
    from .duplicate_dialog import DuplicateDialog
    from .stats_dialog import StatsDialog
    from .search_dialog import SearchDialog
    from .compression_dialog import CompressionDialog
except ImportError:
    from core import FileOrganizer
    from ai import AIClassifier
    from utils.config_manager import ConfigManager
    from utils.icon_manager import IconManager
    from utils.folder_icon_manager import FolderIconManager
    from ui.theme_helper import ThemeHelper
    from ui.duplicate_dialog import DuplicateDialog
    from ui.stats_dialog import StatsDialog
    from ui.search_dialog import SearchDialog
    from ui.compression_dialog import CompressionDialog


logger = logging.getLogger(__name__)


class OrganizeThread(QThread):
    """Background thread for organization operations."""
    
    progress = Signal(int, int, str)  # current, total, status
    finished = Signal(dict)  # result
    error = Signal(str)  # error message
    
    def __init__(self, organizer, folder_path, dry_run=False):
        super().__init__()
        self.organizer = organizer
        self.folder_path = folder_path
        self.dry_run = dry_run
    
    def _progress_callback(self, current, total, status=""):
        """Progress callback that emits signal."""
        logger.debug(f"🔔 THREAD: _progress_callback({current}, {total}, '{status}')")
        self.progress.emit(current, total, status)
        logger.debug(f"✅ THREAD: Signal emitted")
    
    def run(self):
        try:
            result = self.organizer.organize_folder(
                self.folder_path,
                profile='downloads',
                dry_run=self.dry_run,
                progress_callback=self._progress_callback
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
        
        # File icon provider for thumbnails
        self.icon_provider = QFileIconProvider()
        
        self._init_ui()
        self._apply_blue_theme()
        
        # Set custom application icon
        self.setWindowIcon(IconManager.get_app_icon())
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        logger.info("Main window initialized with blueish theme")
    
    def _init_ui(self):
        """Initialize the modern blueish-themed user interface."""
        
        app_config = self.config.get('app', {})
        self.setWindowTitle(f"{app_config.get('name', 'AutoFolder AI')} - v{app_config.get('version', '1.0.0')}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(900, 650)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create prominent status overlay (initially hidden)
        self.status_overlay = QLabel(central_widget)
        self.status_overlay.setAlignment(Qt.AlignCenter)
        self.status_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(59, 130, 246, 0.95);
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 30px;
                border-radius: 15px;
                border: 3px solid #1E40AF;
            }
        """)
        self.status_overlay.setVisible(False)
        self.status_overlay.raise_()  # Bring to front
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Create tab widget for Organize and Tools pages
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #3B82F6;
                border-radius: 8px;
                background-color: #F0F9FF;
            }
            QTabBar::tab {
                background-color: #DBEAFE;
                color: #1E3A8A;
                padding: 12px 30px;
                margin-right: 4px;
                border: 2px solid #3B82F6;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3B82F6;
                color: #F0F9FF;
            }
            QTabBar::tab:hover {
                background-color: #60A5FA;
                color: #1E3A8A;
            }
        """)
        
        # Tab 1: Organize (main functionality)
        organize_tab = self._create_organize_tab()
        self.tab_widget.addTab(organize_tab, "📂 Organize")
        
        # Tab 2: Tools (all secondary features)
        tools_tab = self._create_tools_tab()
        self.tab_widget.addTab(tools_tab, "🛠️ Tools")
        
        main_layout.addWidget(self.tab_widget)
        
        # Create menu bar (keep for keyboard shortcuts)
        self._create_menu_bar()
        
        self.statusBar().showMessage("🚀 Ready")
        
    def _create_header(self) -> QWidget:
        """Create compact header."""
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        
        layout = QVBoxLayout(header_widget)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(0)
        
        title = QLabel("AutoFolder AI")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1E3A8A;")
        layout.addWidget(title)
        
        return header_widget
    
    def _create_organize_tab(self) -> QWidget:
        """Create the main Organize tab with folder selection and preview."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Folder selection
        folder_group = self._create_folder_selection()
        layout.addWidget(folder_group)
        
        # Preview area (MAXIMUM SPACE!)
        preview_group = self._create_preview_area()
        layout.addWidget(preview_group, stretch=1)
        
        # AI options
        ai_options = self._create_ai_options()
        layout.addWidget(ai_options)
        
        # Action buttons (only Undo and Organize)
        button_layout = self._create_action_buttons()
        layout.addLayout(button_layout)
        
        return tab
    
    def _create_tools_tab(self) -> QWidget:
        """Create the Tools tab with all secondary features."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Tools header
        tools_header = QLabel("🛠️ All Tools")
        tools_header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1E3A8A;
            padding: 10px;
        """)
        layout.addWidget(tools_header)
        
        # Tool buttons in a grid
        tools_grid = QHBoxLayout()
        tools_grid.setSpacing(15)
        
        # Column 1: File Management
        col1 = QVBoxLayout()
        col1_header = QLabel("📁 File Management")
        col1_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #3B82F6; margin-bottom: 10px;")
        col1.addWidget(col1_header)
        
        self.scan_duplicates_btn_tools = QPushButton("🔍 Scan for Duplicates")
        self.scan_duplicates_btn_tools.clicked.connect(self._scan_duplicates)
        self.scan_duplicates_btn_tools.setMinimumHeight(50)
        self.scan_duplicates_btn_tools.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: #1E3A8A;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        col1.addWidget(self.scan_duplicates_btn_tools)
        
        self.view_stats_btn_tools = QPushButton("📊 View Statistics")
        self.view_stats_btn_tools.clicked.connect(self._show_stats)
        self.view_stats_btn_tools.setMinimumHeight(50)
        self.view_stats_btn_tools.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: #F0F9FF;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        col1.addWidget(self.view_stats_btn_tools)
        col1.addStretch()
        
        # Column 2: AI Features
        col2 = QVBoxLayout()
        col2_header = QLabel("🔍 Find & Organize")
        col2_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #3B82F6; margin-bottom: 10px;")
        col2.addWidget(col2_header)
        
        self.search_files_btn_tools = QPushButton("🔍 Search Files")
        self.search_files_btn_tools.clicked.connect(self._open_search_dialog)
        self.search_files_btn_tools.setEnabled(False)
        self.search_files_btn_tools.setMinimumHeight(50)
        self.search_files_btn_tools.setStyleSheet("""
            QPushButton {
                background-color: #06B6D4;
                color: #1E3A8A;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0891B2;
            }
            QPushButton:disabled {
                background-color: #DBEAFE;
                color: #9CA3AF;
            }
        """)
        col2.addWidget(self.search_files_btn_tools)
        col2.addStretch()
        
        # Column 3: Storage Tools
        col3 = QVBoxLayout()
        col3_header = QLabel("💾 Storage Tools")
        col3_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #3B82F6; margin-bottom: 10px;")
        col3.addWidget(col3_header)
        
        self.compress_btn_tools = QPushButton("📦 Compress Old Files")
        self.compress_btn_tools.clicked.connect(self._open_compression_dialog)
        self.compress_btn_tools.setEnabled(False)
        self.compress_btn_tools.setMinimumHeight(50)
        self.compress_btn_tools.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #F0F9FF;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #DBEAFE;
                color: #9CA3AF;
            }
        """)
        col3.addWidget(self.compress_btn_tools)
        
        self.ai_stats_btn = QPushButton("🧠 AI Learning Stats")
        self.ai_stats_btn.clicked.connect(self._show_ai_learning_stats)
        self.ai_stats_btn.setMinimumHeight(50)
        self.ai_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #EC4899;
                color: #F0F9FF;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #DB2777;
            }
        """)
        col3.addWidget(self.ai_stats_btn)
        col3.addStretch()
        
        tools_grid.addLayout(col1)
        tools_grid.addLayout(col2)
        tools_grid.addLayout(col3)
        layout.addLayout(tools_grid)
        
        # Info text
        info_label = QLabel("💡 Tip: Use keyboard shortcuts from the Tools menu for quick access!")
        info_label.setStyleSheet("""
            color: #3B82F6;
            font-size: 13px;
            font-style: italic;
            padding: 15px;
            background-color: #EFF6FF;
            border-radius: 8px;
            border: 1px solid #DBEAFE;
        """)
        layout.addWidget(info_label)
        layout.addStretch()
        
        return tab
    
    def _create_folder_selection(self) -> QGroupBox:
        """Create folder selection group."""
        
        group = QGroupBox("📁 Select Folder to Organize")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 10px;
                border: 2px solid #93C5FD;
                border-radius: 8px;
                margin-top: 8px;
                background-color: #EFF6FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: #EFF6FF;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        self.folder_label = QLabel("No folder selected")
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
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["Original Name", "Type", "Category", "Size", "Destination"])
        
        # Enable context menu (right-click)
        self.preview_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview_table.customContextMenuRequested.connect(self._show_context_menu)
        
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
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Original Name - wide
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type - compact
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Size
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Destination
        
        # Configure selection behavior - DISABLE selection for cleaner look
        self.preview_table.setSelectionMode(QTableWidget.NoSelection)
        self.preview_table.setFocusPolicy(Qt.NoFocus)
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
        layout.setContentsMargins(0, 0, 0, 0)
        
        # AI Status label (always enabled)
        ai_status_label = QLabel("🤖 AI Semantic Grouping: ALWAYS ENABLED")
        ai_status_label.setStyleSheet("""
            QLabel {
                color: #059669;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                background-color: #D1FAE5;
                border-radius: 4px;
                border: 1px solid #10B981;
            }
        """)
        layout.addWidget(ai_status_label)
        
        # Phase 3.7: Content Analysis status
        self.content_analysis_label = QLabel("📄 Content Analysis: Checking...")
        self.content_analysis_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 10px;
                padding: 4px 8px;
                background-color: #F3F4F6;
                border-radius: 4px;
                margin-left: 8px;
            }
        """)
        layout.addWidget(self.content_analysis_label)
        
        # Update content analysis status after initialization
        self._update_content_analysis_status()
        
        layout.addStretch()
        
        return widget
    
    def _update_content_analysis_status(self):
        """Update the content analysis status label based on AI classifier status."""
        try:
            if hasattr(self, 'organizer') and hasattr(self.organizer, 'ai_classifier'):
                status = self.organizer.ai_classifier.get_status()
                content_status = status.get('content_analysis', {})
                
                pdf_ok = content_status.get('pdf_available', False)
                ocr_ok = content_status.get('ocr_available', False)
                
                if pdf_ok and ocr_ok:
                    self.content_analysis_label.setText("📄 Content Analysis: PDF ✓ OCR ✓")
                    self.content_analysis_label.setStyleSheet("""
                        QLabel {
                            color: #059669;
                            font-size: 10px;
                            font-weight: bold;
                            padding: 4px 8px;
                            background-color: #D1FAE5;
                            border-radius: 4px;
                            margin-left: 8px;
                        }
                    """)
                elif pdf_ok:
                    self.content_analysis_label.setText("📄 Content Analysis: PDF ✓ (OCR not installed)")
                    self.content_analysis_label.setStyleSheet("""
                        QLabel {
                            color: #D97706;
                            font-size: 10px;
                            padding: 4px 8px;
                            background-color: #FEF3C7;
                            border-radius: 4px;
                            margin-left: 8px;
                        }
                    """)
                else:
                    self.content_analysis_label.setText("📄 Content Analysis: Install PyMuPDF for better accuracy")
                    self.content_analysis_label.setStyleSheet("""
                        QLabel {
                            color: #6B7280;
                            font-size: 10px;
                            padding: 4px 8px;
                            background-color: #F3F4F6;
                            border-radius: 4px;
                            margin-left: 8px;
                        }
                    """)
            else:
                self.content_analysis_label.setText("📄 Content Analysis: Initializing...")
        except Exception as e:
            logger.debug(f"Content analysis status check failed: {e}")
            self.content_analysis_label.setText("📄 Content Analysis: N/A")
    
    def _create_menu_bar(self):
        """Create menu bar with Tools menu for secondary features."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #3B82F6;
                color: white;
                padding: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 15px;
            }
            QMenuBar::item:selected {
                background-color: #2563EB;
                border-radius: 4px;
            }
            QMenu {
                background-color: #EFF6FF;
                border: 2px solid #3B82F6;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 30px;
                color: #1E3A8A;
                font-size: 13px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #DBEAFE;
                color: #1E40AF;
            }
        """)
        
        # Tools menu
        tools_menu = menubar.addMenu("🛠️ Tools")
        
        # Scan for Duplicates
        scan_duplicates_action = QAction("🔍 Scan for Duplicates", self)
        scan_duplicates_action.setShortcut("Ctrl+D")
        scan_duplicates_action.triggered.connect(self._scan_duplicates)
        tools_menu.addAction(scan_duplicates_action)
        
        # View Stats
        view_stats_action = QAction("📊 View Statistics", self)
        view_stats_action.setShortcut("Ctrl+S")
        view_stats_action.triggered.connect(self._show_stats)
        tools_menu.addAction(view_stats_action)

        # Install OCR (Tesseract)
        install_ocr_action = QAction("📄 Install OCR (Tesseract)", self)
        install_ocr_action.triggered.connect(self._install_ocr_tesseract)
        tools_menu.addAction(install_ocr_action)
        
        tools_menu.addSeparator()
        
        # Edit AI Groups
        self.edit_ai_groups_action = QAction("🎨 Edit AI Groups", self)
        self.edit_ai_groups_action.setShortcut("Ctrl+E")
        self.edit_ai_groups_action.triggered.connect(self._open_ai_group_editor)
        self.edit_ai_groups_action.setEnabled(False)
        tools_menu.addAction(self.edit_ai_groups_action)
        
        # Search Files
        self.search_files_action = QAction("🔍 Search Files", self)
        self.search_files_action.setShortcut("Ctrl+F")
        self.search_files_action.triggered.connect(self._open_search_dialog)
        self.search_files_action.setEnabled(False)
        tools_menu.addAction(self.search_files_action)
        
        # Auto Schedule
        schedule_action = QAction("⏰ Auto Schedule", self)
        schedule_action.setShortcut("Ctrl+T")
        schedule_action.triggered.connect(self._open_scheduler_settings)
        tools_menu.addAction(schedule_action)

    def _install_ocr_tesseract(self):
        """Launch the bundled Tesseract installer (Windows) to enable OCR."""
        try:
            analyzer = None
            if hasattr(self, 'organizer') and hasattr(self.organizer, 'ai_classifier'):
                analyzer = getattr(self.organizer.ai_classifier, 'content_analyzer', None)

            if not analyzer:
                msg = QMessageBox(self)
                msg.setWindowTitle("OCR Not Available")
                msg.setText("Content analyzer is not available in this build.")
                msg.exec()
                return

            ok, message = analyzer.install_tesseract()
            msg = QMessageBox(self)
            msg.setWindowTitle("Install OCR (Tesseract)")
            msg.setText(message)
            msg.setIcon(QMessageBox.Information if ok else QMessageBox.Warning)
            msg.exec()

            # Re-check status (installer runs async; restart still required)
            try:
                analyzer.refresh_dependencies()
            except Exception:
                pass
            self._update_content_analysis_status()
        except Exception as e:
            logger.error(f"Failed to launch Tesseract installer: {e}")
            msg = QMessageBox(self)
            msg.setWindowTitle("Install Failed")
            msg.setText(f"Failed to start installer: {e}")
            msg.exec()
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        self.undo_btn = QPushButton("⟲ Undo Last")
        self.undo_btn.clicked.connect(self._undo_last)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(45)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #60A5FA;
                color: #1E3A8A;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 25px;
                border: none;
                border-radius: 8px;
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
        self.organize_btn.setFixedHeight(45)
        self.organize_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #2563EB, stop:1 #1E40AF);
                color: #F0F9FF;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 40px;
                border: none;
                border-radius: 8px;
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
            
            # Show loading dialog IMMEDIATELY before any processing
            self.loading_dialog = QProgressDialog(
                "⏳ Preparing to analyze folder...\n\nScanning files and folders...\n\nPlease wait, this may take a moment for large folders.",
                None,
                0,
                0,  # Indeterminate mode (0-0 = animated)
                self
            )
            self.loading_dialog.setWindowTitle("🔍 Analyzing Folder")
            self.loading_dialog.setWindowModality(Qt.WindowModal)
            self.loading_dialog.setMinimumDuration(0)
            self.loading_dialog.setMinimumSize(500, 200)
            self.loading_dialog.setStyleSheet("""
                QProgressDialog {
                    background-color: #EFF6FF;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                }
                QLabel {
                    color: #1E3A8A;
                    font-size: 14px;
                    padding: 10px;
                }
                QProgressBar {
                    text-align: center;
                    border: 2px solid #3B82F6;
                    border-radius: 5px;
                    background-color: #DBEAFE;
                }
                QProgressBar::chunk {
                    background-color: #3B82F6;
                }
            """)
            # Set range to 0,0 for indeterminate (animated) progress bar
            self.loading_dialog.setRange(0, 0)
            self.loading_dialog.setValue(0)
            self.loading_dialog.setAutoReset(False)
            self.loading_dialog.setAutoClose(False)
            
            # Center on screen
            screen_geo = self.screen().geometry()
            dialog_geo = self.loading_dialog.geometry()
            x = (screen_geo.width() - dialog_geo.width()) // 2
            y = (screen_geo.height() - dialog_geo.height()) // 2
            self.loading_dialog.move(x, y)
            
            self.loading_dialog.show()
            QApplication.processEvents()  # Force immediate display
            
            # Start analysis after dialog is shown
            QTimer.singleShot(50, self._analyze_folder)
    
    def _analyze_folder(self):
        """Analyze the selected folder with AI."""
        if not self.current_folder:
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()
            return
        
        try:
            # Update loading dialog
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.setLabelText(
                    f"📊 Scanning folder: {self.current_folder.name}\n\n"
                    "Counting files and analyzing folder structure...\n\n"
                    "⏳ Please wait, this process is working..."
                )
                QApplication.processEvents()
            
            self.statusBar().showMessage("🤖 AI analyzing folder and subfolders...")
            self.browse_btn.setEnabled(False)
            
            analysis = self.organizer.analyze_folder(self.current_folder)
            
            # Update loading dialog with file count
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.setLabelText(
                    f"✅ Found {analysis['total_files']:,} files ({self._format_size(analysis['total_size'])})\n\n"
                    "🤖 Creating AI organization preview...\n\n"
                    "Processing semantic groups and file categorization...\n\n"
                    "⏳ This may take a few moments for large folders."
                )
                QApplication.processEvents()
            
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
            
            # Continue to preview analysis
            QTimer.singleShot(100, lambda: self._run_preview_analysis(None))
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()
            
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("❌ Analysis Error")
            error_msg.setText(f"<h2 style='color:#DC2626;'>Failed to analyze folder</h2>")
            error_msg.setInformativeText(
                f"<p style='font-size:14px; color:#1E3A8A;'><b>Error:</b> {str(e)}</p>"
            )
            ThemeHelper.style_message_box(error_msg, 'error')
            error_msg.setStandardButtons(QMessageBox.Ok)
            error_msg.exec()
    
    def _run_preview_analysis(self, progress_dialog):
        """Run preview analysis and update UI."""
        try:
            # Define progress callback for preview phase
            def preview_progress(current, total, status=""):
                if hasattr(self, 'loading_dialog') and self.loading_dialog.isVisible():
                    self.loading_dialog.setLabelText(f"{status}\n\n⏳ Please wait...")
                    QApplication.processEvents()
                # Also show in status overlay
                if "Indexing" in status or "AI" in status:
                    self._show_status_overlay(status)
            
            self.current_preview, self.current_stats = self.organizer.preview_organization(
                self.current_folder,
                profile='downloads',
                progress_callback=preview_progress
            )
            
            # Close loading dialog
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()
            if progress_dialog:
                progress_dialog.close()
            
            self._update_preview_table(self.current_preview)
            
            # Enable organize button after preview is ready
            self.organize_btn.setEnabled(len(self.current_preview) > 0)
            
            # Enable Phase 3.6 feature menu actions after organization
            self.edit_ai_groups_action.setEnabled(len(self.current_preview) > 0)
            self.search_files_action.setEnabled(len(self.current_preview) > 0)
            
            # Enable Tools tab buttons
            self.search_files_btn_tools.setEnabled(len(self.current_preview) > 0)
            self.compress_btn_tools.setEnabled(len(self.current_preview) > 0)
            
            # Update status message - AI is always active
            self.statusBar().showMessage(
                f"✅ Ready to organize {len(self.current_preview)} items • 🤖 AI Semantic Grouping Active"
            )
            
        except Exception as e:
            # Close loading dialog on error
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()
            if progress_dialog:
                progress_dialog.close()
                
            logger.error(f"Preview generation error: {e}", exc_info=True)
            
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("❌ Analysis Error")
            error_msg.setText(f"<h2 style='color:#DC2626;'>Failed to analyze folder</h2>")
            error_msg.setInformativeText(
                f"<p style='font-size:14px; color:#1E3A8A;'><b>Error:</b> {str(e)}</p>"
            )
            ThemeHelper.style_message_box(error_msg, 'error')
            error_msg.setStandardButtons(QMessageBox.Ok)
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: #F0F9FF;
                }
                QLabel {
                    font-size: 14px;
                    min-width: 400px;
                    color: #1E3A8A;
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
    
    def _scan_duplicates(self):
        """Scan for duplicate files in selected folder."""
        if not self.current_folder:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("No Folder Selected")
            msg.setText("Please select a folder first using the Browse button.")
            ThemeHelper.style_message_box(msg)
            msg.exec_()
            return
        
        try:
            # Clear duplicate cache to ensure fresh scan
            logger.info("Clearing duplicate cache for fresh scan")
            if hasattr(self.organizer, 'duplicate_detector'):
                self.organizer.duplicate_detector.hash_cache.clear()
                self.organizer.duplicate_detector.size_cache.clear()
                logger.info("Cache cleared successfully")
            
            # Update status bar to show scanning in progress
            self.statusBar().showMessage("🔍 Scanning for duplicates... Please wait.")
            QApplication.processEvents()  # Force UI update
            
            # Get hash algorithm from config
            algorithm = self.config.config.get('duplicates', {}).get('hash_algorithm', 'sha256')
            
            # Scan for duplicates (no progress dialog - faster!)
            duplicates, stats = self.organizer.scan_for_duplicates(
                self.current_folder,
                algorithm=algorithm
            )
            
            # Restore status bar
            self.statusBar().showMessage("✅ Duplicate scan complete")
            
            if not duplicates:
                msg = QMessageBox(self)
                msg.setWindowTitle("✅ No Duplicates Found")
                msg.setText(f"<h3 style='color:#10B981;'>No duplicate files found!</h3>")
                msg.setInformativeText(
                    f"<p style='color:#1E3A8A;'>All files in <b>{self.current_folder.name}</b> are unique.</p>"
                )
                ThemeHelper.style_message_box(msg, 'success')
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #F0F9FF;
                    }
                    QLabel {
                        color: #1E3A8A;
                        font-size: 13px;
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
                msg.exec_()
                return
            
            # Show duplicate management dialog
            dialog = DuplicateDialog(duplicates, stats, self)
            dialog.duplicates_processed.connect(self._handle_duplicate_result)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Duplicate scan error: {e}", exc_info=True)
            error_box = QMessageBox(self)
            error_box.setIcon(QMessageBox.Critical)
            error_box.setWindowTitle("❌ Scan Error")
            error_box.setText("<h3 style='color:#EF4444;'>Failed to Scan Duplicates</h3>")
            error_box.setInformativeText(f"<p style='color:#1E3A8A;'><b>Error:</b> {str(e)}</p>")
            error_box.setStyleSheet("""
                QMessageBox {
                    background-color: #FEF2F2;
                }
                QLabel {
                    color: #1E3A8A;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #EF4444;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)
            error_box.exec_()
    
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
                
                # Show failed deletions (OneDrive issues)
                if result.get('failed_deletes'):
                    message += f"\n⚠️ Failed to delete {len(result['failed_deletes'])} files:\n"
                    for failed_path, reason in result['failed_deletes'][:5]:
                        file_name = Path(failed_path).name
                        message += f"  • {file_name} ({reason})\n"
                    if len(result['failed_deletes']) > 5:
                        message += f"  ... and {len(result['failed_deletes']) - 5} more\n"
                    message += "\n💡 Tip: Pause OneDrive sync or close programs using these files\n\n"
                
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
                    background-color: #F0F9FF;
                }
                QLabel {
                    font-size: 12px;
                    min-width: 350px;
                    max-width: 400px;
                    color: #1E3A8A;
                }
                QPushButton {
                    background-color: #10B981;
                    color: white;
                    padding: 6px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                    min-width: 70px;
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
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No Statistics")
            msg.setText("No statistics available. Please analyze a folder first.")
            ThemeHelper.style_message_box(msg)
            msg.exec_()
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
        
        # Limit display to first 200 items for better scroll performance
        display_limit = 200
        display_ops = operations[:display_limit]
        
        self.preview_table.setRowCount(len(display_ops))
        
        for i, op in enumerate(display_ops):
            # Validate operation is a dictionary
            if not isinstance(op, dict):
                logger.error(f"Operation at index {i} must be a dict, got {type(op)}")
                continue
            
            # File type with icon
            file_path = op['source']
            ext = file_path.suffix.lower().lstrip('.')
            
            # Determine file type category
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'tiff', 'raw', 'heic']:
                file_type = "Image"
            elif ext in ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'mpg', 'mpeg', 'm4v']:
                file_type = "Video"
            elif ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus']:
                file_type = "Audio"
            elif ext in ['pdf']:
                file_type = "PDF"
            elif ext in ['doc', 'docx', 'txt', 'rtf', 'odt']:
                file_type = "Document"
            elif ext in ['xls', 'xlsx', 'csv', 'ods']:
                file_type = "Spreadsheet"
            elif ext in ['ppt', 'pptx', 'odp']:
                file_type = "Presentation"
            elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']:
                file_type = "Archive"
            elif ext in ['exe', 'msi', 'dmg', 'app', 'deb', 'rpm']:
                file_type = "Installer"
            elif ext in ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'cs', 'php', 'rb', 'go', 'rs', 'swift']:
                file_type = "Code"
            else:
                file_type = ext.upper() if ext else "File"
            
            type_item = QTableWidgetItem()
            
            try:
                # Get system file icon
                file_info = QFileInfo(str(file_path))
                system_icon = self.icon_provider.icon(file_info)
                
                if not system_icon.isNull():
                    type_item.setIcon(system_icon)
                else:
                    # Fallback to emoji if system icon fails
                    emoji = self.FILE_TYPE_ICONS.get(ext, self.FILE_TYPE_ICONS['default'])
                    type_item.setText(emoji + " " + file_type)
                    type_item.setFont(QFont("Segoe UI", 10))
            except Exception as e:
                logger.debug(f"Failed to load icon for {file_path.name}: {e}")
                # Fallback to emoji
                emoji = self.FILE_TYPE_ICONS.get(ext, self.FILE_TYPE_ICONS['default'])
                type_item.setText(emoji + " " + file_type)
                type_item.setFont(QFont("Segoe UI", 10))
            
            # If icon loaded successfully, show text alongside icon
            if not type_item.icon().isNull():
                type_item.setText(file_type)
                type_item.setFont(QFont("Segoe UI", 10))
            
            # Column 0: Original name - sanitize to remove problematic characters
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
            self.preview_table.setItem(i, 0, name_item)
            
            # Column 1: Type (with icon)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setForeground(QColor("#1E3A8A"))
            self.preview_table.setItem(i, 1, type_item)
            
            # Column 2: Category
            category_item = QTableWidgetItem(op['category'].title())
            category_item.setForeground(QColor("#2563EB"))
            self.preview_table.setItem(i, 2, category_item)
            
            # Column 3: Size
            size_item = QTableWidgetItem(self._format_size(op['size']))
            size_item.setForeground(QColor("#7C3AED"))
            self.preview_table.setItem(i, 3, size_item)
            
            # Column 4: Target folder (showing nested structure with custom folder icon)
            if self.current_folder and op.get('target'):
                try:
                    target_path = str(op['target'].relative_to(self.current_folder))
                except (ValueError, AttributeError):
                    # Fallback if relative_to fails
                    target_path = str(op['target'])
            else:
                target_path = str(op.get('target', 'Unknown'))
            
            target_item = QTableWidgetItem(target_path)
            target_item.setForeground(QColor("#059669"))
            
            # Add custom folder icon based on category
            category = op['category'].title()
            folder_icon = FolderIconManager.get_folder_icon(category)
            target_item.setIcon(folder_icon)
            
            self.preview_table.setItem(i, 4, target_item)
        
        # Type column stays compact  
        self.preview_table.setColumnWidth(1, 100)
        
        # Disable selection highlight on type column to prevent black box
        for i in range(len(display_ops)):
            type_item = self.preview_table.item(i, 1)  # Type is now column 1
            if type_item:
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsSelectable)
        
        # Show message if there are more items
        if len(operations) > display_limit:
            logger.info(f"Showing first {display_limit} of {len(operations)} items in preview")
            self.statusBar().showMessage(
                f"⚠️ Showing first {display_limit} of {len(operations)} items for performance • All {len(operations)} will be organized"
            )
    
    def _organize_folder(self):
        """Execute smart organization."""
        if not self.current_folder or not self.current_preview:
            return
        
        reply = QMessageBox.question(
            self,
            "✨ Confirm Smart Organization",
            f"<b style='color:#1E3A8A;'>Smart Organize {len(self.current_preview)} items?</b><br><br>"
            f"<span style='color:#3B82F6;'>Multi-level organization: Category → AI Group → Type</span><br>"
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
        self.organize_thread.progress.connect(self._on_organize_progress)
        self.organize_thread.finished.connect(self._on_organize_finished)
        self.organize_thread.error.connect(self._on_organize_error)
        self.organize_thread.start()
    
    def _on_organize_progress(self, current, total, status=""):
        """Update progress bar during organization with prominent status display."""
        logger.debug(f"🎯 UI: _on_organize_progress({current}, {total}, '{status}')")
        percentage = int((current / total) * 100) if total > 0 else 0
        logger.debug(f"📊 UI: Setting progress bar to {current}, percentage={percentage}%")
        self.progress_bar.setValue(current)
        
        # Use custom status if provided (prominent display)
        if status:
            # Show in status bar
            self.statusBar().showMessage(f"⚡ {status}")
            self.statusBar().setStyleSheet("""
                QStatusBar {
                    background-color: #DBEAFE;
                    color: #1E40AF;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
            
            # Show prominent overlay for major steps — also briefly for per-file moves
            if any(keyword in status for keyword in ["Indexing", "AI", "Starting", "Saving", "Customizing"]):
                self._show_status_overlay(status)
            elif status.startswith("📁 Moving"):
                # Show brief overlay for moving messages (avoids invisible feedback)
                self._show_status_overlay(status)
            
            logger.info(f"📢 STATUS: {status}")
        else:
            # Default progress message
            self.statusBar().showMessage(
                f"🚀 Organizing... {current}/{total} files ({percentage}%)"
            )
        
        logger.debug(f"✅ UI: Progress bar and status updated")
        # Force immediate UI repaint
        self.progress_bar.repaint()
        self.statusBar().repaint()
        QApplication.processEvents()
        logger.debug(f"✅ UI: Forced repaint and event processing")
    
    def _show_status_overlay(self, message: str):
        """Show prominent status overlay message."""
        try:
            # Position overlay in center of window
            overlay_width = 600
            overlay_height = 150
            x = (self.width() - overlay_width) // 2
            y = (self.height() - overlay_height) // 2
            
            self.status_overlay.setGeometry(x, y, overlay_width, overlay_height)
            self.status_overlay.setText(message)
            self.status_overlay.setVisible(True)
            self.status_overlay.raise_()  # Bring to front
            self.status_overlay.repaint()
            QApplication.processEvents()
            
            # Auto-hide after 1.5 seconds for moving messages, keep longer for major steps
            if "Moving:" in message:
                QTimer.singleShot(800, lambda: self.status_overlay.setVisible(False))
            else:
                QTimer.singleShot(2000, lambda: self.status_overlay.setVisible(False))
        except Exception as e:
            logger.debug(f"Status overlay error: {e}")
    
    def _on_organize_finished(self, result):
        """Handle organization completion with popup."""
        self.status_overlay.setVisible(False)  # Hide overlay
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        
        if result['success']:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("✅ Success!")
            msg.setText(
                f"<h3 style='color:#059669;'>Successfully organized {result['completed']} items!</h3>"
                f"<p style='color:#1E3A8A;'>Multi-level organization complete (including subfolders).</p>"
                f"<p style='color:#3B82F6;'><i>Click 'Undo Last' if you want to revert.</i></p>"
            )
            ThemeHelper.style_message_box(msg)
            msg.exec_()
            
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
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Partial Success")
            msg.setText(
                f"<h3 style='color:#D97706;'>Partially completed</h3>"
                f"<p style='color:#1E3A8A;'>Organized {result['completed']} items.</p>"
                f"<p style='color:#DC2626;'>{result['failed']} items could not be organized.</p>"
                f"{success_details}"
                f"{error_details}"
            )
            ThemeHelper.style_message_box(msg)
            
            # Center the dialog on screen
            msg.adjustSize()
            screen_geo = self.screen().geometry()
            x = (screen_geo.width() - msg.width()) // 2
            y = (screen_geo.height() - msg.height()) // 2
            msg.move(x, y)
            
            msg.exec_()
    
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
                background-color: #FEF2F2;
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
        msg = QMessageBox(self)
        msg.setWindowTitle("⟲ Confirm Undo")
        msg.setText(
            "<b style='color:#1E3A8A;'>Undo the last organization?</b><br><br>"
            "<span style='color:#3B82F6;'>Items will be moved back to original locations.</span><br>"
            "<span style='color:#D97706;'>Empty folders will be removed.</span>"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        ThemeHelper.style_message_box(msg, 'question')
        reply = msg.exec()
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            undo_manager = self.organizer.undo_manager
            if not undo_manager.can_undo():
                return
            
            last_operation = undo_manager.get_last_operation()
            file_count = len(last_operation.get('operations', []))
            
            # Show progress dialog IMMEDIATELY BEFORE undo starts
            progress = QProgressDialog(
                f"⏳ Undoing organization...\n\n"
                f"Restoring {file_count} files to original locations...\n\n"
                f"⏳ Please wait...",
                None,  # No cancel button
                0, 0,  # Indeterminate progress
                self
            )
            progress.setWindowTitle("⏲️ Processing Undo")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)  # Show immediately
            progress.setMinimumSize(500, 200)  # Larger size for visibility
            progress.setStyleSheet("""
                QProgressDialog {
                    background-color: #EFF6FF;
                    border: 2px solid #3B82F6;
                    border-radius: 8px;
                }
                QLabel {
                    color: #1E3A8A;
                    font-size: 14px;
                    padding: 15px;
                }
                QProgressBar {
                    background-color: #DBEAFE;
                    border: 1px solid #3B82F6;
                    border-radius: 4px;
                    text-align: center;
                }
            """)
            progress.setValue(0)
            progress.forceShow()  # Force immediate display FIRST
            QApplication.processEvents()  # Process the forceShow
            progress.show()  # Then show normally
            QApplication.processEvents()  # Final update for visibility
            
            self.statusBar().showMessage("⏲️ Undoing organization...")
            
            # Perform undo NOW (after dialog is shown)
            success = self.organizer.undo_last_operation()
            
            # Close progress dialog
            progress.close()
            
            if success and self.current_folder:
                # PROPERLY clean up empty folders
                deleted_count = self._cleanup_empty_folders_recursive(self.current_folder)
                
                msg = QMessageBox(self)
                msg.setWindowTitle("✅ Undo Complete")
                ThemeHelper.style_message_box(msg, 'success')
                msg.setText(
                    f"<h3 style='color:#059669;'>Successfully undone!</h3>"
                    f"<p style='color:#1E3A8A;'>• Moved {file_count} items back</p>"
                    f"<p style='color:#1E3A8A;'>• Removed {deleted_count} empty folders</p>"
                )
                ThemeHelper.style_message_box(msg)
                msg.exec_()
                self.undo_btn.setEnabled(False)
                self.statusBar().showMessage(f"✅ Undo complete: {file_count} items restored")
            else:
                progress.close()
                msg = QMessageBox(self)
                msg.setWindowTitle("⚠️ Warning")
                ThemeHelper.style_message_box(msg, 'warning')
                msg.setText("Undo partially completed.")
                ThemeHelper.style_message_box(msg)
                msg.exec_()
                
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
    
    def _open_ai_group_editor(self):
        """Open AI Group Editor dialog."""
        if not self.current_folder:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No Folder Selected")
            msg.setText("Please organize a folder first to edit AI groups.")
            ThemeHelper.style_message_box(msg)
            msg.exec_()
            return
        
        try:
            # Get AI groups from organizer's semantic_groups (created during preview/organization)
            ai_groups = getattr(self.organizer, 'semantic_groups', {})
            if not ai_groups:
                # Styled information dialog
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("🤖 No AI Groups")
                msg.setText(
                    "<div style='background-color:#F0F9FF; padding:20px;'>" 
                    "<h3 style='color:#1E40AF;'>🤖 No AI Groups Found</h3>"
                    "<p style='color:#1E3A8A;'>AI semantic groups are created when you organize a folder.</p>"
                    "<p style='color:#3B82F6;'><b>Please organize a folder first to create AI groups.</b></p>"
                    "</div>"
                )
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #F0F9FF;
                    }
                    QPushButton {
                        background-color: #3B82F6;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 6px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #2563EB;
                    }
                """)
                msg.exec_()
                return
            
            # Convert string paths to Path objects for AIGroupEditor
            ai_groups_paths = {}
            for group_name, file_paths in ai_groups.items():
                ai_groups_paths[group_name] = [Path(p) for p in file_paths]
            
            dialog = AIGroupEditor(ai_groups_paths, self)
            if dialog.exec_():
                updated_groups = dialog.get_updated_groups()
                # Convert back to strings and store in organizer
                self.organizer.semantic_groups = {}
                for group_name, file_paths in updated_groups.items():
                    self.organizer.semantic_groups[group_name] = [str(p) for p in file_paths]
                self.statusBar().showMessage("✅ AI groups updated successfully")
        except Exception as e:
            logger.error(f"Error opening AI Group Editor: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"<p style='color:#DC2626;'>Failed to open AI Group Editor:</p>"
                f"<p style='color:#1E3A8A;'>{str(e)}</p>"
            )
    
    def _open_search_dialog(self):
        """Open search dialog."""
        if not self.current_folder:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No Folder Selected")
            msg.setText("Please organize a folder first to enable search.")
            ThemeHelper.style_message_box(msg)
            msg.exec_()
            return
        
        try:
            dialog = SearchDialog(self.current_folder, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error opening search dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"<p style='color:#DC2626;'>Failed to open search:</p>"
                f"<p style='color:#1E3A8A;'>{str(e)}</p>"
            )
    
    def _open_scheduler_settings(self):
        """Open scheduler settings dialog."""
        logger.info("Schedule button clicked - opening settings dialog")
        try:
            # Pass config.config dict instead of ConfigManager object
            dialog = ScheduleSettingsDialog(self.config.config, self)
            if dialog.exec_():
                self.statusBar().showMessage("✅ Schedule settings saved")
                logger.info("Schedule settings saved successfully")
        except Exception as e:
            logger.error(f"Error opening scheduler settings: {e}", exc_info=True)
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"<p style='color:#DC2626;'>Failed to open scheduler settings:</p>"
                f"<p style='color:#1E3A8A;'>{str(e)}</p>")
            ThemeHelper.style_message_box(error_msg, 'error')
            error_msg.exec_()
    
    def _open_compression_dialog(self):
        """Open smart compression dialog."""
        if not self.current_folder:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No Folder Selected")
            msg.setText("Please select a folder first to enable compression.")
            ThemeHelper.style_message_box(msg)
            msg.exec_()
            return
        
        try:
            dialog = CompressionDialog(
                parent=self,
                config=self.config.config,
                target_folder=self.current_folder
            )
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error opening compression dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"<p style='color:#DC2626;'>Failed to open compression:</p>"
                f"<p style='color:#1E3A8A;'>{str(e)}</p>"
            )
    
    def _show_ai_learning_stats(self):
        """Show AI learning statistics."""
        try:
            from ..core.ai_learning import AILearningSystem
        except ImportError:
            from core.ai_learning import AILearningSystem
        
        try:
            learner = AILearningSystem(self.config.config)
            stats = learner.get_accuracy_estimate()
            suggestions = learner.get_learning_suggestions()
            common = learner.get_common_corrections(5)
            
            # Build message
            msg_text = f"""
            <h3 style='color:#1E3A8A;'>🧠 AI Learning Statistics</h3>
            
            <p style='color:#1E3A8A;'>
            <b>Accuracy:</b> {stats['accuracy_percent']}%<br>
            <b>Total Organized:</b> {stats['total_organized']} files<br>
            <b>Corrections Made:</b> {stats['total_corrections']}<br>
            <b>Status:</b> {stats['message']}
            </p>
            
            <h4 style='color:#3B82F6;'>💡 Suggestions:</h4>
            <ul style='color:#1E3A8A;'>
            """
            
            for suggestion in suggestions[:3]:
                msg_text += f"<li>{suggestion}</li>"
            
            msg_text += "</ul>"
            
            if common:
                msg_text += "<h4 style='color:#3B82F6;'>📊 Common Corrections:</h4><ul style='color:#1E3A8A;'>"
                for item in common[:3]:
                    msg_text += f"<li>{item['pattern']}: {item['count']}x</li>"
                msg_text += "</ul>"
            
            msg = QMessageBox(self)
            msg.setWindowTitle("AI Learning Stats")
            msg.setText(msg_text)
            msg.setIcon(QMessageBox.Information)
            ThemeHelper.style_message_box(msg)
            msg.exec_()
            
        except Exception as e:
            logger.error(f"Error showing AI stats: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"<p style='color:#DC2626;'>Failed to load AI stats:</p>"
                f"<p style='color:#1E3A8A;'>{str(e)}</p>"
            )
    
    def _show_context_menu(self, position):
        """Show context menu when right-clicking on preview table."""
        # Check if a row is selected
        row = self.preview_table.rowAt(position.y())
        if row < 0 or not self.current_preview:
            return
        
        # Get file info from current preview
        if row >= len(self.current_preview):
            return
        
        file_info = self.current_preview[row]
        # Use 'source' key (Path object) from operation dict
        file_path = file_info.get('source')
        
        if not file_path or not isinstance(file_path, Path):
            logger.warning(f"Invalid file_info in context menu: {file_info}")
            return
        
        # Create context menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #EFF6FF;
                color: #1E3A8A;
                border: 2px solid #3B82F6;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #DBEAFE;
                color: #1E3A8A;
            }
        """)
        
        # Add actions
        open_action = menu.addAction("📂 Open File")
        open_folder_action = menu.addAction("📁 Open Containing Folder")
        menu.addSeparator()
        copy_path_action = menu.addAction("📋 Copy Full Path")
        copy_name_action = menu.addAction("📝 Copy File Name")
        
        # Execute menu and handle action
        action = menu.exec(self.preview_table.viewport().mapToGlobal(position))
        
        if action == open_action:
            # Open file with default application
            try:
                import subprocess
                if os.name == 'nt':  # Windows
                    os.startfile(str(file_path))
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', str(file_path)])
                logger.info(f"Opened file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to open file: {e}")
                QMessageBox.warning(self, "Error", f"Could not open file:\n{str(e)}")
        
        elif action == open_folder_action:
            # Open folder containing the file
            try:
                import subprocess
                folder = file_path.parent
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', str(file_path)])
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', '-R', str(file_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(folder)])
                logger.info(f"Opened folder: {folder}")
            except Exception as e:
                logger.error(f"Failed to open folder: {e}")
                QMessageBox.warning(self, "Error", f"Could not open folder:\n{str(e)}")
        
        elif action == copy_path_action:
            # Copy full path to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(str(file_path))
            self.statusBar().showMessage(f"📋 Copied: {file_path}", 3000)
            logger.info(f"Copied path to clipboard: {file_path}")
        
        elif action == copy_name_action:
            # Copy file name to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path.name)
            self.statusBar().showMessage(f"📋 Copied: {file_path.name}", 3000)
            logger.info(f"Copied name to clipboard: {file_path.name}")

    def closeEvent(self, event):
        """Handle window close."""
        logger.info("Application closing")
        event.accept()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event - accept folders dropped on window."""
        if event.mimeData().hasUrls():
            # Check if any URL is a directory
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.is_dir():
                    event.acceptProposedAction()
                    logger.info(f"Drag enter: Folder detected - {path}")
                    return
        event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event - analyze dropped folder."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.is_dir():
                    logger.info(f"Folder dropped: {path}")
                    # Set the folder and trigger normal browse+analyze flow
                    self.current_folder = path
                    self.folder_label.setText(f"📁 {path}")
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
                    
                    # Use the same analysis flow as Browse button (via QTimer for UI responsiveness)
                    QTimer.singleShot(50, self._analyze_folder)
                    
                    event.acceptProposedAction()
                    return
        event.ignore()
