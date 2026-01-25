"""
Search Dialog for Organized Files
Provides UI for searching and filtering organized files.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QDateEdit, QDoubleSpinBox,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from pathlib import Path
from datetime import datetime
import subprocess
import logging

try:
    from ..core.search_engine import SearchEngine
except ImportError:
    from core.search_engine import SearchEngine

logger = logging.getLogger(__name__)


class SearchDialog(QDialog):
    """Dialog for searching organized files."""
    
    def __init__(self, organized_root: Path, parent=None):
        """
        Initialize search dialog.
        
        Args:
            organized_root: Root directory of organized files
            parent: Parent widget
        """
        super().__init__(parent)
        self.search_engine = SearchEngine(organized_root)
        self.results = []
        
        self.setWindowTitle("🔍 Search Organized Files")
        self.setMinimumSize(1200, 800)        self.setStyleSheet("""
            QDialog {
                background-color: #F0F9FF;
            }
        """)        
        self._setup_ui()
        self._populate_filters()
        
        # Build index on startup
        self.search_engine.build_index()
        self._update_stats()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🔍 Search Your Organized Files")
        header.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 15px;
                background-color: #EFF6FF;
                border-radius: 8px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type filename to search...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #93C5FD;
                border-radius: 8px;
                font-size: 14px;
                background-color: #EFF6FF;
                color: #1E3A8A;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background-color: #DBEAFE;
            }
        """)
        self.search_input.returnPressed.connect(self._perform_search)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._perform_search)
        search_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                background-color: #3B82F6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Filters
        filter_group = QGroupBox("🎯 Filters")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #93C5FD;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #EFF6FF;
                color: #1E3A8A;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1E40AF;
            }
        """)
        filter_layout = QVBoxLayout(filter_group)
        
        # Row 1: Category, AI Group, File Type, Extension
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row1.addWidget(self.category_combo)
        
        row1.addWidget(QLabel("AI Group:"))
        self.ai_group_combo = QComboBox()
        self.ai_group_combo.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row1.addWidget(self.ai_group_combo)
        
        row1.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row1.addWidget(self.type_combo)
        
        row1.addWidget(QLabel("Extension:"))
        self.ext_combo = QComboBox()
        self.ext_combo.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row1.addWidget(self.ext_combo)
        
        filter_layout.addLayout(row1)
        
        # Row 2: Date range
        row2 = QHBoxLayout()
        
        row2.addWidget(QLabel("Date From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_from.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row2.addWidget(self.date_from)
        
        row2.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row2.addWidget(self.date_to)
        
        # Size range
        row2.addWidget(QLabel("Size (MB):"))
        self.size_min = QDoubleSpinBox()
        self.size_min.setRange(0, 100000)
        self.size_min.setDecimals(2)
        self.size_min.setPrefix("Min: ")
        self.size_min.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row2.addWidget(self.size_min)
        
        self.size_max = QDoubleSpinBox()
        self.size_max.setRange(0, 100000)
        self.size_max.setValue(100000)
        self.size_max.setDecimals(2)
        self.size_max.setPrefix("Max: ")
        self.size_max.setStyleSheet("padding: 8px; font-size: 13px; background-color: #DBEAFE; color: #1E3A8A;")
        row2.addWidget(self.size_max)
        
        filter_layout.addLayout(row2)
        
        # Clear filters button
        clear_btn = QPushButton("🔄 Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
                background-color: #BFDBFE;
                color: #1E40AF;
                border: 2px solid #93C5FD;
            }
            QPushButton:hover {
                background-color: #93C5FD;
            }
        """)
        filter_layout.addWidget(clear_btn)
        
        layout.addWidget(filter_group)
        
        # Stats label
        self.stats_label = QLabel("📊 Index: 0 files")
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                color: #1E40AF;
                font-size: 13px;
                font-weight: bold;
                background-color: #DBEAFE;
                border-radius: 6px;
                border: 2px solid #93C5FD;
            }
        """)
        layout.addWidget(self.stats_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "📄 Filename", "📁 Category", "🤖 AI Group", 
            "📦 Type", "💾 Size", "📅 Modified"
        ])
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #93C5FD;
                border-radius: 8px;
                background-color: #F0F9FF;
                font-size: 13px;
                color: #1E3A8A;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1E3A8A;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E40AF;
            }
            QHeaderView::section {
                background-color: #3B82F6;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.doubleClicked.connect(self._open_file)
        
        layout.addWidget(self.results_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        open_btn = QPushButton("📂 Open File")
        open_btn.clicked.connect(self._open_file)
        
        explorer_btn = QPushButton("📁 Show in Explorer")
        explorer_btn.clicked.connect(self._show_in_explorer)
        
        copy_path_btn = QPushButton("📋 Copy Path")
        copy_path_btn.clicked.connect(self._copy_path)
        
        for btn in [open_btn, explorer_btn, copy_path_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            action_layout.addWidget(btn)
        
        action_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 25px;
                border-radius: 6px;
                font-size: 13px;
                background-color: #E5E7EB;
                color: #374151;
                border: none;
            }
            QPushButton:hover {
                background-color: #D1D5DB;
            }
        """)
        action_layout.addWidget(close_btn)
        
        layout.addLayout(action_layout)
    
    def _populate_filters(self):
        """Populate filter dropdowns."""
        # Will be populated after index is built
        pass
    
    def _update_stats(self):
        """Update statistics label."""
        stats = self.search_engine.get_stats()
        self.stats_label.setText(
            f"📊 Index: {stats['total_files']} files | "
            f"{stats['total_size_gb']:.2f} GB | "
            f"{stats['categories']} categories | "
            f"{stats['ai_groups']} AI groups"
        )
        
        # Populate filters
        self.category_combo.clear()
        self.category_combo.addItem("All")
        self.category_combo.addItems(self.search_engine.get_categories())
        
        self.ai_group_combo.clear()
        self.ai_group_combo.addItem("All")
        self.ai_group_combo.addItems(self.search_engine.get_ai_groups())
        
        self.type_combo.clear()
        self.type_combo.addItem("All")
        self.type_combo.addItems(self.search_engine.get_file_types())
        
        self.ext_combo.clear()
        self.ext_combo.addItem("All")
        self.ext_combo.addItems(self.search_engine.get_extensions())
    
    def _perform_search(self):
        """Perform search with current filters."""
        query = self.search_input.text()
        category = self.category_combo.currentText()
        ai_group = self.ai_group_combo.currentText()
        file_type = self.type_combo.currentText()
        extension = self.ext_combo.currentText()
        
        date_from = datetime(
            self.date_from.date().year(),
            self.date_from.date().month(),
            self.date_from.date().day()
        )
        date_to = datetime(
            self.date_to.date().year(),
            self.date_to.date().month(),
            self.date_to.date().day(),
            23, 59, 59
        )
        
        size_min = self.size_min.value() if self.size_min.value() > 0 else None
        size_max = self.size_max.value() if self.size_max.value() < 100000 else None
        
        # Perform search
        self.results = self.search_engine.search(
            query=query,
            category=category if category != "All" else None,
            ai_group=ai_group if ai_group != "All" else None,
            file_type=file_type if file_type != "All" else None,
            extension=extension if extension != "All" else None,
            date_from=date_from,
            date_to=date_to,
            size_min_mb=size_min,
            size_max_mb=size_max
        )
        
        self._display_results()
    
    def _display_results(self):
        """Display search results in table."""
        self.results_table.setRowCount(len(self.results))
        
        for row, result in enumerate(self.results):
            # Filename
            self.results_table.setItem(row, 0, QTableWidgetItem(result['name']))
            
            # Category
            self.results_table.setItem(row, 1, QTableWidgetItem(result['category']))
            
            # AI Group
            ai_group = result['ai_group'] or "N/A"
            self.results_table.setItem(row, 2, QTableWidgetItem(ai_group))
            
            # Type
            file_type = result['file_type'] or "N/A"
            self.results_table.setItem(row, 3, QTableWidgetItem(file_type))
            
            # Size
            size_str = f"{result['size_mb']:.2f} MB"
            self.results_table.setItem(row, 4, QTableWidgetItem(size_str))
            
            # Modified date
            date_str = result['modified'].strftime("%Y-%m-%d %H:%M")
            self.results_table.setItem(row, 5, QTableWidgetItem(date_str))
            
            # Store path in row data
            self.results_table.item(row, 0).setData(Qt.UserRole, result['path'])
        
        logger.info(f"Displayed {len(self.results)} search results")
    
    def _clear_filters(self):
        """Clear all filters."""
        self.search_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.ai_group_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.ext_combo.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_to.setDate(QDate.currentDate())
        self.size_min.setValue(0)
        self.size_max.setValue(100000)
    
    def _open_file(self):
        """Open selected file."""
        current_row = self.results_table.currentRow()
        if current_row < 0:
            return
        
        file_path = self.results_table.item(current_row, 0).data(Qt.UserRole)
        if file_path and file_path.exists():
            try:
                subprocess.Popen(['start', '', str(file_path)], shell=True)
                logger.info(f"Opened file: {file_path}")
            except Exception as e:
                logger.error(f"Error opening file: {e}")
                QMessageBox.warning(self, "Error", f"Could not open file:\n{e}")
    
    def _show_in_explorer(self):
        """Show selected file in Windows Explorer."""
        current_row = self.results_table.currentRow()
        if current_row < 0:
            return
        
        file_path = self.results_table.item(current_row, 0).data(Qt.UserRole)
        if file_path and file_path.exists():
            try:
                subprocess.Popen(['explorer', '/select,', str(file_path)])
                logger.info(f"Showed in Explorer: {file_path}")
            except Exception as e:
                logger.error(f"Error showing in Explorer: {e}")
    
    def _copy_path(self):
        """Copy file path to clipboard."""
        current_row = self.results_table.currentRow()
        if current_row < 0:
            return
        
        file_path = self.results_table.item(current_row, 0).data(Qt.UserRole)
        if file_path:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(str(file_path))
            logger.info(f"Copied path to clipboard: {file_path}")
