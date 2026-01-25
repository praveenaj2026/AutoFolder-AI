"""
Organization Statistics Dashboard
Shows comprehensive statistics about file organization.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QScrollArea, QWidget,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class StatsDialog(QDialog):
    """Dialog showing organization statistics and analysis."""
    
    def __init__(self, stats: Dict, parent=None):
        """
        Initialize stats dashboard.
        
        Args:
            stats: Statistics dictionary from organizer
            parent: Parent widget
        """
        super().__init__(parent)
        self.stats = stats
        
        self.setWindowTitle("📊 Organization Statistics Dashboard")
        self.setMinimumSize(900, 700)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📊 Organization Statistics")
        header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 20px;
                background-color: #EFF6FF;
                border-radius: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F9FAFB;
            }
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Summary cards
        summary_group = self._create_summary_cards()
        content_layout.addWidget(summary_group)
        
        # Category breakdown
        if 'by_category' in self.stats:
            category_group = self._create_category_breakdown()
            content_layout.addWidget(category_group)
        
        # Size analysis
        if 'by_size_range' in self.stats:
            size_group = self._create_size_breakdown()
            content_layout.addWidget(size_group)
        
        # File type analysis
        if 'by_extension' in self.stats:
            type_group = self._create_type_breakdown()
            content_layout.addWidget(type_group)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("✅ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
    
    def _create_summary_cards(self) -> QWidget:
        """Create summary statistics cards."""
        group = QGroupBox("📈 Summary")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #1E3A8A;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                padding: 15px;
                background-color: #F0F9FF;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        # Define cards - light colors only
        cards = [
            ("📁 Total Files", self.stats.get('total_files', 0), "#3B82F6"),
            ("📦 Total Size", self._format_size(self.stats.get('total_size', 0)), "#10B981"),
            ("🗂️ Categories", len(self.stats.get('by_category', {})), "#FCA5A5"),  # Light red
            ("📄 File Types", len(self.stats.get('by_extension', {})), "#FCD34D"),  # Light orange
            ("✅ Organized", self.stats.get('completed', 0), "#059669"),
        ]
        
        # Create cards in 3 columns
        for i, (title, value, color) in enumerate(cards):
            row = i // 3
            col = i % 3
            card = self._create_stat_card(title, value, color)
            layout.addWidget(card, row, col)
        
        return group
    
    def _create_stat_card(self, title: str, value, color: str) -> QFrame:
        """Create a single stat card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: #6B7280;
                font-weight: bold;
            }}
        """)
        layout.addWidget(title_label)
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {color};
            }}
        """)
        layout.addWidget(value_label)
        
        return card
    
    def _create_category_breakdown(self) -> QGroupBox:
        """Create category breakdown visualization."""
        group = QGroupBox("🏷️ Files by Category")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #1E3A8A;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                padding: 15px;
                background-color: #F0F9FF;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        categories = self.stats.get('by_category', {})
        total_files = self.stats.get('total_files', 1)
        
        # Sort by count
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories[:10]:  # Top 10
            bar = self._create_progress_bar(
                category, 
                count, 
                total_files,
                "#3B82F6"
            )
            layout.addWidget(bar)
        
        return group
    
    def _create_ai_group_breakdown(self) -> QGroupBox:
        """Create AI group breakdown."""
        group = QGroupBox("🤖 Files by AI Semantic Group")
        group.setToolTip(
            "AI Groups are intelligent clusters of similar files based on their content and meaning.\n"
            "For example: 'job applications', 'bills & invoices', 'vacation photos', etc.\n"
            "This helps you see patterns in your files that go beyond just file types."
        )
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #1E3A8A;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                padding: 15px;
                background-color: #F0F9FF;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        ai_groups = self.stats.get('ai_groups', {})
        total_files = self.stats.get('total_files', 1)
        
        if not ai_groups:
            no_data = QLabel("No AI groups created (files too different or too few)")
            no_data.setStyleSheet("color: #9CA3AF; font-style: italic; padding: 10px;")
            layout.addWidget(no_data)
            return group
        
        # Sort by count
        sorted_groups = sorted(ai_groups.items(), key=lambda x: x[1], reverse=True)
        
        for group_name, count in sorted_groups[:15]:  # Top 15
            bar = self._create_progress_bar(
                group_name, 
                count, 
                total_files,
                "#8B5CF6"
            )
            layout.addWidget(bar)
        
        if len(ai_groups) > 15:
            more_label = QLabel(f"... and {len(ai_groups) - 15} more groups")
            more_label.setStyleSheet("color: #6B7280; font-style: italic; padding: 5px;")
            layout.addWidget(more_label)
        
        return group
    
    def _create_size_breakdown(self) -> QGroupBox:
        """Create size range breakdown."""
        group = QGroupBox("💾 Files by Size Range")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #1E3A8A;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                padding: 15px;
                background-color: #F0F9FF;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        size_ranges = self.stats.get('by_size_range', {})
        total_files = self.stats.get('total_files', 1)
        
        # Define range labels
        range_labels = {
            'tiny': '📄 Tiny (< 1 MB)',
            'small': '📁 Small (1-10 MB)',
            'medium': '📦 Medium (10-100 MB)',
            'large': '🗃️ Large (100 MB - 1 GB)',
            'huge': '🏔️ Huge (> 1 GB)'
        }
        
        for key in ['huge', 'large', 'medium', 'small', 'tiny']:
            if key in size_ranges:
                count = size_ranges[key]
                label = range_labels.get(key, key)
                bar = self._create_progress_bar(
                    label, 
                    count, 
                    total_files,
                    "#10B981"
                )
                layout.addWidget(bar)
        
        return group
    
    def _create_type_breakdown(self) -> QGroupBox:
        """Create file type breakdown."""
        group = QGroupBox("📝 Top File Types")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #1E3A8A;
                border: 2px solid #93C5FD;
                border-radius: 10px;
                padding: 15px;
                background-color: #F0F9FF;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        extensions = self.stats.get('by_extension', {})
        total_files = self.stats.get('total_files', 1)
        
        # Sort by count
        sorted_types = sorted(extensions.items(), key=lambda x: x[1], reverse=True)
        
        for ext, count in sorted_types[:10]:  # Top 10
            display_ext = f".{ext}" if ext else "(no extension)"
            bar = self._create_progress_bar(
                display_ext, 
                count, 
                total_files,
                "#EC4899"
            )
            layout.addWidget(bar)
        
        if len(extensions) > 10:
            more_label = QLabel(f"... and {len(extensions) - 10} more file types")
            more_label.setStyleSheet("color: #6B7280; font-style: italic; padding: 5px;")
            layout.addWidget(more_label)
        
        return group
    
    def _create_progress_bar(
        self, 
        label: str, 
        value: int, 
        total: int,
        color: str
    ) -> QWidget:
        """Create a horizontal progress bar with label."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(200)
        label_widget.setStyleSheet("font-size: 14px; color: #1F2937; font-weight: 500;")
        layout.addWidget(label_widget)
        
        # Progress bar container
        bar_container = QFrame()
        bar_container.setStyleSheet("""
            QFrame {
                background-color: #E5E7EB;
                border-radius: 5px;
            }
        """)
        bar_container.setFixedHeight(24)
        
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        # Calculate percentage
        percentage = (value / total * 100) if total > 0 else 0
        
        # Filled bar
        filled_bar = QFrame()
        filled_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        filled_bar.setFixedWidth(int(400 * percentage / 100))
        bar_layout.addWidget(filled_bar)
        bar_layout.addStretch()
        
        layout.addWidget(bar_container)
        
        # Count and percentage
        count_label = QLabel(f"{value} ({percentage:.1f}%)")
        count_label.setMinimumWidth(100)
        count_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #000000;")
        layout.addWidget(count_label)
        
        return widget
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
