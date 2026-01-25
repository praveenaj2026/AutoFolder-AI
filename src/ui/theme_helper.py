"""
Theme Helper - Centralized blue theme styling for all dialogs

**THEME RULE - CRITICAL:**
NEVER use default QMessageBox (white background).
ALWAYS use ThemeHelper.style_message_box() with blue theme (#EFF6FF).
ALL dialogs, progress bars, and message boxes MUST use blue theme.
NO white/black/grey dialogs allowed anywhere in the application.
"""

import logging

try:
    from ..utils.icon_manager import IconManager
except ImportError:
    from utils.icon_manager import IconManager

logger = logging.getLogger(__name__)


class ThemeHelper:
    """Helper class for consistent blue theme across all dialogs."""
    
    BLUE_DIALOG_STYLE = """
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
    """
    
    PROGRESS_DIALOG_STYLE = """
        QProgressDialog {
            background-color: #EFF6FF;
            min-width: 400px;
        }
        QWidget {
            background-color: #EFF6FF;
        }
        QLabel {
            color: #1E3A8A;
            font-size: 13px;
            padding: 10px;
            background-color: #EFF6FF;
        }
        QProgressBar {
            background-color: #DBEAFE;
            border: 2px solid #3B82F6;
            border-radius: 5px;
            text-align: center;
            color: #1E3A8A;
        }
        QProgressBar::chunk {
            background-color: #3B82F6;
        }
        QPushButton {
            background-color: #EF4444;
            color: #F0F9FF;
            padding: 6px 16px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
            border: none;
        }
        QPushButton:hover {
            background-color: #DC2626;
        }
    """
    
    @staticmethod
    def style_message_box(msg_box, icon_type=None):
        """
        Apply blue theme to a QMessageBox.
        
        Args:
            msg_box: QMessageBox instance
            icon_type: Optional custom icon type ('info', 'warning', 'error', 'question', 'success')
        """
        msg_box.setStyleSheet(ThemeHelper.BLUE_DIALOG_STYLE)
        
        # Set custom icon if specified
        if icon_type:
            IconManager.set_message_box_icon(msg_box, icon_type)
    
    @staticmethod
    def style_progress_dialog(progress):
        """Apply blue theme to a QProgressDialog."""
        progress.setStyleSheet(ThemeHelper.PROGRESS_DIALOG_STYLE)
