#!/usr/bin/env python3
"""
Scheduling system for II Indexation Checker
Allows automated indexation checking at specified intervals
"""

import threading
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class IndexationScheduler:
    def __init__(self, config_path='config/scheduler.json'):
        self.config_path = config_path
        self.is_running = False
        self.stop_event = threading.Event()
        self.scheduler_thread = None
        self.callback = None
        self.config = self.load_config()

    def load_config(self):
        """Load scheduler configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as file:
                    return json.load(file)
            else:
                # Create default config
                default_config = {
                    "enabled": False,
                    "interval_type": "hours",  # "hours", "daily", "weekly", "biweekly", "monthly"
                    "interval_value": 24,
                    "run_time": "09:00",
                    "run_day": 1,  # Day of week (1=Monday) for weekly/biweekly, day of month (1-28) for monthly
                    "enabled_websites": [],
                    "last_run": None,
                    "upload_to_sheets": True,
                    "email_notifications": False,
                    "email_address": ""
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            print(f"Error loading scheduler config: {e}")
            return {}

    def save_config(self, config=None):
        """Save scheduler configuration"""
        try:
            if config is None:
                config = self.config

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=2)
            self.config = config
        except Exception as e:
            print(f"Error saving scheduler config: {e}")

    def set_callback(self, callback_func):
        """Set callback function for running checks"""
        self.callback = callback_func

    def start_scheduler(self):
        """Start the scheduler"""
        if self.is_running:
            return False

        if not self.config.get('enabled', False):
            return False

        self.is_running = True
        self.stop_event.clear()

        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        return True

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        self.stop_event.set()
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while not self.stop_event.is_set():
            try:
                if self._should_run_check():
                    self._run_scheduled_check()

                # Check every minute
                self.stop_event.wait(60)

            except Exception as e:
                print(f"Scheduler error: {e}")
                self.stop_event.wait(300)  # Wait 5 minutes on error

    def _should_run_check(self):
        """Check if we should run the indexation check"""
        if not self.config.get('enabled', False):
            return False

        interval_type = self.config.get('interval_type', 'hours')
        interval_value = self.config.get('interval_value', 24)
        run_time = self.config.get('run_time', '09:00')
        run_day = self.config.get('run_day', 1)
        last_run = self.config.get('last_run')

        now = datetime.now()

        # Parse run time
        try:
            run_hour, run_minute = map(int, run_time.split(':'))
        except:
            run_hour, run_minute = 9, 0

        # Check if we're at the right time of day
        current_time = now.time()
        target_time = datetime.now().replace(hour=run_hour, minute=run_minute, second=0, microsecond=0).time()

        # Allow 1-minute window
        time_match = abs((datetime.combine(datetime.today(), current_time) -
                         datetime.combine(datetime.today(), target_time)).seconds) < 60

        if not time_match:
            return False

        # Check scheduling conditions based on interval type
        if interval_type == 'hours':
            # Legacy hourly scheduling
            if last_run:
                try:
                    last_run_dt = datetime.fromisoformat(last_run)
                    time_since_last = now - last_run_dt

                    if time_since_last.total_seconds() < (interval_value * 3600 - 300):  # 5-minute buffer
                        return False
                except:
                    pass
            return True

        elif interval_type == 'daily':
            # Daily scheduling - run every day at specified time
            if last_run:
                try:
                    last_run_dt = datetime.fromisoformat(last_run)
                    # Don't run if we already ran today
                    if last_run_dt.date() == now.date():
                        return False
                except:
                    pass
            return True

        elif interval_type == 'weekly':
            # Weekly scheduling - run on specific day of week
            if now.weekday() + 1 != run_day:  # weekday() returns 0-6, we use 1-7
                return False

            if last_run:
                try:
                    last_run_dt = datetime.fromisoformat(last_run)
                    # Don't run if we already ran this week
                    days_since_last = (now.date() - last_run_dt.date()).days
                    if days_since_last < 6:  # Less than 6 days since last run
                        return False
                except:
                    pass
            return True

        elif interval_type == 'biweekly':
            # Bi-weekly scheduling - run every 2 weeks on specific day
            if now.weekday() + 1 != run_day:
                return False

            if last_run:
                try:
                    last_run_dt = datetime.fromisoformat(last_run)
                    # Don't run if we already ran in the last 13 days
                    days_since_last = (now.date() - last_run_dt.date()).days
                    if days_since_last < 13:  # Less than 13 days since last run
                        return False
                except:
                    pass
            return True

        elif interval_type == 'monthly':
            # Monthly scheduling - run on specific day of month
            if now.day != run_day:
                return False

            if last_run:
                try:
                    last_run_dt = datetime.fromisoformat(last_run)
                    # Don't run if we already ran this month
                    if (last_run_dt.year == now.year and
                        last_run_dt.month == now.month):
                        return False
                except:
                    pass
            return True

        return False

    def _run_scheduled_check(self):
        """Run the scheduled indexation check"""
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled indexation check...")

            if self.callback:
                # Run the callback (which should be the main app's check function)
                websites = self.config.get('enabled_websites', [])
                upload_sheets = self.config.get('upload_to_sheets', True)

                self.callback(websites, upload_sheets)

            # Update last run time
            self.config['last_run'] = datetime.now().isoformat()
            self.save_config()

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduled check completed")

        except Exception as e:
            print(f"Error in scheduled check: {e}")

    def get_next_run_time(self):
        """Get the next scheduled run time"""
        if not self.config.get('enabled', False):
            return None

        interval_type = self.config.get('interval_type', 'hours')
        interval_value = self.config.get('interval_value', 24)
        run_time = self.config.get('run_time', '09:00')
        run_day = self.config.get('run_day', 1)
        last_run = self.config.get('last_run')

        try:
            run_hour, run_minute = map(int, run_time.split(':'))
        except:
            run_hour, run_minute = 9, 0

        now = datetime.now()

        if interval_type == 'hours':
            # Legacy hourly scheduling
            if last_run:
                try:
                    last_run_dt = datetime.fromisoformat(last_run)
                    next_run = last_run_dt + timedelta(hours=interval_value)
                    next_run = next_run.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)

                    while next_run <= now:
                        next_run += timedelta(hours=interval_value)

                    return next_run
                except:
                    pass

            # Calculate next run from current time
            next_run = now.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=interval_value)
            return next_run

        elif interval_type == 'daily':
            # Daily scheduling
            next_run = now.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif interval_type == 'weekly':
            # Weekly scheduling - find next occurrence of run_day
            days_ahead = run_day - (now.weekday() + 1)
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            return next_run

        elif interval_type == 'biweekly':
            # Bi-weekly scheduling
            days_ahead = run_day - (now.weekday() + 1)
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 14  # Next occurrence in 2 weeks
            else:
                # Check if we need to skip to next cycle
                if last_run:
                    try:
                        last_run_dt = datetime.fromisoformat(last_run)
                        days_since_last = (now.date() - last_run_dt.date()).days
                        if days_since_last < 13:  # Last run was less than 2 weeks ago
                            days_ahead += 7  # Skip to next week's occurrence

                    except:
                        pass

            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            return next_run

        elif interval_type == 'monthly':
            # Monthly scheduling - find next occurrence of run_day in month
            next_run = now.replace(day=run_day, hour=run_hour, minute=run_minute, second=0, microsecond=0)

            # If the target day has passed this month, go to next month
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)

            return next_run

        return None

    def get_status(self):
        """Get scheduler status"""
        next_run = self.get_next_run_time()

        return {
            'enabled': self.config.get('enabled', False),
            'running': self.is_running,
            'interval_type': self.config.get('interval_type', 'hours'),
            'interval_value': self.config.get('interval_value', 24),
            'interval_hours': self.config.get('interval_hours', 24),  # Legacy support
            'run_time': self.config.get('run_time', '09:00'),
            'run_day': self.config.get('run_day', 1),
            'last_run': self.config.get('last_run'),
            'next_run': next_run.isoformat() if next_run else None,
            'enabled_websites': self.config.get('enabled_websites', []),
            'upload_to_sheets': self.config.get('upload_to_sheets', True)
        }

    def update_config(self, **kwargs):
        """Update scheduler configuration"""
        for key, value in kwargs.items():
            if key in ['enabled', 'interval_type', 'interval_value', 'interval_hours', 'run_time', 'run_day', 'enabled_websites', 'upload_to_sheets', 'email_notifications', 'email_address']:
                self.config[key] = value

        # Handle legacy interval_hours for backward compatibility
        if 'interval_hours' in kwargs:
            self.config['interval_type'] = 'hours'
            self.config['interval_value'] = kwargs['interval_hours']

        self.save_config()

        # Restart scheduler if it was running
        if self.is_running:
            self.stop_scheduler()
            if self.config.get('enabled', False):
                self.start_scheduler()