#!/usr/bin/env python3
"""
II Indexation Checker - Simple & Beginner-Friendly GUI
Inbound Interactive's Easy-to-Use SEO Tool
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import os
import sys
from pathlib import Path
import webbrowser
from datetime import datetime
import io
import contextlib

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from indexation_checker import check_website_indexation, save_results_to_csv
    from google_sheets_integration import GoogleSheetsIntegration
    from search_console_checker import SearchConsoleChecker
    from scheduler import IndexationScheduler
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required files are in the src/ directory")

class ConsoleRedirector:
    """Redirect console output to GUI log"""
    def __init__(self, log_function):
        self.log_function = log_function
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, message):
        try:
            if message.strip():  # Only log non-empty messages
                # Clean up the message
                clean_message = message.strip()

                # Filter out some noise but keep important messages
                if (clean_message and
                    not clean_message.startswith('[') and
                    not clean_message.startswith('Traceback') and
                    'update_idletasks' not in clean_message and
                    'invalid command name' not in clean_message and
                    'object address' not in clean_message):

                    # Categorize message types
                    if any(keyword in clean_message.lower() for keyword in ['error', 'failed', 'exception']):
                        self.log_function(f"[ERROR] {clean_message}")
                    elif any(keyword in clean_message.lower() for keyword in ['warning', 'warn']):
                        self.log_function(f"[WARN] {clean_message}")
                    elif any(keyword in clean_message.lower() for keyword in ['success', 'complete', 'done', 'uploaded']):
                        self.log_function(f"[SUCCESS] {clean_message}")
                    else:
                        self.log_function(f"[INFO] {clean_message}")

        except Exception:
            # If logging fails, just ignore it to prevent recursive errors
            pass

        # Always write to original stdout for backup
        try:
            self.original_stdout.write(message)
        except Exception:
            pass

    def flush(self):
        self.original_stdout.flush()

    def start_capture(self):
        """Start capturing console output"""
        sys.stdout = self
        sys.stderr = self

    def stop_capture(self):
        """Stop capturing and restore original output"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

class SimpleIndexationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("II Indexation Checker - Inbound Interactive")
        self.root.geometry("900x600")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(True, True)

        # Variables
        self.websites_config = None
        self.is_checking = False
        self.results = {}
        self.scheduler = IndexationScheduler()
        self.console_redirector = None
        self.stop_event = threading.Event()  # For stopping checks

        self.setup_ui()
        self.setup_console_capture()
        self.load_config()
        self.setup_scheduler()

    def setup_ui(self):
        """Setup simple, compact user interface"""
        # Top header - compact
        header = tk.Frame(self.root, bg='#2c3e50', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 II Indexation Checker - Inbound Interactive SEO Tool",
            font=('Trebuchet MS', 14, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=15)

        # Main content - no excessive padding
        main = tk.Frame(self.root, bg='#f8f9fa')
        main.pack(fill='both', expand=True, padx=10, pady=10)

        # Left side - controls (compact)
        left_frame = tk.LabelFrame(main, text="1. Select Websites & Run Check", font=('Trebuchet MS', 10, 'bold'), bg='#f8f9fa')
        left_frame.pack(side='left', fill='y', padx=(0, 10), ipadx=10, ipady=5)

        # Simple config section
        config_frame = tk.Frame(left_frame, bg='#f8f9fa')
        config_frame.pack(fill='x', pady=5)

        tk.Label(config_frame, text="Config File:", font=('Trebuchet MS', 9), bg='#f8f9fa').pack(anchor='w')

        config_input = tk.Frame(config_frame, bg='#f8f9fa')
        config_input.pack(fill='x', pady=2)

        self.config_path_var = tk.StringVar(value="config/websites.json")
        config_entry = tk.Entry(config_input, textvariable=self.config_path_var, font=('Trebuchet MS', 9), width=25)
        config_entry.pack(side='left', fill='x', expand=True)

        browse_btn = tk.Button(config_input, text="...", command=self.browse_config, width=3, font=('Trebuchet MS', 8))
        browse_btn.pack(side='right', padx=(2, 0))

        reload_btn = tk.Button(config_frame, text="Reload", command=self.load_config,
                              bg='#3498db', fg='white', font=('Trebuchet MS', 9), relief='flat')
        reload_btn.pack(pady=2)

        # Website selection - compact
        tk.Label(left_frame, text="Select websites to check:", font=('Trebuchet MS', 9, 'bold'), bg='#f8f9fa').pack(anchor='w', pady=(10, 2))

        # Compact listbox
        list_frame = tk.Frame(left_frame, bg='#f8f9fa')
        list_frame.pack(fill='both', expand=True, pady=2)

        self.websites_listbox = tk.Listbox(
            list_frame,
            selectmode='multiple',
            font=('Trebuchet MS', 9),
            height=8,
            bg='white',
            selectbackground='#3498db'
        )
        list_scroll = tk.Scrollbar(list_frame, orient='vertical', command=self.websites_listbox.yview)
        self.websites_listbox.config(yscrollcommand=list_scroll.set)

        self.websites_listbox.pack(side='left', fill='both', expand=True)
        list_scroll.pack(side='right', fill='y')

        # Status and buttons - compact
        status_frame = tk.Frame(left_frame, bg='#f8f9fa')
        status_frame.pack(fill='x', pady=5)

        tk.Label(status_frame, text="Status:", font=('Trebuchet MS', 9, 'bold'), bg='#f8f9fa').pack(anchor='w')
        self.status_label = tk.Label(status_frame, text="Ready", fg='green', font=('Trebuchet MS', 9), bg='#f8f9fa')
        self.status_label.pack(anchor='w')

        # Progress bar
        self.progress = ttk.Progressbar(left_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=5)

        # Action buttons - compact
        self.check_button = tk.Button(
            left_frame,
            text="🔍 CHECK INDEXATION",
            command=self.start_check,
            bg='#27ae60',
            fg='white',
            font=('Trebuchet MS', 10, 'bold'),
            relief='flat',
            pady=8
        )
        self.check_button.pack(fill='x', pady=2)

        # Stop button (initially hidden)
        self.stop_button = tk.Button(
            left_frame,
            text="STOP CHECK",
            command=self.stop_check,
            bg='#e74c3c',
            fg='white',
            font=('Trebuchet MS', 10, 'bold'),
            relief='flat',
            pady=8
        )
        # Don't pack the stop button initially - it will be shown when checking starts

        self.sheets_button = tk.Button(
            left_frame,
            text="📊 UPLOAD TO SHEETS",
            command=self.upload_to_sheets,
            bg='#e74c3c',
            fg='white',
            font=('Trebuchet MS', 10, 'bold'),
            relief='flat',
            pady=8
        )
        self.sheets_button.pack(fill='x', pady=2)

        # Quick action buttons
        button_row = tk.Frame(left_frame, bg='#f8f9fa')
        button_row.pack(fill='x', pady=2)

        results_btn = tk.Button(button_row, text="📁 Results", command=self.open_results_folder,
                               font=('Trebuchet MS', 8), width=8)
        results_btn.pack(side='left', padx=(0, 2))

        sheets_btn = tk.Button(button_row, text="📊 Setup", command=self.open_sheets_setup,
                              font=('Trebuchet MS', 8), width=8)
        sheets_btn.pack(side='left', padx=(2, 0))

        manage_btn = tk.Button(button_row, text="⚙️ Manage", command=self.open_website_manager,
                              font=('Trebuchet MS', 8), width=8)
        manage_btn.pack(side='left', padx=(2, 0))

        schedule_btn = tk.Button(button_row, text="⏰ Schedule", command=self.open_scheduler,
                                font=('Trebuchet MS', 8), width=8)
        schedule_btn.pack(side='right', padx=(2, 0))

        diag_btn = tk.Button(button_row, text="🔧 Diag", command=self.run_diagnostics,
                             font=('Trebuchet MS', 8), width=8)
        diag_btn.pack(side='right', padx=(2, 0))

        test_btn = tk.Button(button_row, text="🧪 Test Log", command=self.test_console_log,
                             font=('Trebuchet MS', 8), width=8)
        test_btn.pack(side='right', padx=(2, 0))

        help_btn = tk.Button(button_row, text="❓ Help", command=self.open_setup_guide,
                            font=('Trebuchet MS', 8), width=8)
        help_btn.pack(side='right', padx=(2, 0))

        # Right side - results (compact)
        right_frame = tk.LabelFrame(main, text="2. Results & Progress Log", font=('Trebuchet MS', 10, 'bold'), bg='#f8f9fa')
        right_frame.pack(side='right', fill='both', expand=True, ipadx=10, ipady=5)

        # Summary at top - compact
        self.summary_frame = tk.Frame(right_frame, bg='#e8f5e8', relief='solid', bd=1)
        self.summary_frame.pack(fill='x', pady=2)

        self.summary_label = tk.Label(
            self.summary_frame,
            text="No checks completed yet - Select websites and click 'CHECK INDEXATION'",
            font=('Trebuchet MS', 9),
            bg='#e8f5e8',
            wraplength=400
        )
        self.summary_label.pack(pady=5)

        # Log area - compact
        tk.Label(right_frame, text="Activity Log:", font=('Trebuchet MS', 9, 'bold'), bg='#f8f9fa').pack(anchor='w', pady=(5, 2))

        self.results_text = scrolledtext.ScrolledText(
            right_frame,
            font=('Consolas', 8),
            bg='#2c3e50',
            fg='#ecf0f1',
            height=20,
            wrap='word'
        )
        self.results_text.pack(fill='both', expand=True, pady=2)

        # Bottom info bar - compact with scheduler status
        info_bar = tk.Frame(self.root, bg='#34495e', height=25)
        info_bar.pack(fill='x')
        info_bar.pack_propagate(False)

        # Left side - app info
        left_info = tk.Label(
            info_bar,
            text="Inbound Interactive SEO Tools • v2.1",
            font=('Trebuchet MS', 8),
            fg='white',
            bg='#34495e'
        )
        left_info.pack(side='left', pady=4, padx=10)

        # Right side - scheduler status
        self.scheduler_status_label = tk.Label(
            info_bar,
            text="Scheduler: Disabled",
            font=('Trebuchet MS', 8),
            fg='#bdc3c7',
            bg='#34495e'
        )
        self.scheduler_status_label.pack(side='right', pady=4, padx=10)

        # Initial helpful message
        self.log("Welcome! This tool checks if your website pages are indexed by Google.")
        self.log("STEP 1: Make sure websites are selected above")
        self.log("STEP 2: Click 'CHECK INDEXATION' to start")
        self.log("STEP 3: Wait for results, then click 'UPLOAD TO SHEETS' if needed")
        self.log("-" * 60)

    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format different types of messages
        if message.startswith("[ERROR]"):
            # Error messages from console
            clean_msg = message[7:].strip()
            formatted_msg = f"[{timestamp}] ❌ {clean_msg}\n"
        elif message.startswith("[WARN]"):
            # Warning messages from console
            clean_msg = message[6:].strip()
            formatted_msg = f"[{timestamp}] ⚠️ {clean_msg}\n"
        elif message.startswith("[SUCCESS]"):
            # Success messages from console
            clean_msg = message[9:].strip()
            formatted_msg = f"[{timestamp}] ✅ {clean_msg}\n"
        elif message.startswith("[INFO]"):
            # Info messages from console
            clean_msg = message[6:].strip()
            formatted_msg = f"[{timestamp}] 🖥️ {clean_msg}\n"
        elif message.startswith("🕒") or message.startswith("🔍") or message.startswith("📊"):
            # Scheduled or important operations
            formatted_msg = f"[{timestamp}] {message}\n"
        else:
            # Regular log messages
            formatted_msg = f"[{timestamp}] {message}\n"

        # Thread-safe GUI update
        try:
            if threading.current_thread() == threading.main_thread():
                self.results_text.insert(tk.END, formatted_msg)
                self.results_text.see(tk.END)
                self.root.update_idletasks()
            else:
                # Schedule GUI update from main thread
                self.root.after(0, lambda: self._add_to_log(formatted_msg))
        except Exception:
            # If GUI update fails, just ignore it to prevent crashes
            pass

    def _add_to_log(self, formatted_message):
        """Helper method to add message to log from main thread"""
        try:
            self.results_text.insert(tk.END, formatted_message)
            self.results_text.see(tk.END)
        except Exception:
            # If GUI update fails, just ignore it
            pass

    def setup_console_capture(self):
        """Setup console output capture"""
        try:
            self.console_redirector = ConsoleRedirector(self.log)
            self.console_redirector.start_capture()
            self.log("Console output capture enabled - CMD messages will appear here")
        except Exception as e:
            self.log(f"Warning: Console capture setup failed: {e}")

        # Handle application closing to restore console
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def browse_config(self):
        """Browse for configuration file"""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="config"
        )
        if filename:
            self.config_path_var.set(filename)
            self.load_config()

    def load_config(self):
        """Load websites configuration"""
        try:
            config_path = self.config_path_var.get()
            if not os.path.exists(config_path):
                if config_path == "config/websites.json" and os.path.exists("config/websites.demo.json"):
                    # Auto-copy demo config for beginners
                    import shutil
                    shutil.copy("config/websites.demo.json", "config/websites.json")
                    self.log("Created websites.json from demo file for you!")
                else:
                    self.log(f"Config file not found: {config_path}")
                    self.log("TIP: Copy config/websites.demo.json to config/websites.json to get started")
                    self.status_label.config(text="Config file missing", fg="red")
                    return

            with open(config_path, 'r') as file:
                self.websites_config = json.load(file)

            # Simple website display
            self.websites_listbox.delete(0, tk.END)
            for i, website in enumerate(self.websites_config.get('websites', [])):
                status = "✓" if website.get('enabled', True) else "✗"
                method = "GSC" if website.get('gsc_available', False) else "Search"
                display = f"{status} {website['name']} ({method})"
                self.websites_listbox.insert(tk.END, display)

                # Auto-select enabled websites
                if website.get('enabled', True):
                    self.websites_listbox.selection_set(i)

            count = len(self.websites_config.get('websites', []))
            self.log(f"Loaded {count} websites from configuration")
            self.status_label.config(text=f"Ready - {count} websites loaded", fg="green")

        except Exception as e:
            self.log(f"Error loading config: {e}")
            self.status_label.config(text="Config error", fg="red")

    def start_check(self):
        """Start indexation check"""
        if self.is_checking:
            self.log("Check already running...")
            return

        if not self.websites_config:
            messagebox.showerror("Error", "Please load a configuration file first")
            return

        selected = self.websites_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one website to check")
            return

        # Reset stop event and start checking
        self.stop_event.clear()
        self.is_checking = True

        # Update UI - hide check button, show stop button
        self.check_button.pack_forget()
        self.stop_button.pack(fill='x', pady=2)

        self.progress.start()
        self.status_label.config(text="Checking indexation...", fg="orange")

        # Clear previous results display
        self.summary_label.config(text="Checking websites... Please wait", bg="#fff3cd")

        # Start background thread
        thread = threading.Thread(target=self.run_check, args=(selected,))
        thread.daemon = True
        thread.start()

    def stop_check(self):
        """Stop the current indexation check"""
        if not self.is_checking:
            return

        self.log("[STOP] Stopping check... Please wait for current operations to complete.")
        self.stop_event.set()  # Signal the check to stop
        self.status_label.config(text="Stopping check...", fg="red")

    def finish_check(self, stopped=False):
        """Clean up after check completion or stop"""
        self.is_checking = False
        self.progress.stop()

        # Restore UI - show check button, hide stop button
        self.stop_button.pack_forget()
        self.check_button.pack(fill='x', pady=2)

        if stopped:
            self.status_label.config(text="Check stopped by user", fg="red")
            self.log("[STOP] Check stopped by user")
        else:
            self.status_label.config(text="Check completed", fg="green")

    def run_check(self, selected_indices):
        """Run indexation check in background"""
        try:
            self.results = {}
            total_indexed = 0
            total_urls = 0

            for index in selected_indices:
                # Check if stop was requested
                if self.stop_event.is_set():
                    self.log("🛑 Check stopped by user before completion")
                    self.root.after(0, lambda: self.finish_check(stopped=True))
                    return

                website = self.websites_config['websites'][index]

                if not website.get('enabled', True):
                    self.log(f"Skipping disabled website: {website['name']}")
                    continue

                self.log(f"🔍 Checking {website['name']}...")
                self.log(f"   Method: {'Google Search Console' if website.get('gsc_available') else 'Google Search'}")

                # Add URL limit warning for large sites
                self.log(f"   ⚠️ Note: Large sites may take several minutes to check...")

                # Run the check (pass stop_event for cancellation)
                results = check_website_indexation(website, stop_event=self.stop_event)

                if results:
                    # Save results
                    filename = save_results_to_csv(results, website['name'])
                    if filename:
                        indexed_count = sum(1 for r in results if 'INDEXED' in r['status'])
                        error_count = sum(1 for r in results if 'ERROR' in r['status'])
                        rate = (indexed_count / len(results) * 100) if results else 0

                        self.results[website['name']] = {
                            'results': results,
                            'filename': filename,
                            'total': len(results),
                            'indexed': indexed_count
                        }

                        total_urls += len(results)
                        total_indexed += indexed_count

                        if error_count > 0:
                            self.log(f"⚠️ {website['name']}: {indexed_count}/{len(results)} indexed ({rate:.1f}%) - {error_count} errors")

                            # Check for specific common errors
                            has_rate_limit = any('HTTP 429' in r['status'] for r in results if 'ERROR' in r['status'])
                            has_gsc_disabled = any('Google Search Console API has not been used' in str(r) for r in results)

                            if has_rate_limit:
                                self.log(f"   💡 TIP: Google is rate-limiting searches. Enable Google Search Console for better results!")
                            if has_gsc_disabled:
                                self.log(f"   💡 TIP: Enable Search Console API in Google Cloud Console")
                        else:
                            self.log(f"✓ {website['name']}: {indexed_count}/{len(results)} indexed ({rate:.1f}%)")
                    else:
                        self.log(f"✗ Failed to save results for {website['name']}")
                else:
                    self.log(f"✗ No results for {website['name']}")

            # Update summary
            if total_urls > 0:
                overall_rate = (total_indexed / total_urls * 100)
                summary_text = f"COMPLETE! {total_indexed:,} of {total_urls:,} URLs indexed ({overall_rate:.1f}%)"

                # Color code the summary
                if overall_rate >= 80:
                    bg_color = "#d4edda"  # Green
                elif overall_rate >= 60:
                    bg_color = "#fff3cd"  # Yellow
                else:
                    bg_color = "#f8d7da"  # Red

                self.summary_label.config(text=summary_text, bg=bg_color)
                self.log(f"CHECK COMPLETE! Overall: {total_indexed}/{total_urls} URLs indexed ({overall_rate:.1f}%)")
                self.log("TIP: Click 'UPLOAD TO SHEETS' to send results to Google Sheets")
            else:
                self.summary_label.config(text="No results - check failed", bg="#f8d7da")

        except Exception as e:
            self.log(f"Error during check: {e}")
            self.summary_label.config(text="Check failed - see log for details", bg="#f8d7da")
        finally:
            # Re-enable UI
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.finish_check(stopped=False))
            # If stopped, finish_check was already called

    def check_complete(self):
        """Called when check is complete"""
        self.is_checking = False
        self.check_button.config(state='normal', text="🔍 CHECK INDEXATION")
        self.progress.stop()
        self.status_label.config(text="Check complete", fg="green")

    def upload_to_sheets(self):
        """Upload results to Google Sheets"""
        if not self.results:
            messagebox.showwarning("No Results", "Run a check first, then upload the results.")
            return

        try:
            self.log("Uploading to Google Sheets...")
            self.status_label.config(text="Uploading...", fg="orange")

            # Initialize sheets integration
            sheets = GoogleSheetsIntegration('config/google_credentials.json')

            if not sheets.client:
                self.log("Google Sheets not configured")
                messagebox.showerror("Setup Needed",
                    "Google Sheets not set up yet.\n\nSee the Help guide for setup instructions.")
                self.status_label.config(text="Sheets not configured", fg="red")
                return

            # Upload files
            uploaded = 0
            for website_name, data in self.results.items():
                filename = data['filename']
                if os.path.exists(filename):
                    success = sheets.upload_results(filename)
                    if success:
                        uploaded += 1
                        self.log(f"✓ Uploaded {website_name}")
                    else:
                        self.log(f"✗ Failed to upload {website_name}")

            if uploaded > 0:
                sheets.create_summary_sheet()
                self.log(f"SUCCESS! Uploaded {uploaded} websites to Google Sheets")
                self.status_label.config(text="Upload complete", fg="green")
                messagebox.showinfo("Success", f"Uploaded {uploaded} websites to Google Sheets!")
            else:
                self.log("No files uploaded")
                self.status_label.config(text="Upload failed", fg="red")

        except Exception as e:
            self.log(f"Upload error: {e}")
            self.status_label.config(text="Upload error", fg="red")
            messagebox.showerror("Error", f"Upload failed: {e}")

    def open_results_folder(self):
        """Open results folder"""
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        import platform
        system = platform.system()

        try:
            if system == "Windows":
                os.startfile(results_dir)
            elif system == "Darwin":  # macOS
                os.system(f"open {results_dir}")
            else:  # Linux
                os.system(f"xdg-open {results_dir}")
            self.log("Opened results folder")
        except Exception as e:
            self.log(f"Could not open folder: {e}")

    def open_setup_guide(self):
        """Open setup guide"""
        setup_file = "docs/SETUP.md"
        if os.path.exists(setup_file):
            webbrowser.open(f"file://{os.path.abspath(setup_file)}")
            self.log("Opened setup guide")
        else:
            webbrowser.open("https://github.com/inboundinteractivegit/seo-indexation-checker")
            self.log("Opened GitHub repository")

    def open_website_manager(self):
        """Open website management dialog"""
        WebsiteManagerDialog(self.root, self)

    def open_scheduler(self):
        """Open scheduler dialog"""
        SchedulerDialog(self.root, self)

    def open_sheets_setup(self):
        """Open Google Sheets setup dialog"""
        GoogleSheetsSetupDialog(self.root, self)

    def setup_scheduler(self):
        """Setup scheduler with callback"""
        self.scheduler.set_callback(self.scheduled_check_callback)
        if self.scheduler.config.get('enabled', False):
            self.scheduler.start_scheduler()
        self.update_scheduler_status()

    def update_scheduler_status(self):
        """Update scheduler status in UI"""
        status = self.scheduler.get_status()
        if status['enabled'] and status['running']:
            next_run = status.get('next_run')
            if next_run:
                try:
                    next_dt = datetime.fromisoformat(next_run)
                    next_str = next_dt.strftime("%m/%d %H:%M")
                    self.scheduler_status_label.config(text=f"Scheduler: ON (Next: {next_str})", fg='#2ecc71')
                except:
                    self.scheduler_status_label.config(text="Scheduler: ON", fg='#2ecc71')
            else:
                self.scheduler_status_label.config(text="Scheduler: ON", fg='#2ecc71')
        else:
            self.scheduler_status_label.config(text="Scheduler: OFF", fg='#bdc3c7')

        # Schedule next update in 30 seconds
        self.root.after(30000, self.update_scheduler_status)

    def scheduled_check_callback(self, enabled_websites, upload_sheets):
        """Callback for scheduled checks"""
        try:
            self.log("🕒 SCHEDULED CHECK STARTED")

            # Get selected websites or use all enabled
            if enabled_websites:
                # Filter to only enabled websites from the list
                selected_indices = []
                for i, website in enumerate(self.websites_config.get('websites', [])):
                    if website['name'] in enabled_websites and website.get('enabled', True):
                        selected_indices.append(i)
            else:
                # Use all enabled websites
                selected_indices = []
                for i, website in enumerate(self.websites_config.get('websites', [])):
                    if website.get('enabled', True):
                        selected_indices.append(i)

            if selected_indices:
                # Run check in background
                thread = threading.Thread(target=self.run_scheduled_check, args=(selected_indices, upload_sheets))
                thread.daemon = True
                thread.start()
            else:
                self.log("No enabled websites found for scheduled check")

        except Exception as e:
            self.log(f"Scheduled check error: {e}")

    def run_scheduled_check(self, selected_indices, upload_sheets):
        """Run scheduled check in background"""
        try:
            self.results = {}
            total_indexed = 0
            total_urls = 0

            for index in selected_indices:
                website = self.websites_config['websites'][index]
                self.log(f"🔍 Checking {website['name']}...")

                results = check_website_indexation(website)

                if results:
                    filename = save_results_to_csv(results, website['name'])
                    if filename:
                        indexed_count = sum(1 for r in results if 'INDEXED' in r['status'])
                        rate = (indexed_count / len(results) * 100) if results else 0

                        self.results[website['name']] = {
                            'results': results,
                            'filename': filename,
                            'total': len(results),
                            'indexed': indexed_count
                        }

                        total_urls += len(results)
                        total_indexed += indexed_count

                        self.log(f"✓ {website['name']}: {indexed_count}/{len(results)} indexed ({rate:.1f}%)")

            if total_urls > 0:
                overall_rate = (total_indexed / total_urls * 100)
                self.log(f"📊 SCHEDULED CHECK COMPLETE: {total_indexed}/{total_urls} URLs indexed ({overall_rate:.1f}%)")

                # Upload to sheets if requested
                if upload_sheets and self.results:
                    self.log("📊 Uploading scheduled results to Google Sheets...")
                    self.root.after(0, self.upload_scheduled_results)

        except Exception as e:
            self.log(f"Scheduled check error: {e}")

    def upload_scheduled_results(self):
        """Upload scheduled results to Google Sheets"""
        try:
            sheets = GoogleSheetsIntegration('config/google_credentials.json')
            if sheets.client:
                uploaded = 0
                for website_name, data in self.results.items():
                    filename = data['filename']
                    if os.path.exists(filename):
                        success = sheets.upload_results(filename)
                        if success:
                            uploaded += 1
                            self.log(f"✓ Uploaded {website_name} to sheets")

                if uploaded > 0:
                    sheets.create_summary_sheet()
                    self.log(f"📊 Uploaded {uploaded} websites to Google Sheets via scheduler")
            else:
                self.log("Google Sheets not configured for scheduled upload")
        except Exception as e:
            self.log(f"Scheduled upload error: {e}")

    def test_console_log(self):
        """Test console output capture with different message types"""
        self.log("Testing console output capture...")

        # Test different types of print statements that will be captured
        print("This is a regular info message from Python")
        print("Warning: This is a test warning message")
        print("Error: This is a test error message")
        print("Success: Console capture is working!")
        print("Failed to connect to test service")
        print("Upload completed successfully")

        self.log("Console capture test complete - check the messages above!")

    def run_diagnostics(self):
        """Run comprehensive diagnostics to identify issues"""
        self.log("🔧 RUNNING SYSTEM DIAGNOSTICS...")

        # Test 1: File structure
        self.log("1. Checking file structure...")
        if os.path.exists("config/websites.json"):
            self.log("   ✅ websites.json exists")
        else:
            self.log("   ❌ websites.json missing")

        if os.path.exists("config/google_credentials.json"):
            self.log("   ✅ google_credentials.json exists")
        else:
            self.log("   ❌ google_credentials.json missing")

        # Test 2: Config loading
        self.log("2. Testing configuration loading...")
        try:
            if self.websites_config:
                count = len(self.websites_config.get('websites', []))
                self.log(f"   ✅ Config loaded: {count} websites")
            else:
                self.log("   ❌ Config not loaded")
        except Exception as e:
            self.log(f"   ❌ Config error: {e}")

        # Test 3: Google Sheets
        self.log("3. Testing Google Sheets...")
        try:
            from google_sheets_integration import GoogleSheetsIntegration
            sheets = GoogleSheetsIntegration('config/google_credentials.json')
            if sheets.client:
                self.log("   ✅ Google Sheets client working")
            else:
                self.log("   ❌ Google Sheets client failed")
        except Exception as e:
            self.log(f"   ❌ Google Sheets error: {e}")

        # Test 4: Scheduler
        self.log("4. Testing scheduler...")
        try:
            status = self.scheduler.get_status()
            self.log(f"   ✅ Scheduler status: {'enabled' if status['enabled'] else 'disabled'}")
        except Exception as e:
            self.log(f"   ❌ Scheduler error: {e}")

        # Test 5: Button states
        self.log("5. Checking UI state...")
        selected = self.websites_listbox.curselection()
        self.log(f"   Selected websites: {len(selected)}")
        self.log(f"   Checking in progress: {self.is_checking}")

        # Test 6: Test specific website sitemaps
        self.log("6. Testing website sitemaps...")
        if self.websites_config:
            for website in self.websites_config.get('websites', []):
                if website.get('enabled', True):
                    self.log(f"   Testing {website['name']}...")
                    try:
                        # Test sitemap URLs
                        if 'sitemap_url' in website:
                            self.log(f"      Sitemap: {website['sitemap_url']}")
                        elif 'sitemap_urls' in website:
                            for url in website['sitemap_urls']:
                                self.log(f"      Sitemap: {url}")

                        # Test GSC availability
                        gsc_status = "GSC enabled" if website.get('gsc_available', False) else "Search fallback"
                        self.log(f"      Method: {gsc_status}")

                    except Exception as e:
                        self.log(f"      ❌ Error: {e}")

        self.log("🔧 DIAGNOSTICS COMPLETE!")
        self.log("If you see errors above, that's what needs to be fixed.")

    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop console capture
            if self.console_redirector:
                self.console_redirector.stop_capture()

            # Stop scheduler
            if self.scheduler:
                self.scheduler.stop_scheduler()

            # Close the application
            self.root.destroy()
        except Exception as e:
            print(f"Error during closing: {e}")
            self.root.destroy()

class WebsiteManagerDialog:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Website Manager - Add/Edit Sites")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg='#f8f9fa')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self.setup_ui()
        self.load_websites()

    def setup_ui(self):
        """Setup the website manager UI"""
        # Title
        title_frame = tk.Frame(self.dialog, bg='#2c3e50', height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="🌐 Website Manager",
                font=('Trebuchet MS', 12, 'bold'), fg='white', bg='#2c3e50').pack(pady=12)

        # Main content
        main_frame = tk.Frame(self.dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Website list
        list_frame = tk.LabelFrame(main_frame, text="Current Websites", font=('Trebuchet MS', 10, 'bold'))
        list_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Listbox with scrollbar
        list_container = tk.Frame(list_frame)
        list_container.pack(fill='both', expand=True, padx=10, pady=10)

        self.websites_list = tk.Listbox(list_container, font=('Trebuchet MS', 9), height=8)
        list_scroll = tk.Scrollbar(list_container, orient='vertical', command=self.websites_list.yview)
        self.websites_list.config(yscrollcommand=list_scroll.set)

        self.websites_list.pack(side='left', fill='both', expand=True)
        list_scroll.pack(side='right', fill='y')

        # Buttons
        button_frame = tk.Frame(list_frame)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))

        tk.Button(button_frame, text="➕ Add Website", command=self.add_website,
                 bg='#27ae60', fg='white', font=('Trebuchet MS', 9, 'bold')).pack(side='left', padx=(0, 5))

        tk.Button(button_frame, text="✏️ Edit Selected", command=self.edit_website,
                 bg='#3498db', fg='white', font=('Trebuchet MS', 9, 'bold')).pack(side='left', padx=5)

        tk.Button(button_frame, text="🗑️ Delete Selected", command=self.delete_website,
                 bg='#e74c3c', fg='white', font=('Trebuchet MS', 9, 'bold')).pack(side='left', padx=5)

        # Add form
        self.form_frame = tk.LabelFrame(main_frame, text="Add/Edit Website", font=('Trebuchet MS', 10, 'bold'))
        self.form_frame.pack(fill='x')

        # Form fields
        form_content = tk.Frame(self.form_frame)
        form_content.pack(fill='x', padx=10, pady=10)

        # Website name
        tk.Label(form_content, text="Website Name:", font=('Trebuchet MS', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=2)
        self.name_var = tk.StringVar()
        tk.Entry(form_content, textvariable=self.name_var, font=('Trebuchet MS', 9), width=40).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)

        # Sitemap URL(s)
        tk.Label(form_content, text="Sitemap URLs:", font=('Trebuchet MS', 9, 'bold')).grid(row=1, column=0, sticky='nw', pady=2)
        self.sitemap_text = tk.Text(form_content, height=3, width=40, font=('Trebuchet MS', 9))
        self.sitemap_text.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)

        # Options
        options_frame = tk.Frame(form_content)
        options_frame.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=5)

        self.enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Enabled", variable=self.enabled_var, font=('Trebuchet MS', 9)).pack(side='left')

        self.gsc_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Google Search Console Available", variable=self.gsc_var, font=('Trebuchet MS', 9)).pack(side='left', padx=(20, 0))

        # IndexedAPI configuration
        tk.Label(form_content, text="IndexedAPI Key:", font=('Trebuchet MS', 9, 'bold')).grid(row=3, column=0, sticky='w', pady=2)
        self.indexed_api_var = tk.StringVar()
        tk.Entry(form_content, textvariable=self.indexed_api_var, font=('Trebuchet MS', 9), width=40, show="*").grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=2)

        # Checking method
        tk.Label(form_content, text="Checking Method:", font=('Trebuchet MS', 9, 'bold')).grid(row=4, column=0, sticky='w', pady=2)
        method_frame = tk.Frame(form_content)
        method_frame.grid(row=4, column=1, sticky='ew', padx=(10, 0), pady=2)

        self.checking_method_var = tk.StringVar(value="auto")
        methods = [("Auto (Best Available)", "auto"), ("Google Search Console", "gsc"),
                  ("IndexedAPI", "indexed_api"), ("Google Search", "google_search")]

        for i, (text, value) in enumerate(methods):
            tk.Radiobutton(method_frame, text=text, variable=self.checking_method_var, value=value,
                          font=('Trebuchet MS', 8)).pack(side='left', padx=(0 if i == 0 else 10, 0))

        # Description
        tk.Label(form_content, text="Description:", font=('Trebuchet MS', 9, 'bold')).grid(row=5, column=0, sticky='w', pady=2)
        self.desc_var = tk.StringVar()
        tk.Entry(form_content, textvariable=self.desc_var, font=('Trebuchet MS', 9), width=40).grid(row=5, column=1, sticky='ew', padx=(10, 0), pady=2)

        form_content.columnconfigure(1, weight=1)

        # Form buttons
        form_buttons = tk.Frame(self.form_frame)
        form_buttons.pack(fill='x', padx=10, pady=(0, 10))

        tk.Button(form_buttons, text="💾 Save Website", command=self.save_website,
                 bg='#27ae60', fg='white', font=('Trebuchet MS', 9, 'bold')).pack(side='left')

        tk.Button(form_buttons, text="🔄 Clear Form", command=self.clear_form,
                 bg='#95a5a6', fg='white', font=('Trebuchet MS', 9, 'bold')).pack(side='left', padx=(10, 0))

        # Close button
        tk.Button(main_frame, text="✅ Close & Reload", command=self.close_dialog,
                 bg='#34495e', fg='white', font=('Trebuchet MS', 10, 'bold')).pack(pady=(10, 0))

        # Current editing index
        self.edit_index = None

    def load_websites(self):
        """Load websites into the list"""
        self.websites_list.delete(0, tk.END)
        if hasattr(self.main_app, 'websites_config') and self.main_app.websites_config:
            for i, website in enumerate(self.main_app.websites_config.get('websites', [])):
                status = "✓" if website.get('enabled', True) else "✗"

                # Determine method display
                method = website.get('checking_method', 'auto')
                if method == 'gsc':
                    method_display = "GSC"
                elif method == 'indexed_api':
                    method_display = "IndexedAPI"
                elif method == 'google_search':
                    method_display = "Search"
                else:  # auto
                    if website.get('gsc_available', False):
                        method_display = "Auto(GSC)"
                    elif website.get('indexed_api_key'):
                        method_display = "Auto(API)"
                    else:
                        method_display = "Auto(Search)"

                display = f"{status} {website['name']} ({method_display})"
                self.websites_list.insert(tk.END, display)

    def add_website(self):
        """Add new website"""
        self.clear_form()
        self.edit_index = None
        self.form_frame.config(text="Add New Website")

    def edit_website(self):
        """Edit selected website"""
        selection = self.websites_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a website to edit")
            return

        self.edit_index = selection[0]
        website = self.main_app.websites_config['websites'][self.edit_index]

        # Populate form
        self.name_var.set(website['name'])
        self.desc_var.set(website.get('description', ''))
        self.enabled_var.set(website.get('enabled', True))
        self.gsc_var.set(website.get('gsc_available', False))
        self.indexed_api_var.set(website.get('indexed_api_key', ''))
        self.checking_method_var.set(website.get('checking_method', 'auto'))

        # Handle sitemap URLs
        self.sitemap_text.delete(1.0, tk.END)
        if 'sitemap_url' in website:
            self.sitemap_text.insert(1.0, website['sitemap_url'])
        elif 'sitemap_urls' in website:
            self.sitemap_text.insert(1.0, '\n'.join(website['sitemap_urls']))

        self.form_frame.config(text="Edit Website")

    def delete_website(self):
        """Delete selected website"""
        selection = self.websites_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a website to delete")
            return

        website = self.main_app.websites_config['websites'][selection[0]]
        if messagebox.askyesno("Confirm Delete", f"Delete '{website['name']}'?"):
            del self.main_app.websites_config['websites'][selection[0]]
            self.save_config()
            self.load_websites()
            self.clear_form()

    def save_website(self):
        """Save website to config"""
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Website name is required")
            return

        sitemap_content = self.sitemap_text.get(1.0, tk.END).strip()
        if not sitemap_content:
            messagebox.showerror("Error", "At least one sitemap URL is required")
            return

        # Create website data
        website_data = {
            "name": self.name_var.get().strip(),
            "enabled": self.enabled_var.get(),
            "gsc_available": self.gsc_var.get(),
            "description": self.desc_var.get().strip(),
            "checking_method": self.checking_method_var.get()
        }

        # Add IndexedAPI key if provided
        indexed_api_key = self.indexed_api_var.get().strip()
        if indexed_api_key:
            website_data["indexed_api_key"] = indexed_api_key

        # Handle sitemap URLs
        sitemap_lines = [line.strip() for line in sitemap_content.split('\n') if line.strip()]
        if len(sitemap_lines) == 1:
            website_data["sitemap_url"] = sitemap_lines[0]
        else:
            website_data["sitemap_urls"] = sitemap_lines

        # Add or update
        if self.edit_index is not None:
            self.main_app.websites_config['websites'][self.edit_index] = website_data
        else:
            self.main_app.websites_config['websites'].append(website_data)

        self.save_config()
        self.load_websites()
        self.clear_form()
        messagebox.showinfo("Success", "Website saved successfully!")

    def save_config(self):
        """Save configuration to file"""
        try:
            config_path = self.main_app.config_path_var.get()
            with open(config_path, 'w') as file:
                json.dump(self.main_app.websites_config, file, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def clear_form(self):
        """Clear the form"""
        self.name_var.set("")
        self.desc_var.set("")
        self.sitemap_text.delete(1.0, tk.END)
        self.enabled_var.set(True)
        self.gsc_var.set(False)
        self.indexed_api_var.set("")
        self.checking_method_var.set("auto")
        self.edit_index = None
        self.form_frame.config(text="Add/Edit Website")

    def close_dialog(self):
        """Close dialog and reload main app"""
        self.main_app.load_config()  # Reload in main app
        self.dialog.destroy()

class SchedulerDialog:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.scheduler = main_app.scheduler

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Scheduler - Automated Indexation Checks")
        self.dialog.geometry("550x600")
        self.dialog.configure(bg='#f8f9fa')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the scheduler UI"""
        # Title
        title_frame = tk.Frame(self.dialog, bg='#2c3e50', height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="⏰ Automated Scheduler",
                font=('Trebuchet MS', 12, 'bold'), fg='white', bg='#2c3e50').pack(pady=12)

        # Main content
        main_frame = tk.Frame(self.dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Enable/Disable
        status_frame = tk.LabelFrame(main_frame, text="Scheduler Status", font=('Trebuchet MS', 10, 'bold'))
        status_frame.pack(fill='x', pady=(0, 10))

        status_content = tk.Frame(status_frame)
        status_content.pack(fill='x', padx=10, pady=10)

        self.enabled_var = tk.BooleanVar()
        enable_check = tk.Checkbutton(
            status_content,
            text="Enable Automatic Indexation Checks",
            variable=self.enabled_var,
            font=('Trebuchet MS', 10, 'bold'),
            command=self.toggle_scheduler
        )
        enable_check.pack(anchor='w')

        # Status display
        self.status_display = tk.Label(
            status_content,
            text="Scheduler is currently disabled",
            font=('Trebuchet MS', 9),
            fg='#7f8c8d'
        )
        self.status_display.pack(anchor='w', pady=(5, 0))

        # Schedule Settings
        schedule_frame = tk.LabelFrame(main_frame, text="Schedule Settings", font=('Trebuchet MS', 10, 'bold'))
        schedule_frame.pack(fill='x', pady=(0, 10))

        schedule_content = tk.Frame(schedule_frame)
        schedule_content.pack(fill='x', padx=10, pady=10)

        # Interval Type
        tk.Label(schedule_content, text="Schedule:", font=('Trebuchet MS', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=2)

        interval_frame = tk.Frame(schedule_content)
        interval_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)

        self.interval_type_var = tk.StringVar(value="daily")
        interval_options = [
            ("Every __ hours", "hours"),
            ("Daily", "daily"),
            ("Weekly", "weekly"),
            ("Bi-weekly", "biweekly"),
            ("Monthly", "monthly")
        ]

        self.interval_combo = ttk.Combobox(
            interval_frame,
            textvariable=self.interval_type_var,
            values=[opt[0] for opt in interval_options],
            state="readonly",
            width=15,
            font=('Trebuchet MS', 9)
        )
        self.interval_combo.pack(side='left')
        self.interval_combo.bind('<<ComboboxSelected>>', self.on_interval_type_change)

        # Hour interval input (only shown for hourly)
        self.hour_interval_frame = tk.Frame(interval_frame)
        self.hour_interval_frame.pack(side='left', padx=(5, 0))

        self.interval_value_var = tk.StringVar(value="24")
        self.hour_spin = tk.Spinbox(
            self.hour_interval_frame,
            from_=1, to=168,
            textvariable=self.interval_value_var,
            width=5,
            font=('Trebuchet MS', 9)
        )
        self.hour_spin.pack(side='left')

        tk.Label(self.hour_interval_frame, text="hours", font=('Trebuchet MS', 9)).pack(side='left', padx=(2, 0))

        # Day selection (for weekly/monthly)
        tk.Label(schedule_content, text="Run on:", font=('Trebuchet MS', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=2)

        day_frame = tk.Frame(schedule_content)
        day_frame.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)

        self.day_var = tk.StringVar(value="1")

        # Day of week selector (for weekly/biweekly)
        self.weekday_frame = tk.Frame(day_frame)
        self.weekday_frame.pack(side='left')

        weekday_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.weekday_combo = ttk.Combobox(
            self.weekday_frame,
            values=weekday_options,
            state="readonly",
            width=10,
            font=('Trebuchet MS', 9)
        )
        self.weekday_combo.pack(side='left')
        self.weekday_combo.set("Monday")

        # Day of month selector (for monthly)
        self.monthday_frame = tk.Frame(day_frame)
        self.monthday_frame.pack(side='left')

        tk.Label(self.monthday_frame, text="Day", font=('Trebuchet MS', 9)).pack(side='left')
        self.monthday_spin = tk.Spinbox(
            self.monthday_frame,
            from_=1, to=28,
            textvariable=self.day_var,
            width=3,
            font=('Trebuchet MS', 9)
        )
        self.monthday_spin.pack(side='left', padx=(5, 0))
        tk.Label(self.monthday_frame, text="of month", font=('Trebuchet MS', 9)).pack(side='left', padx=(5, 0))

        # Time of day
        tk.Label(schedule_content, text="Run at time:", font=('Trebuchet MS', 9, 'bold')).grid(row=2, column=0, sticky='w', pady=2)

        time_frame = tk.Frame(schedule_content)
        time_frame.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)

        self.hour_var = tk.StringVar(value="09")
        hour_spin = tk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=3, format="%02.0f", font=('Trebuchet MS', 9))
        hour_spin.pack(side='left')

        tk.Label(time_frame, text=":", font=('Trebuchet MS', 9)).pack(side='left')

        self.minute_var = tk.StringVar(value="00")
        minute_spin = tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=3, format="%02.0f", font=('Trebuchet MS', 9))
        minute_spin.pack(side='left')

        tk.Label(time_frame, text="(24-hour format)", font=('Trebuchet MS', 8), fg='#7f8c8d').pack(side='left', padx=(10, 0))

        schedule_content.columnconfigure(1, weight=1)

        # Initially hide day selectors and hour interval
        self.update_schedule_controls()

        # Website Selection
        websites_frame = tk.LabelFrame(main_frame, text="Websites to Check", font=('Trebuchet MS', 10, 'bold'))
        websites_frame.pack(fill='both', expand=True, pady=(0, 10))

        websites_content = tk.Frame(websites_frame)
        websites_content.pack(fill='both', expand=True, padx=10, pady=10)

        tk.Label(websites_content, text="Select which websites to include in scheduled checks:", font=('Trebuchet MS', 9)).pack(anchor='w')

        # Websites listbox with checkboxes
        list_frame = tk.Frame(websites_content)
        list_frame.pack(fill='both', expand=True, pady=5)

        self.websites_listbox = tk.Listbox(
            list_frame,
            selectmode='multiple',
            font=('Trebuchet MS', 9),
            height=8
        )
        websites_scroll = tk.Scrollbar(list_frame, orient='vertical', command=self.websites_listbox.yview)
        self.websites_listbox.config(yscrollcommand=websites_scroll.set)

        self.websites_listbox.pack(side='left', fill='both', expand=True)
        websites_scroll.pack(side='right', fill='y')

        # Select all/none buttons
        select_frame = tk.Frame(websites_content)
        select_frame.pack(fill='x', pady=2)

        tk.Button(select_frame, text="Select All", command=self.select_all_websites,
                 font=('Trebuchet MS', 8)).pack(side='left')

        tk.Button(select_frame, text="Select None", command=self.select_no_websites,
                 font=('Trebuchet MS', 8)).pack(side='left', padx=(5, 0))

        # Options
        options_frame = tk.LabelFrame(main_frame, text="Options", font=('Trebuchet MS', 10, 'bold'))
        options_frame.pack(fill='x', pady=(0, 10))

        options_content = tk.Frame(options_frame)
        options_content.pack(fill='x', padx=10, pady=10)

        self.upload_sheets_var = tk.BooleanVar(value=True)
        sheets_check = tk.Checkbutton(
            options_content,
            text="Automatically upload results to Google Sheets",
            variable=self.upload_sheets_var,
            font=('Trebuchet MS', 9)
        )
        sheets_check.pack(anchor='w')

        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x')

        tk.Button(button_frame, text="💾 Save Settings", command=self.save_settings,
                 bg='#27ae60', fg='white', font=('Trebuchet MS', 10, 'bold')).pack(side='left')

        tk.Button(button_frame, text="🧪 Test Now", command=self.test_now,
                 bg='#3498db', fg='white', font=('Trebuchet MS', 10, 'bold')).pack(side='left', padx=(10, 0))

        tk.Button(button_frame, text="✅ Close", command=self.close_dialog,
                 bg='#34495e', fg='white', font=('Trebuchet MS', 10, 'bold')).pack(side='right')

    def load_settings(self):
        """Load current scheduler settings"""
        config = self.scheduler.config

        self.enabled_var.set(config.get('enabled', False))
        self.upload_sheets_var.set(config.get('upload_to_sheets', True))

        # Load interval settings
        interval_type = config.get('interval_type', 'daily')
        interval_value = config.get('interval_value', 24)

        # Map interval type to combo box
        type_mapping = {
            'hours': 'Every __ hours',
            'daily': 'Daily',
            'weekly': 'Weekly',
            'biweekly': 'Bi-weekly',
            'monthly': 'Monthly'
        }

        self.interval_type_var.set(type_mapping.get(interval_type, 'Daily'))
        self.interval_value_var.set(str(interval_value))

        # Load day settings
        run_day = config.get('run_day', 1)
        if interval_type in ['weekly', 'biweekly']:
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if 1 <= run_day <= 7:
                self.weekday_combo.set(weekdays[run_day - 1])
        elif interval_type == 'monthly':
            self.day_var.set(str(run_day))

        # Parse run time
        run_time = config.get('run_time', '09:00')
        try:
            hour, minute = run_time.split(':')
            self.hour_var.set(f"{int(hour):02d}")
            self.minute_var.set(f"{int(minute):02d}")
        except:
            self.hour_var.set("09")
            self.minute_var.set("00")

        # Update controls visibility
        self.update_schedule_controls()

        # Load websites
        self.load_websites()
        self.update_status_display()

    def load_websites(self):
        """Load websites into the list"""
        self.websites_listbox.delete(0, tk.END)

        if hasattr(self.main_app, 'websites_config') and self.main_app.websites_config:
            enabled_websites = self.scheduler.config.get('enabled_websites', [])

            for i, website in enumerate(self.main_app.websites_config.get('websites', [])):
                if website.get('enabled', True):
                    status = "GSC" if website.get('gsc_available', False) else "Search"
                    display = f"{website['name']} ({status})"
                    self.websites_listbox.insert(tk.END, display)

                    # Auto-select if in enabled list
                    if website['name'] in enabled_websites:
                        self.websites_listbox.selection_set(i)

    def select_all_websites(self):
        """Select all websites"""
        self.websites_listbox.select_set(0, tk.END)

    def select_no_websites(self):
        """Deselect all websites"""
        self.websites_listbox.selection_clear(0, tk.END)

    def on_interval_type_change(self, event=None):
        """Handle interval type change"""
        self.update_schedule_controls()
        self.update_status_display()

    def update_schedule_controls(self):
        """Show/hide controls based on interval type"""
        interval_type = self.interval_type_var.get()

        # Hide all controls first
        self.hour_interval_frame.pack_forget()
        self.weekday_frame.pack_forget()
        self.monthday_frame.pack_forget()

        if interval_type == "Every __ hours":
            # Show hour interval input
            self.hour_interval_frame.pack(side='left', padx=(5, 0))
        elif interval_type in ["Weekly", "Bi-weekly"]:
            # Show weekday selector
            self.weekday_frame.pack(side='left')
        elif interval_type == "Monthly":
            # Show day of month selector
            self.monthday_frame.pack(side='left')
        # Daily doesn't need additional controls

    def toggle_scheduler(self):
        """Toggle scheduler on/off"""
        self.update_status_display()

    def update_status_display(self):
        """Update the status display"""
        if self.enabled_var.get():
            status = self.scheduler.get_status()
            next_run = status.get('next_run')

            if next_run:
                try:
                    next_dt = datetime.fromisoformat(next_run)
                    next_str = next_dt.strftime("%Y-%m-%d at %H:%M")
                    self.status_display.config(
                        text=f"Scheduler is ENABLED. Next run: {next_str}",
                        fg='#27ae60'
                    )
                except:
                    self.status_display.config(
                        text="Scheduler is ENABLED",
                        fg='#27ae60'
                    )
            else:
                # Generate preview text based on current settings
                interval_type = self.interval_type_var.get()
                time_str = f"{self.hour_var.get()}:{self.minute_var.get()}"

                if interval_type == "Every __ hours":
                    interval_value = self.interval_value_var.get()
                    preview = f"every {interval_value} hours at {time_str}"
                elif interval_type == "Daily":
                    preview = f"daily at {time_str}"
                elif interval_type == "Weekly":
                    weekday = self.weekday_combo.get()
                    preview = f"weekly on {weekday} at {time_str}"
                elif interval_type == "Bi-weekly":
                    weekday = self.weekday_combo.get()
                    preview = f"bi-weekly on {weekday} at {time_str}"
                elif interval_type == "Monthly":
                    day = self.day_var.get()
                    preview = f"monthly on day {day} at {time_str}"
                else:
                    preview = f"at {time_str}"

                self.status_display.config(
                    text=f"Scheduler will run {preview}",
                    fg='#27ae60'
                )
        else:
            self.status_display.config(
                text="Scheduler is currently DISABLED",
                fg='#e74c3c'
            )

    def save_settings(self):
        """Save scheduler settings"""
        try:
            # Get selected websites
            selected_indices = self.websites_listbox.curselection()
            enabled_websites = []

            for index in selected_indices:
                if hasattr(self.main_app, 'websites_config') and self.main_app.websites_config:
                    websites = [w for w in self.main_app.websites_config.get('websites', []) if w.get('enabled', True)]
                    if index < len(websites):
                        enabled_websites.append(websites[index]['name'])

            # Convert interval type back to internal format
            interval_type_map = {
                'Every __ hours': 'hours',
                'Daily': 'daily',
                'Weekly': 'weekly',
                'Bi-weekly': 'biweekly',
                'Monthly': 'monthly'
            }

            interval_type = interval_type_map.get(self.interval_type_var.get(), 'daily')
            run_time = f"{self.hour_var.get()}:{self.minute_var.get()}"

            # Determine interval value and run day
            if interval_type == 'hours':
                interval_value = int(self.interval_value_var.get())
                run_day = 1  # Not used for hourly
            elif interval_type in ['weekly', 'biweekly']:
                interval_value = 1  # Not used for weekly/biweekly
                weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                run_day = weekdays.index(self.weekday_combo.get()) + 1
            elif interval_type == 'monthly':
                interval_value = 1  # Not used for monthly
                run_day = int(self.day_var.get())
            else:  # daily
                interval_value = 1
                run_day = 1

            # Update scheduler config
            self.scheduler.update_config(
                enabled=self.enabled_var.get(),
                interval_type=interval_type,
                interval_value=interval_value,
                run_time=run_time,
                run_day=run_day,
                enabled_websites=enabled_websites,
                upload_to_sheets=self.upload_sheets_var.get()
            )

            self.update_status_display()
            self.main_app.update_scheduler_status()

            messagebox.showinfo("Success", "Scheduler settings saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def test_now(self):
        """Run a test check now"""
        try:
            selected_indices = self.websites_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one website to test")
                return

            # Get selected websites
            enabled_websites = []
            for index in selected_indices:
                if hasattr(self.main_app, 'websites_config') and self.main_app.websites_config:
                    websites = [w for w in self.main_app.websites_config.get('websites', []) if w.get('enabled', True)]
                    if index < len(websites):
                        enabled_websites.append(websites[index]['name'])

            if enabled_websites:
                self.main_app.log("🧪 TESTING SCHEDULED CHECK...")
                self.main_app.scheduled_check_callback(enabled_websites, self.upload_sheets_var.get())
                messagebox.showinfo("Test Started", "Test check started! Check the main window for progress.")
            else:
                messagebox.showwarning("No Websites", "No websites selected for testing")

        except Exception as e:
            messagebox.showerror("Error", f"Test failed: {e}")

    def close_dialog(self):
        """Close dialog"""
        self.dialog.destroy()

class GoogleSheetsSetupDialog:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Google Sheets Setup - Easy Configuration")
        self.dialog.geometry("600x700")
        self.dialog.configure(bg='#f8f9fa')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self.setup_ui()
        self.check_current_setup()

    def setup_ui(self):
        """Setup the Google Sheets configuration UI"""
        # Title
        title_frame = tk.Frame(self.dialog, bg='#2c3e50', height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="📊 Google Sheets Integration Setup",
                font=('Trebuchet MS', 12, 'bold'), fg='white', bg='#2c3e50').pack(pady=12)

        # Main content
        main_frame = tk.Frame(self.dialog, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Status section
        status_frame = tk.LabelFrame(main_frame, text="Current Status", font=('Trebuchet MS', 10, 'bold'))
        status_frame.pack(fill='x', pady=(0, 10))

        status_content = tk.Frame(status_frame)
        status_content.pack(fill='x', padx=10, pady=10)

        self.status_label = tk.Label(
            status_content,
            text="Checking Google Sheets configuration...",
            font=('Trebuchet MS', 9),
            fg='#7f8c8d',
            wraplength=500
        )
        self.status_label.pack(anchor='w')

        # Instructions section
        instructions_frame = tk.LabelFrame(main_frame, text="Setup Instructions", font=('Trebuchet MS', 10, 'bold'))
        instructions_frame.pack(fill='both', expand=True, pady=(0, 10))

        instructions_content = tk.Frame(instructions_frame)
        instructions_content.pack(fill='both', expand=True, padx=10, pady=10)

        instructions_text = tk.Text(
            instructions_content,
            height=15,
            wrap='word',
            font=('Trebuchet MS', 9),
            bg='#ffffff',
            relief='flat',
            bd=1
        )
        instructions_scroll = tk.Scrollbar(instructions_content, orient='vertical', command=instructions_text.yview)
        instructions_text.config(yscrollcommand=instructions_scroll.set)

        instructions_text.pack(side='left', fill='both', expand=True)
        instructions_scroll.pack(side='right', fill='y')

        # Add detailed instructions
        instructions = """📋 GOOGLE SHEETS SETUP GUIDE

🎯 WHAT YOU NEED:
• Google Cloud Project with Sheets API enabled
• Service Account with JSON credentials file
• Share your Google Sheets with the service account email

📝 STEP-BY-STEP SETUP:

1️⃣ CREATE GOOGLE CLOUD PROJECT:
   • Go to: https://console.cloud.google.com/
   • Click "Select a project" → "New Project"
   • Name: "SEO Indexation Checker" → Create

2️⃣ ENABLE GOOGLE SHEETS API:
   • In your project, go to "APIs & Services" → "Library"
   • Search "Google Sheets API" → Enable it

3️⃣ CREATE SERVICE ACCOUNT:
   • Go to "APIs & Services" → "Credentials"
   • Click "Create Credentials" → "Service Account"
   • Name: "indexation-checker" → Create
   • Skip roles (click Continue → Done)

4️⃣ DOWNLOAD CREDENTIALS:
   • Click on your service account email
   • Go to "Keys" tab → "Add Key" → "Create new key"
   • Choose "JSON" → Create & Download
   • IMPORTANT: Save as "google_credentials.json"

5️⃣ SHARE YOUR SPREADSHEET:
   • Open your Google Sheets document
   • Click "Share" button
   • Add the service account email (looks like: name@project.iam.gserviceaccount.com)
   • Give "Editor" permissions → Send

6️⃣ UPLOAD CREDENTIALS:
   • Use the button below to upload your JSON file
   • File will be saved as: config/google_credentials.json

✅ THAT'S IT! Your SEO tool can now automatically upload results to Google Sheets.

💡 TIP: The service account email is in your downloaded JSON file under "client_email"
"""

        instructions_text.insert(1.0, instructions)
        instructions_text.config(state='disabled')

        # Credentials upload section
        upload_frame = tk.LabelFrame(main_frame, text="Upload Credentials", font=('Trebuchet MS', 10, 'bold'))
        upload_frame.pack(fill='x', pady=(0, 10))

        upload_content = tk.Frame(upload_frame)
        upload_content.pack(fill='x', padx=10, pady=10)

        tk.Label(upload_content, text="Select your google_credentials.json file:",
                font=('Trebuchet MS', 9, 'bold')).pack(anchor='w')

        file_frame = tk.Frame(upload_content)
        file_frame.pack(fill='x', pady=5)

        self.file_path_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.file_path_var, font=('Trebuchet MS', 9), state='readonly')
        file_entry.pack(side='left', fill='x', expand=True)

        browse_btn = tk.Button(file_frame, text="📁 Browse", command=self.browse_credentials,
                              bg='#3498db', fg='white', font=('Trebuchet MS', 9, 'bold'))
        browse_btn.pack(side='right', padx=(5, 0))

        upload_btn = tk.Button(upload_content, text="⬆️ Upload & Configure", command=self.upload_credentials,
                              bg='#27ae60', fg='white', font=('Trebuchet MS', 10, 'bold'))
        upload_btn.pack(pady=5)

        # Test section
        test_frame = tk.LabelFrame(main_frame, text="Test Connection", font=('Trebuchet MS', 10, 'bold'))
        test_frame.pack(fill='x', pady=(0, 10))

        test_content = tk.Frame(test_frame)
        test_content.pack(fill='x', padx=10, pady=10)

        test_btn = tk.Button(test_content, text="🧪 Test Google Sheets Connection", command=self.test_connection,
                            bg='#f39c12', fg='white', font=('Trebuchet MS', 10, 'bold'))
        test_btn.pack()

        # Close button
        tk.Button(main_frame, text="✅ Close", command=self.close_dialog,
                 bg='#34495e', fg='white', font=('Trebuchet MS', 10, 'bold')).pack(pady=(10, 0))

    def check_current_setup(self):
        """Check if Google Sheets is already configured"""
        try:
            credentials_path = "config/google_credentials.json"
            if os.path.exists(credentials_path):
                # Try to load credentials and get service account email
                with open(credentials_path, 'r') as f:
                    creds_data = json.load(f)
                    service_email = creds_data.get('client_email', 'Unknown')

                self.status_label.config(
                    text=f"✅ Google Sheets is CONFIGURED!\nService Account: {service_email}\n\nYou can now upload results to Google Sheets automatically.",
                    fg='#27ae60'
                )
            else:
                self.status_label.config(
                    text="❌ Google Sheets is NOT configured.\n\nFollow the instructions below to set up automatic Google Sheets integration.",
                    fg='#e74c3c'
                )
        except Exception as e:
            self.status_label.config(
                text=f"⚠️ Configuration file exists but has errors: {e}\n\nPlease re-upload your credentials file.",
                fg='#f39c12'
            )

    def browse_credentials(self):
        """Browse for Google credentials JSON file"""
        filename = filedialog.askopenfilename(
            title="Select Google Credentials JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~/Downloads")
        )
        if filename:
            self.file_path_var.set(filename)

    def upload_credentials(self):
        """Upload and configure Google credentials"""
        source_file = self.file_path_var.get()
        if not source_file:
            messagebox.showerror("No File Selected", "Please select a JSON credentials file first.")
            return

        if not os.path.exists(source_file):
            messagebox.showerror("File Not Found", "The selected file does not exist.")
            return

        try:
            # Validate JSON format
            with open(source_file, 'r') as f:
                creds_data = json.load(f)

            # Check for required fields
            required_fields = ['client_email', 'private_key', 'project_id']
            missing_fields = [field for field in required_fields if field not in creds_data]

            if missing_fields:
                messagebox.showerror("Invalid Credentials",
                    f"The JSON file is missing required fields: {', '.join(missing_fields)}\n\nPlease ensure you downloaded the correct service account key file.")
                return

            # Create config directory if it doesn't exist
            os.makedirs("config", exist_ok=True)

            # Copy file to config directory
            destination = "config/google_credentials.json"
            import shutil
            shutil.copy2(source_file, destination)

            service_email = creds_data.get('client_email', 'Unknown')

            messagebox.showinfo("Success!",
                f"✅ Google Sheets credentials uploaded successfully!\n\n"
                f"Service Account Email:\n{service_email}\n\n"
                f"IMPORTANT: Make sure to share your Google Sheets with this email address and give it 'Editor' permissions.")

            # Update status
            self.check_current_setup()

            # Log to main app
            self.main_app.log(f"✅ Google Sheets credentials configured: {service_email}")

        except json.JSONDecodeError:
            messagebox.showerror("Invalid File", "The selected file is not a valid JSON file.")
        except Exception as e:
            messagebox.showerror("Upload Failed", f"Failed to upload credentials: {e}")

    def test_connection(self):
        """Test Google Sheets connection"""
        try:
            from google_sheets_integration import GoogleSheetsIntegration

            self.main_app.log("🧪 Testing Google Sheets connection...")

            sheets = GoogleSheetsIntegration('config/google_credentials.json')

            if sheets.client:
                # Try to create a test spreadsheet
                test_result = sheets.create_summary_sheet()

                if test_result:
                    messagebox.showinfo("Test Successful!",
                        "✅ Google Sheets connection is working perfectly!\n\n"
                        "Your SEO tool can now automatically upload indexation results to Google Sheets.")
                    self.main_app.log("✅ Google Sheets connection test successful!")
                else:
                    messagebox.showwarning("Test Warning",
                        "⚠️ Connection established but couldn't create test sheet.\n\n"
                        "Make sure you've shared a Google Sheet with your service account email.")
                    self.main_app.log("⚠️ Google Sheets connection partial - check sharing permissions")
            else:
                messagebox.showerror("Test Failed",
                    "❌ Could not connect to Google Sheets.\n\n"
                    "Please check your credentials file and try again.")
                self.main_app.log("❌ Google Sheets connection test failed")

        except ImportError:
            messagebox.showerror("Missing Dependencies",
                "Google Sheets integration modules not found.\n\n"
                "Please ensure all required files are in the src/ directory.")
        except Exception as e:
            messagebox.showerror("Test Error", f"Connection test failed: {e}")
            self.main_app.log(f"❌ Google Sheets test error: {e}")

    def close_dialog(self):
        """Close dialog"""
        self.dialog.destroy()

def main():
    """Main function"""
    # Change to script directory
    os.chdir(Path(__file__).parent)

    # Create results directory
    os.makedirs("results", exist_ok=True)

    # Create and run GUI
    root = tk.Tk()
    app = SimpleIndexationGUI(root)

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()

if __name__ == "__main__":
    main()