"""
Schedule Settings Dialog
Configure automation and folder watching.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QComboBox, QTimeEdit, QListWidget,
    QPushButton, QLabel, QSpinBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QTime, Signal
from pathlib import Path
from typing import Dict
import logging


logger = logging.getLogger(__name__)


class ScheduleSettingsDialog(QDialog):
    """Dialog for configuring scheduling and automation."""
    
    settings_changed = Signal(dict)
    
    def __init__(self, config: Dict, parent=None):
        """
        Initialize dialog.
        
        Args:
            config: Current automation configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config.copy()
        self.automation_config = self.config.get('automation', {})
        
        self.setWindowTitle("Schedule & Automation Settings")
        self.setMinimumSize(600, 500)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Enable automation checkbox
        self.enable_checkbox = QCheckBox("Enable Automation")
        self.enable_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        layout.addWidget(self.enable_checkbox)
        
        # Scheduled organization group
        schedule_group = self._create_schedule_group()
        layout.addWidget(schedule_group)
        
        # Folder watch group
        watch_group = self._create_watch_group()
        layout.addWidget(watch_group)
        
        # Notifications group
        notif_group = self._create_notifications_group()
        layout.addWidget(notif_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.save_button.clicked.connect(self._save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E5E7EB;
                color: #374151;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D1D5DB;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def _create_schedule_group(self) -> QGroupBox:
        """Create scheduled organization settings group."""
        group = QGroupBox("Scheduled Organization")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Frequency
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency:"))
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Monthly"])
        freq_layout.addWidget(self.frequency_combo)
        freq_layout.addStretch()
        
        layout.addLayout(freq_layout)
        
        # Time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time:"))
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        
        layout.addLayout(time_layout)
        
        # Days (for daily frequency)
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Days:"))
        
        self.days_checkboxes = {}
        days = [("Mon", 1), ("Tue", 2), ("Wed", 3), ("Thu", 4), ("Fri", 5), ("Sat", 6), ("Sun", 7)]
        for day_name, day_num in days:
            cb = QCheckBox(day_name)
            self.days_checkboxes[day_num] = cb
            days_layout.addWidget(cb)
        
        days_layout.addStretch()
        layout.addLayout(days_layout)
        
        # Folders to organize
        layout.addWidget(QLabel("Folders to Organize:"))
        
        self.schedule_folders_list = QListWidget()
        self.schedule_folders_list.setMaximumHeight(100)
        layout.addWidget(self.schedule_folders_list)
        
        # Folder buttons
        folder_btn_layout = QHBoxLayout()
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(lambda: self._add_folder(self.schedule_folders_list))
        folder_btn_layout.addWidget(add_folder_btn)
        
        remove_folder_btn = QPushButton("Remove")
        remove_folder_btn.clicked.connect(lambda: self._remove_folder(self.schedule_folders_list))
        folder_btn_layout.addWidget(remove_folder_btn)
        
        folder_btn_layout.addStretch()
        layout.addLayout(folder_btn_layout)
        
        return group
    
    def _create_watch_group(self) -> QGroupBox:
        """Create folder watch settings group."""
        group = QGroupBox("Folder Watching")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Enable folder watch
        self.watch_enabled = QCheckBox("Watch folders for new files")
        layout.addWidget(self.watch_enabled)
        
        # Debounce time
        debounce_layout = QHBoxLayout()
        debounce_layout.addWidget(QLabel("Wait time after last file:"))
        
        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(5, 300)
        self.debounce_spin.setValue(30)
        self.debounce_spin.setSuffix(" seconds")
        debounce_layout.addWidget(self.debounce_spin)
        debounce_layout.addStretch()
        
        layout.addLayout(debounce_layout)
        
        # Folders to watch
        layout.addWidget(QLabel("Folders to Watch:"))
        
        self.watch_folders_list = QListWidget()
        self.watch_folders_list.setMaximumHeight(100)
        layout.addWidget(self.watch_folders_list)
        
        # Folder buttons
        folder_btn_layout = QHBoxLayout()
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(lambda: self._add_folder(self.watch_folders_list))
        folder_btn_layout.addWidget(add_folder_btn)
        
        remove_folder_btn = QPushButton("Remove")
        remove_folder_btn.clicked.connect(lambda: self._remove_folder(self.watch_folders_list))
        folder_btn_layout.addWidget(remove_folder_btn)
        
        folder_btn_layout.addStretch()
        layout.addLayout(folder_btn_layout)
        
        return group
    
    def _create_notifications_group(self) -> QGroupBox:
        """Create notifications settings group."""
        group = QGroupBox("Notifications")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        self.notif_enabled = QCheckBox("Enable notifications")
        layout.addWidget(self.notif_enabled)
        
        self.notif_completion = QCheckBox("Show completion notifications")
        layout.addWidget(self.notif_completion)
        
        self.notif_errors = QCheckBox("Show error notifications")
        layout.addWidget(self.notif_errors)
        
        return group
    
    def _on_enable_changed(self, state):
        """Handle enable checkbox change."""
        enabled = state == Qt.CheckState.Checked
        
        # Enable/disable all child widgets
        for group in self.findChildren(QGroupBox):
            for widget in group.findChildren((QComboBox, QTimeEdit, QCheckBox, QSpinBox, QListWidget, QPushButton)):
                widget.setEnabled(enabled)
    
    def _add_folder(self, list_widget: QListWidget):
        """Add folder to list."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Watch/Organize",
            str(Path.home() / "Downloads")
        )
        
        if folder:
            # Check if already in list
            existing = [list_widget.item(i).text() for i in range(list_widget.count())]
            if folder not in existing:
                list_widget.addItem(folder)
            else:
                QMessageBox.information(self, "Already Added", "This folder is already in the list.")
    
    def _remove_folder(self, list_widget: QListWidget):
        """Remove selected folder from list."""
        current = list_widget.currentRow()
        if current >= 0:
            list_widget.takeItem(current)
    
    def _load_settings(self):
        """Load current settings into UI."""
        # Enable checkbox
        self.enable_checkbox.setChecked(self.automation_config.get('enabled', False))
        
        # Schedule settings
        schedule_config = self.automation_config.get('schedule', {})
        
        frequency = schedule_config.get('frequency', 'daily')
        freq_map = {'daily': 0, 'weekly': 1, 'monthly': 2}
        self.frequency_combo.setCurrentIndex(freq_map.get(frequency, 0))
        
        time_str = schedule_config.get('time', '02:00')
        hour, minute = map(int, time_str.split(':'))
        self.time_edit.setTime(QTime(hour, minute))
        
        days = schedule_config.get('days', [1, 2, 3, 4, 5])
        for day_num, cb in self.days_checkboxes.items():
            cb.setChecked(day_num in days)
        
        schedule_folders = self.automation_config.get('folders', [])
        for folder in schedule_folders:
            self.schedule_folders_list.addItem(folder)
        
        # Watch settings
        watch_config = self.automation_config.get('folder_watch', {})
        
        self.watch_enabled.setChecked(watch_config.get('enabled', False))
        self.debounce_spin.setValue(watch_config.get('debounce_seconds', 30))
        
        watch_folders = watch_config.get('folders', [])
        for folder in watch_folders:
            self.watch_folders_list.addItem(folder)
        
        # Notification settings
        notif_config = self.automation_config.get('notifications', {})
        
        self.notif_enabled.setChecked(notif_config.get('enabled', True))
        self.notif_completion.setChecked(notif_config.get('show_completion', True))
        self.notif_errors.setChecked(notif_config.get('show_errors', True))
        
        # Trigger enable/disable
        self._on_enable_changed(self.enable_checkbox.checkState())
    
    def _save_settings(self):
        """Save settings and emit signal."""
        # Build automation config
        freq_map = {0: 'daily', 1: 'weekly', 2: 'monthly'}
        
        selected_days = [
            day_num for day_num, cb in self.days_checkboxes.items()
            if cb.isChecked()
        ]
        
        schedule_folders = [
            self.schedule_folders_list.item(i).text()
            for i in range(self.schedule_folders_list.count())
        ]
        
        watch_folders = [
            self.watch_folders_list.item(i).text()
            for i in range(self.watch_folders_list.count())
        ]
        
        automation_config = {
            'enabled': self.enable_checkbox.isChecked(),
            'schedule': {
                'frequency': freq_map[self.frequency_combo.currentIndex()],
                'time': self.time_edit.time().toString("HH:mm"),
                'days': selected_days
            },
            'folders': schedule_folders,
            'folder_watch': {
                'enabled': self.watch_enabled.isChecked(),
                'debounce_seconds': self.debounce_spin.value(),
                'folders': watch_folders
            },
            'notifications': {
                'enabled': self.notif_enabled.isChecked(),
                'show_completion': self.notif_completion.isChecked(),
                'show_errors': self.notif_errors.isChecked()
            }
        }
        
        # Validate
        if automation_config['enabled']:
            if not schedule_folders and not watch_folders:
                QMessageBox.warning(
                    self,
                    "No Folders Selected",
                    "Please add at least one folder to organize or watch."
                )
                return
            
            if automation_config['schedule']['frequency'] == 'daily' and not selected_days:
                QMessageBox.warning(
                    self,
                    "No Days Selected",
                    "Please select at least one day for daily scheduling."
                )
                return
        
        logger.info("Automation settings saved")
        self.settings_changed.emit(automation_config)
        self.accept()
