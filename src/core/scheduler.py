"""
Scheduler and Automation Module
Handles scheduled organization and folder watching.
"""

from pathlib import Path
from typing import List, Callable, Dict
import logging
from datetime import datetime, time
import threading

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("APScheduler not installed. Scheduling features disabled.")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Watchdog not installed. Folder watching features disabled.")


logger = logging.getLogger(__name__)


class FolderWatchHandler(FileSystemEventHandler):
    """Handler for folder file system events."""
    
    def __init__(self, callback: Callable, debounce_seconds: int = 30):
        """
        Initialize folder watch handler.
        
        Args:
            callback: Function to call when files are added
            debounce_seconds: Wait time after last file before triggering
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.timer = None
        self.lock = threading.Lock()
    
    def on_created(self, event):
        """Handle file creation event."""
        if not event.is_directory:
            logger.debug(f"File created: {event.src_path}")
            self._schedule_callback()
    
    def on_modified(self, event):
        """Handle file modification event."""
        if not event.is_directory:
            logger.debug(f"File modified: {event.src_path}")
            self._schedule_callback()
    
    def _schedule_callback(self):
        """Schedule callback with debouncing."""
        with self.lock:
            # Cancel existing timer
            if self.timer:
                self.timer.cancel()
            
            # Schedule new timer
            self.timer = threading.Timer(self.debounce_seconds, self._trigger_callback)
            self.timer.start()
            logger.debug(f"Scheduled callback in {self.debounce_seconds}s")
    
    def _trigger_callback(self):
        """Trigger the callback function."""
        try:
            logger.info("Triggering auto-organization callback")
            self.callback()
        except Exception as e:
            logger.error(f"Error in auto-organization callback: {e}")


class AutoOrganizer:
    """Handles automatic organization through scheduling and folder watching."""
    
    def __init__(self, config: Dict):
        """
        Initialize auto-organizer.
        
        Args:
            config: Configuration dictionary with automation settings
        """
        self.config = config
        self.automation_config = config.get('automation', {})
        
        self.scheduler = None
        self.observers: Dict[str, Observer] = {}
        self.organize_callback = None
        
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
        else:
            logger.warning("Scheduler not available - install apscheduler")
        
        if not WATCHDOG_AVAILABLE:
            logger.warning("Folder watching not available - install watchdog")
    
    def set_organize_callback(self, callback: Callable):
        """
        Set the callback function for organization.
        
        Args:
            callback: Function to call for organization (should accept folder path)
        """
        self.organize_callback = callback
        logger.info("Organization callback set")
    
    def start_scheduler(self):
        """Start scheduled organization."""
        if not SCHEDULER_AVAILABLE or not self.scheduler:
            logger.error("Scheduler not available")
            return False
        
        if not self.automation_config.get('enabled', False):
            logger.info("Automation not enabled in config")
            return False
        
        schedule_config = self.automation_config.get('schedule', {})
        frequency = schedule_config.get('frequency', 'daily')
        schedule_time = schedule_config.get('time', '02:00')
        days = schedule_config.get('days', [1, 2, 3, 4, 5])  # Monday-Friday
        
        # Parse time
        try:
            hour, minute = map(int, schedule_time.split(':'))
        except:
            hour, minute = 2, 0
        
        # Create trigger based on frequency
        if frequency == 'daily':
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                day_of_week=','.join(map(str, days))
            )
        elif frequency == 'weekly':
            # Run once a week on first day in days list
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                day_of_week=days[0] if days else 1
            )
        elif frequency == 'monthly':
            # Run on 1st of month
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                day=1
            )
        else:
            logger.error(f"Unknown frequency: {frequency}")
            return False
        
        # Add job for each folder
        folders = self.automation_config.get('folders', [])
        for folder_path in folders:
            job_id = f"organize_{Path(folder_path).name}"
            self.scheduler.add_job(
                self._scheduled_organize,
                trigger,
                args=[Path(folder_path)],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Scheduled job: {job_id} at {schedule_time} ({frequency})")
        
        self.scheduler.start()
        logger.info("Scheduler started")
        return True
    
    def stop_scheduler(self):
        """Stop scheduled organization."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def start_folder_watch(self, folders: List[Path] = None):
        """
        Start watching folders for new files.
        
        Args:
            folders: List of folders to watch. If None, uses config.
        """
        if not WATCHDOG_AVAILABLE:
            logger.error("Watchdog not available")
            return False
        
        if not self.automation_config.get('folder_watch', {}).get('enabled', False):
            logger.info("Folder watching not enabled in config")
            return False
        
        if folders is None:
            folders = [
                Path(p) for p in 
                self.automation_config.get('folder_watch', {}).get('folders', [])
            ]
        
        debounce = self.automation_config.get('folder_watch', {}).get('debounce_seconds', 30)
        
        for folder in folders:
            if not folder.exists():
                logger.warning(f"Folder does not exist: {folder}")
                continue
            
            # Create handler and observer
            handler = FolderWatchHandler(
                lambda f=folder: self._watched_organize(f),
                debounce_seconds=debounce
            )
            
            observer = Observer()
            observer.schedule(handler, str(folder), recursive=False)
            observer.start()
            
            self.observers[str(folder)] = observer
            logger.info(f"Started watching folder: {folder}")
        
        return True
    
    def stop_folder_watch(self):
        """Stop watching all folders."""
        for folder_path, observer in self.observers.items():
            observer.stop()
            observer.join()
            logger.info(f"Stopped watching folder: {folder_path}")
        
        self.observers.clear()
    
    def _scheduled_organize(self, folder: Path):
        """
        Callback for scheduled organization.
        
        Args:
            folder: Folder to organize
        """
        logger.info(f"Scheduled organization triggered for: {folder}")
        
        if self.organize_callback:
            try:
                self.organize_callback(folder)
                
                # Send notification if enabled
                if self.automation_config.get('notifications', {}).get('show_completion', True):
                    self._send_notification(
                        "AutoFolder AI",
                        f"Scheduled organization completed for {folder.name}"
                    )
            except Exception as e:
                logger.error(f"Error in scheduled organization: {e}")
                if self.automation_config.get('notifications', {}).get('enabled', True):
                    self._send_notification(
                        "AutoFolder AI Error",
                        f"Organization failed for {folder.name}: {str(e)}"
                    )
        else:
            logger.error("No organize callback set")
    
    def _watched_organize(self, folder: Path):
        """
        Callback for folder watch organization.
        
        Args:
            folder: Folder to organize
        """
        logger.info(f"Folder watch triggered organization for: {folder}")
        
        if self.organize_callback:
            try:
                self.organize_callback(folder)
                
                # Send notification
                if self.automation_config.get('notifications', {}).get('show_completion', True):
                    self._send_notification(
                        "AutoFolder AI",
                        f"Auto-organized new files in {folder.name}"
                    )
            except Exception as e:
                logger.error(f"Error in watched organization: {e}")
        else:
            logger.error("No organize callback set")
    
    def _send_notification(self, title: str, message: str):
        """
        Send Windows notification.
        
        Args:
            title: Notification title
            message: Notification message
        """
        try:
            # Try to use Windows 10+ toast notifications
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=5,
                threaded=True
            )
        except ImportError:
            logger.warning("win10toast not installed - notifications disabled")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_status(self) -> Dict:
        """
        Get current automation status.
        
        Returns:
            Status dictionary
        """
        return {
            'scheduler_running': self.scheduler.running if self.scheduler else False,
            'scheduled_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0,
            'watched_folders': len(self.observers),
            'scheduler_available': SCHEDULER_AVAILABLE,
            'watchdog_available': WATCHDOG_AVAILABLE
        }
    
    def shutdown(self):
        """Shutdown all automation services."""
        self.stop_scheduler()
        self.stop_folder_watch()
        logger.info("Auto-organizer shutdown complete")
