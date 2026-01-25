"""
AI Group Editor Dialog
Allows users to rename, merge, split, and customize AI groups.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QGroupBox, QMessageBox, QListWidget, QListWidgetItem,
    QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class AIGroupEditor(QDialog):
    """Dialog for managing AI groups before organization."""
    
    # Signal emitted when groups are modified
    groups_modified = Signal(dict)  # {group_name: [files]}
    
    def __init__(self, semantic_groups: Dict[str, List[Path]], parent=None):
        """
        Initialize AI group editor.
        
        Args:
            semantic_groups: Dict mapping group name to list of files
            parent: Parent widget
        """
        super().__init__(parent)
        self.semantic_groups = semantic_groups.copy()  # Work on a copy
        self.selected_group = None
        
        self.setWindowTitle("✏️ Edit AI Groups")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #F0F9FF;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3B82F6;
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
            QLabel {
                color: #1E3A8A;
                background-color: transparent;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 2px solid #DBEAFE;
                border-radius: 5px;
                background-color: white;
                color: #1E3A8A;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #3B82F6;
            }
            QTreeWidget, QListWidget {
                border: 2px solid #3B82F6;
                border-radius: 5px;
                background-color: #EFF6FF;
                color: #1E3A8A;
            }
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        
        self._setup_ui()
        self._populate_groups()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("✏️ Customize AI Groups")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 8px;
                background-color: #EFF6FF;
                border-radius: 8px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "💡 Select groups to rename, merge, or split. "
            "Drag files between groups to reorganize."
        )
        instructions.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 12px;
                padding: 5px;
                background-color: #F9FAFB;
                border-radius: 5px;
            }
        """)
                padding: 10px;
                color: #64748B;
                font-size: 13px;
            }
        """)
        layout.addWidget(instructions)
        
        # Main content - Splitter for groups and files
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Group list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        group_label = QLabel("📦 AI Groups")
        group_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(group_label)
        
        self.group_list = QListWidget()
        self.group_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 5px;
                background-color: white;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #DBEAFE;
                color: #1E3A8A;
            }
            QListWidget::item:hover {
                background-color: #F0F9FF;
            }
        """)
        self.group_list.itemClicked.connect(self._on_group_selected)
        left_layout.addWidget(self.group_list)
        
        splitter.addWidget(left_widget)
        
        # Right side - File list for selected group
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.file_label = QLabel("📄 Files in Group")
        self.file_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(self.file_label)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 5px;
                background-color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 1px;
            }
        """)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        right_layout.addWidget(self.file_list)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.rename_btn = QPushButton("✏️ Rename Group")
        self.rename_btn.clicked.connect(self._rename_group)
        self.rename_btn.setEnabled(False)
        
        self.merge_btn = QPushButton("🔀 Merge Groups")
        self.merge_btn.clicked.connect(self._merge_groups)
        
        self.split_btn = QPushButton("✂️ Split Group")
        self.split_btn.clicked.connect(self._split_group)
        self.split_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("❌ Delete Group")
        self.delete_btn.clicked.connect(self._delete_group)
        self.delete_btn.setEnabled(False)
        
        self.new_group_btn = QPushButton("➕ Create Group")
        self.new_group_btn.clicked.connect(self._create_new_group)
        
        button_layout.addWidget(self.rename_btn)
        button_layout.addWidget(self.merge_btn)
        button_layout.addWidget(self.split_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.new_group_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Style action buttons
        button_style = """
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                background-color: #3B82F6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """
        for btn in [self.rename_btn, self.merge_btn, self.split_btn, 
                    self.delete_btn, self.new_group_btn]:
            btn.setStyleSheet(button_style)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 14px;
                background-color: #E5E7EB;
                color: #374151;
                border: none;
            }
            QPushButton:hover {
                background-color: #D1D5DB;
            }
        """)
        
        apply_btn = QPushButton("✅ Apply Changes")
        apply_btn.clicked.connect(self._apply_changes)
        apply_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                background-color: #10B981;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(cancel_btn)
        bottom_layout.addWidget(apply_btn)
        
        layout.addLayout(bottom_layout)
    
    def _populate_groups(self):
        """Populate the group list."""
        self.group_list.clear()
        
        for group_name, files in self.semantic_groups.items():
            item = QListWidgetItem(f"📦 {group_name} ({len(files)} files)")
            item.setData(Qt.UserRole, group_name)
            self.group_list.addItem(item)
    
    def _on_group_selected(self, item: QListWidgetItem):
        """Handle group selection."""
        self.selected_group = item.data(Qt.UserRole)
        
        # Enable/disable buttons
        self.rename_btn.setEnabled(True)
        self.split_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # Update file list
        self.file_label.setText(f"📄 Files in '{self.selected_group}' ({len(self.semantic_groups[self.selected_group])} files)")
        self.file_list.clear()
        
        for file_path in self.semantic_groups[self.selected_group]:
            file_item = QListWidgetItem(file_path.name)
            file_item.setData(Qt.UserRole, file_path)
            self.file_list.addItem(file_item)
    
    def _rename_group(self):
        """Rename the selected group."""
        if not self.selected_group:
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Group",
            f"Enter new name for '{self.selected_group}':",
            text=self.selected_group
        )
        
        if ok and new_name and new_name != self.selected_group:
            if new_name in self.semantic_groups:
                QMessageBox.warning(
                    self,
                    "Name Exists",
                    f"Group '{new_name}' already exists. Please choose a different name."
                )
                return
            
            # Rename group
            self.semantic_groups[new_name] = self.semantic_groups.pop(self.selected_group)
            self.selected_group = new_name
            
            self._populate_groups()
            logger.info(f"Renamed group to: {new_name}")
    
    def _merge_groups(self):
        """Merge selected groups."""
        selected_items = self.group_list.selectedItems()
        
        if len(selected_items) < 2:
            QMessageBox.information(
                self,
                "Select Groups",
                "Please select 2 or more groups to merge (Ctrl+Click to select multiple)."
            )
            return
        
        group_names = [item.data(Qt.UserRole) for item in selected_items]
        
        # Ask for merged group name
        new_name, ok = QInputDialog.getText(
            self,
            "Merge Groups",
            f"Enter name for merged group (merging {len(group_names)} groups):",
            text=group_names[0]
        )
        
        if ok and new_name:
            # Merge all files
            merged_files = []
            for group_name in group_names:
                merged_files.extend(self.semantic_groups[group_name])
                del self.semantic_groups[group_name]
            
            self.semantic_groups[new_name] = merged_files
            
            self._populate_groups()
            logger.info(f"Merged {len(group_names)} groups into: {new_name}")
    
    def _split_group(self):
        """Split selected files into a new group."""
        if not self.selected_group:
            return
        
        selected_files = [
            item.data(Qt.UserRole) 
            for item in self.file_list.selectedItems()
        ]
        
        if not selected_files:
            QMessageBox.information(
                self,
                "Select Files",
                "Please select files to move to a new group."
            )
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Split Group",
            f"Enter name for new group ({len(selected_files)} files):",
        )
        
        if ok and new_name:
            if new_name in self.semantic_groups:
                QMessageBox.warning(
                    self,
                    "Name Exists",
                    f"Group '{new_name}' already exists."
                )
                return
            
            # Create new group with selected files
            self.semantic_groups[new_name] = selected_files
            
            # Remove files from current group
            self.semantic_groups[self.selected_group] = [
                f for f in self.semantic_groups[self.selected_group]
                if f not in selected_files
            ]
            
            self._populate_groups()
            logger.info(f"Split {len(selected_files)} files into new group: {new_name}")
    
    def _delete_group(self):
        """Delete the selected group."""
        if not self.selected_group:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Group",
            f"Delete group '{self.selected_group}'?\n\n"
            f"{len(self.semantic_groups[self.selected_group])} files will be ungrouped "
            f"and organized without AI grouping.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.semantic_groups[self.selected_group]
            self.selected_group = None
            
            self.rename_btn.setEnabled(False)
            self.split_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            
            self._populate_groups()
            self.file_list.clear()
            self.file_label.setText("📄 Files in Group")
            
            logger.info(f"Deleted group: {self.selected_group}")
    
    def _create_new_group(self):
        """Create a new empty group."""
        new_name, ok = QInputDialog.getText(
            self,
            "Create Group",
            "Enter name for new group:"
        )
        
        if ok and new_name:
            if new_name in self.semantic_groups:
                QMessageBox.warning(
                    self,
                    "Name Exists",
                    f"Group '{new_name}' already exists."
                )
                return
            
            self.semantic_groups[new_name] = []
            self._populate_groups()
            logger.info(f"Created new group: {new_name}")
    
    def _apply_changes(self):
        """Apply changes and close dialog."""
        # Emit signal with modified groups
        self.groups_modified.emit(self.semantic_groups)
        self.accept()
        logger.info(f"Applied AI group changes: {len(self.semantic_groups)} groups")
