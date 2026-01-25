"""
Duplicate File Management Dialog
Shows duplicate files and provides management options.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QRadioButton, QButtonGroup, QMessageBox,
    QProgressDialog, QFileIconProvider
)
from PySide6.QtCore import Qt, Signal, QFileInfo
from PySide6.QtGui import QFont, QColor, QIcon
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DuplicateDialog(QDialog):
    """Dialog for managing duplicate files."""
    
    # Signal emitted when user confirms duplicate handling
    duplicates_processed = Signal(dict)  # {action: str, duplicates: dict}
    
    def __init__(self, duplicates: Dict[str, List[Path]], stats: Dict, parent=None):
        """
        Initialize duplicate management dialog.
        
        Args:
            duplicates: Dict mapping hash to list of duplicate files
            stats: Analysis statistics from DuplicateDetector
            parent: Parent widget
        """
        super().__init__(parent)
        self.duplicates = duplicates
        self.stats = stats
        self.selected_action = 'keep_newest'
        
        # File icon provider for thumbnails
        self.icon_provider = QFileIconProvider()
        
        self.setWindowTitle("🔍 Duplicate Files Found")
        self.setMinimumSize(1000, 700)  # Increased from 800x600 for better spacing
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with stats
        header = self._create_header()
        layout.addWidget(header)
        
        # Duplicate groups tree
        tree_label = QLabel("📦 Duplicate File Groups:")
        tree_label.setStyleSheet("font-size: 13px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(tree_label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File Name", "Location", "Size"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)  # Disable editing
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: 2px solid #3B82F6;
                border-radius: 5px;
                background-color: #EFF6FF;
                font-size: 12px;
                color: #1E3A8A;
            }
            QTreeWidget::item {
                padding: 5px;
                background-color: #EFF6FF;
                color: #1E3A8A;
            }
            QTreeWidget::item:alternate {
                background-color: #DBEAFE;
                color: #1E3A8A;
            }
            QTreeWidget::item:selected {
                background-color: #3B82F6;
                color: #F0F9FF;
            }
            QHeaderView::section {
                background-color: #3B82F6;
                color: #F0F9FF;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        self._populate_tree()
        layout.addWidget(self.tree)
        
        # Action selection
        action_group = self._create_action_group()
        layout.addWidget(action_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.process_btn = QPushButton("✅ Process Duplicates")
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #1E3A8A;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.process_btn.clicked.connect(self._process_duplicates)
        button_layout.addWidget(self.process_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #1E3A8A;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_header(self) -> QGroupBox:
        """Create header with statistics."""
        group = QGroupBox("📊 Duplicate Analysis Summary")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #8B5CF6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #EDE9FE;
            }
            QGroupBox::title {
                color: #5B21B6;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Stats grid
        stats_text = f"""
        <table style='width: 100%; font-size: 13px; color: #5B21B6;'>
            <tr>
                <td><b>📦 Duplicate Groups:</b></td>
                <td><b>{self.stats['duplicate_groups']}</b></td>
                <td><b>📄 Total Duplicate Files:</b></td>
                <td><b>{self.stats['total_duplicate_files']}</b></td>
            </tr>
            <tr>
                <td><b>💾 Wasted Space:</b></td>
                <td colspan='3'><b>{self.stats['wasted_space_mb']:.2f} MB</b></td>
            </tr>
        </table>
        """
        
        if self.stats['largest_duplicate_group']:
            lg = self.stats['largest_duplicate_group']
            stats_text += f"""
            <p style='margin-top: 10px; color: #5B21B6;'>
                <b>🔥 Largest Duplicate Group:</b> {lg['count']} copies of "{lg['sample_file']}" 
                ({lg['size_mb']:.2f} MB each)
            </p>
            """
        
        stats_label = QLabel(stats_text)
        stats_label.setTextFormat(Qt.RichText)
        layout.addWidget(stats_label)
        
        return group
    
    def _create_action_group(self) -> QGroupBox:
        """Create action selection radio buttons."""
        group = QGroupBox("⚙️ Duplicate Handling Options")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #3B82F6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #DBEAFE;
            }
            QGroupBox::title {
                color: #1E40AF;
                border: 2px solid #3B82F6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        self.action_group = QButtonGroup(self)
        
        # Radio button options
        options = [
            ('keep_newest', '🕐 Keep Newest', 'Keep most recently modified file, delete others'),
            ('keep_oldest', '📅 Keep Oldest', 'Keep oldest file, delete others'),
            ('keep_all', '💾 Keep All', 'Move duplicates to "Duplicates" folder (no deletion)'),
            ('skip', '⏭️ Skip All', 'Ignore duplicates and continue organizing')
        ]
        
        for action, label, tooltip in options:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 12px;
                    padding: 5px;
                    color: #1E3A8A;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
            """)
            if action == self.selected_action:
                radio.setChecked(True)
            
            self.action_group.addButton(radio)
            radio.toggled.connect(lambda checked, a=action: self._on_action_changed(checked, a))
            layout.addWidget(radio)
        
        return group
    
    def _populate_tree(self):
        """Populate tree with duplicate file groups."""
        self.tree.clear()
        
        for group_idx, (hash_val, files) in enumerate(self.duplicates.items(), 1):
            if not files:
                continue
            
            # Get file size
            file_size = files[0].stat().st_size if files[0].exists() else 0
            size_mb = file_size / (1024 * 1024)
            
            # Create parent item for group
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, f"Group {group_idx} ({len(files)} copies)")
            group_item.setText(1, "")  # Empty middle column
            group_item.setText(2, f"Wasting: {(len(files)-1) * size_mb:.2f} MB")
            group_item.setBackground(0, QColor("#60A5FA"))  # Bright blue background
            group_item.setBackground(1, QColor("#60A5FA"))  # Bright blue background
            group_item.setBackground(2, QColor("#60A5FA"))  # Bright blue background
            group_item.setForeground(0, QColor("#1E3A8A"))  # Dark blue text
            group_item.setForeground(1, QColor("#1E3A8A"))  # Dark blue text
            group_item.setForeground(2, QColor("#1E3A8A"))  # Dark blue text
            
            # Make group item non-editable
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsEditable)
            
            font = QFont()
            font.setBold(True)
            group_item.setFont(0, font)
            group_item.setFont(1, font)
            group_item.setFont(2, font)
            
            # Add child items for each file
            for file_path in files:
                file_item = QTreeWidgetItem(group_item)
                
                # Add system file icon
                try:
                    file_info = QFileInfo(str(file_path))
                    system_icon = self.icon_provider.icon(file_info)
                    if not system_icon.isNull():
                        file_item.setIcon(0, system_icon)
                except Exception as e:
                    logger.debug(f"Failed to load icon for {file_path.name}: {e}")
                
                file_item.setText(0, file_path.name)
                file_item.setText(1, str(file_path.parent))
                file_item.setText(2, f"{size_mb:.2f} MB")
                
                # Add tooltip with full path
                file_item.setToolTip(0, str(file_path))
                file_item.setToolTip(1, str(file_path))
            
            group_item.setExpanded(True)
        
        # Resize columns
        for i in range(3):
            self.tree.resizeColumnToContents(i)
    
    def _on_action_changed(self, checked: bool, action: str):
        """Handle action selection change."""
        if checked:
            self.selected_action = action
            logger.debug(f"Selected action: {action}")
    
    def _process_duplicates(self):
        """Process duplicates based on selected action."""
        if not self.duplicates:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No Duplicates")
            msg.setText("No duplicate files to process.")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #EFF6FF;
                }
                QLabel {
                    color: #1E3A8A;
                    background-color: #EFF6FF;
                }
                QPushButton {
                    background-color: #3B82F6;
                    color: #F0F9FF;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            msg.exec_()
            self.accept()
            return
        
        # Confirm action
        action_descriptions = {
            'keep_newest': 'keep the newest file and DELETE older copies',
            'keep_oldest': 'keep the oldest file and DELETE newer copies',
            'keep_all': 'move all duplicates to a "Duplicates" folder',
            'skip': 'skip duplicate handling and continue'
        }
        
        description = action_descriptions.get(self.selected_action, 'process duplicates')
        
        if self.selected_action in ['keep_newest', 'keep_oldest']:
            total_to_delete = sum(len(files) - 1 for files in self.duplicates.values())
            msg = (
                f"This will {description}.\n\n"
                f"⚠️ {total_to_delete} files will be PERMANENTLY DELETED.\n\n"
                f"Are you sure you want to continue?"
            )
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Confirm Deletion")
            msg_box.setText(msg)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #EFF6FF;
                }
                QLabel {
                    color: #1E3A8A;
                    background-color: #EFF6FF;
                }
                QPushButton {
                    background-color: #3B82F6;
                    color: #F0F9FF;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            reply = msg_box.exec_()
            
            if reply == QMessageBox.No:
                return
        
        # Emit signal with action and duplicates
        result = {
            'action': self.selected_action,
            'duplicates': self.duplicates,
            'stats': self.stats
        }
        
        self.duplicates_processed.emit(result)
        self.accept()
    
    def get_selected_action(self) -> str:
        """Get the selected action."""
        return self.selected_action
