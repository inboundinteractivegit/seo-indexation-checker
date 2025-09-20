#!/usr/bin/env python3
"""
II Indexation Checker - GUI Application
Inbound Interactive's SEO Indexation Monitoring Tool
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

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from indexation_checker import check_website_indexation, save_results_to_csv
    from google_sheets_integration import GoogleSheetsIntegration
    from search_console_checker import SearchConsoleChecker
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required files are in the src/ directory")

class IIIndexationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("II Indexation Checker - Inbound Interactive")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')

        # Variables
        self.websites_config = None
        self.is_checking = False
        self.results = {}

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Setup the user interface"""
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)

        # Logo and Title
        title_label = tk.Label(
            title_frame,
            text="🚀 II Indexation Checker",
            font=('Arial', 20, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=15)

        subtitle_label = tk.Label(
            title_frame,
            text="Inbound Interactive's Professional SEO Indexation Monitoring Tool",
            font=('Arial', 10),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        subtitle_label.pack()

        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Left Panel - Configuration
        left_frame = tk.LabelFrame(main_frame, text="Configuration", font=('Arial', 11, 'bold'), bg='#f0f0f0')
        left_frame.pack(side='left', fill='y', padx=(0, 10))

        # Status Frame
        status_frame = tk.Frame(left_frame, bg='#f0f0f0')
        status_frame.pack(fill='x', pady=10)

        tk.Label(status_frame, text="Status:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w')
        self.status_label = tk.Label(status_frame, text="Ready", fg='green', bg='#f0f0f0')
        self.status_label.pack(anchor='w')

        # Config file selection
        config_frame = tk.Frame(left_frame, bg='#f0f0f0')
        config_frame.pack(fill='x', pady=10)

        tk.Label(config_frame, text="Configuration File:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w')

        config_select_frame = tk.Frame(config_frame, bg='#f0f0f0')
        config_select_frame.pack(fill='x', pady=5)

        self.config_path_var = tk.StringVar(value="config/websites.json")
        tk.Entry(config_select_frame, textvariable=self.config_path_var, width=25).pack(side='left', fill='x', expand=True)
        tk.Button(config_select_frame, text="Browse", command=self.browse_config).pack(side='right', padx=(5, 0))

        tk.Button(config_frame, text="Reload Config", command=self.load_config, bg='#3498db', fg='white').pack(pady=5)

        # Websites list
        tk.Label(left_frame, text="Websites:", font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w', pady=(10, 0))

        # Websites listbox with scrollbar
        websites_frame = tk.Frame(left_frame, bg='#f0f0f0')
        websites_frame.pack(fill='both', expand=True, pady=5)

        self.websites_listbox = tk.Listbox(websites_frame, selectmode='multiple', height=8)
        scrollbar = tk.Scrollbar(websites_frame, orient='vertical')
        self.websites_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.websites_listbox.yview)

        self.websites_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Buttons
        button_frame = tk.Frame(left_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=10)

        self.check_button = tk.Button(
            button_frame,
            text="🔍 Check Indexation",
            command=self.start_check,
            bg='#27ae60',
            fg='white',
            font=('Arial', 11, 'bold'),
            height=2
        )
        self.check_button.pack(fill='x', pady=2)

        self.sheets_button = tk.Button(
            button_frame,
            text="📊 Upload to Sheets",
            command=self.upload_to_sheets,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 11, 'bold'),
            height=2
        )
        self.sheets_button.pack(fill='x', pady=2)

        tk.Button(button_frame, text="📁 Open Results Folder", command=self.open_results_folder).pack(fill='x', pady=2)
        tk.Button(button_frame, text="⚙️ Setup Guide", command=self.open_setup_guide).pack(fill='x', pady=2)

        # Right Panel - Results
        right_frame = tk.LabelFrame(main_frame, text="Results & Log", font=('Arial', 11, 'bold'), bg='#f0f0f0')
        right_frame.pack(side='right', fill='both', expand=True)

        # Progress bar
        self.progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=5)

        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            right_frame,
            height=25,
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.results_text.pack(fill='both', expand=True, pady=5)

        # Summary frame
        summary_frame = tk.Frame(right_frame, bg='#f0f0f0')
        summary_frame.pack(fill='x', pady=5)

        self.summary_label = tk.Label(
            summary_frame,
            text="No checks completed yet",
            font=('Arial', 10, 'bold'),
            bg='#f0f0f0'
        )
        self.summary_label.pack()

        # Initial log message
        self.log("Welcome to II Indexation Checker!")
        self.log("By Inbound Interactive - Professional SEO Tools")
        self.log("-" * 50)

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
                self.log(f"Config file not found: {config_path}")
                self.log("Please check the file path or create a configuration file.")
                return

            with open(config_path, 'r') as file:
                self.websites_config = json.load(file)

            # Update websites listbox
            self.websites_listbox.delete(0, tk.END)
            for website in self.websites_config.get('websites', []):
                status = "✅" if website.get('enabled', True) else "❌"
                gsc_status = "🔗GSC" if website.get('gsc_available', False) else "🔍Search"
                display_text = f"{status} {website['name']} ({gsc_status})"
                self.websites_listbox.insert(tk.END, display_text)

            # Select all enabled websites by default
            for i, website in enumerate(self.websites_config.get('websites', [])):
                if website.get('enabled', True):
                    self.websites_listbox.selection_set(i)

            self.log(f"Loaded {len(self.websites_config.get('websites', []))} websites from config")
            self.status_label.config(text="Config Loaded", fg="green")

        except Exception as e:
            self.log(f"Error loading config: {e}")
            self.status_label.config(text="Config Error", fg="red")

    def log(self, message):
        """Add message to results log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.results_text.see(tk.END)
        self.root.update_idletasks()

    def start_check(self):
        """Start indexation check in background thread"""
        if self.is_checking:
            self.log("Check already in progress...")
            return

        if not self.websites_config:
            messagebox.showerror("Error", "Please load a configuration file first")
            return

        selected_indices = self.websites_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one website to check")
            return

        self.is_checking = True
        self.check_button.config(state='disabled', text="Checking...")
        self.progress.start()
        self.status_label.config(text="Checking...", fg="orange")

        # Start background thread
        thread = threading.Thread(target=self.run_check, args=(selected_indices,))
        thread.daemon = True
        thread.start()

    def run_check(self, selected_indices):
        """Run indexation check in background"""
        try:
            self.results = {}
            total_indexed = 0
            total_urls = 0

            for index in selected_indices:
                website = self.websites_config['websites'][index]

                if not website.get('enabled', True):
                    self.log(f"Skipping disabled website: {website['name']}")
                    continue

                self.log(f"Checking: {website['name']}")

                # Run the check
                results = check_website_indexation(website)

                if results:
                    # Save results
                    filename = save_results_to_csv(results, website['name'])
                    if filename:
                        self.results[website['name']] = {
                            'results': results,
                            'filename': filename,
                            'total': len(results),
                            'indexed': sum(1 for r in results if 'INDEXED' in r['status'])
                        }

                        total_urls += len(results)
                        total_indexed += sum(1 for r in results if 'INDEXED' in r['status'])

                        indexed_count = sum(1 for r in results if 'INDEXED' in r['status'])
                        rate = (indexed_count / len(results) * 100) if results else 0

                        self.log(f"✅ {website['name']}: {indexed_count}/{len(results)} ({rate:.1f}%) indexed")
                    else:
                        self.log(f"❌ Failed to save results for {website['name']}")
                else:
                    self.log(f"❌ No results for {website['name']}")

            # Update summary
            if total_urls > 0:
                overall_rate = (total_indexed / total_urls * 100)
                summary = f"Summary: {total_indexed}/{total_urls} URLs indexed ({overall_rate:.1f}%)"
                self.summary_label.config(text=summary)
                self.log("-" * 50)
                self.log(f"FINAL SUMMARY: {total_indexed}/{total_urls} URLs indexed ({overall_rate:.1f}%)")

        except Exception as e:
            self.log(f"Error during check: {e}")
        finally:
            # Re-enable UI
            self.root.after(0, self.check_complete)

    def check_complete(self):
        """Called when check is complete"""
        self.is_checking = False
        self.check_button.config(state='normal', text="🔍 Check Indexation")
        self.progress.stop()
        self.status_label.config(text="Check Complete", fg="green")
        self.log("Check completed!")

    def upload_to_sheets(self):
        """Upload results to Google Sheets"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to upload. Run a check first.")
            return

        try:
            self.log("Uploading to Google Sheets...")
            self.status_label.config(text="Uploading...", fg="orange")

            # Initialize sheets integration
            sheets = GoogleSheetsIntegration('config/google_credentials.json')

            if not sheets.client:
                self.log("❌ Google Sheets not configured. Check credentials file.")
                messagebox.showerror("Error", "Google Sheets integration not configured.\nCheck your credentials file.")
                return

            # Upload each result file
            uploaded = 0
            for website_name, data in self.results.items():
                filename = data['filename']
                if os.path.exists(filename):
                    success = sheets.upload_results(filename)
                    if success:
                        uploaded += 1
                        self.log(f"✅ Uploaded {website_name} to Google Sheets")
                    else:
                        self.log(f"❌ Failed to upload {website_name}")

            # Create summary
            if uploaded > 0:
                sheets.create_summary_sheet()
                self.log(f"✅ Uploaded {uploaded} websites to Google Sheets")
                self.status_label.config(text="Upload Complete", fg="green")
            else:
                self.log("❌ No files were uploaded")
                self.status_label.config(text="Upload Failed", fg="red")

        except Exception as e:
            self.log(f"❌ Upload error: {e}")
            self.status_label.config(text="Upload Error", fg="red")
            messagebox.showerror("Error", f"Upload failed: {e}")

    def open_results_folder(self):
        """Open results folder in file explorer"""
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Open folder based on OS
        import platform
        system = platform.system()

        if system == "Windows":
            os.startfile(results_dir)
        elif system == "Darwin":  # macOS
            os.system(f"open {results_dir}")
        else:  # Linux
            os.system(f"xdg-open {results_dir}")

    def open_setup_guide(self):
        """Open setup guide"""
        setup_file = "docs/SETUP.md"
        if os.path.exists(setup_file):
            webbrowser.open(f"file://{os.path.abspath(setup_file)}")
        else:
            webbrowser.open("https://github.com/inboundinteractivegit/seo-indexation-checker")

def main():
    """Main function"""
    # Change to script directory
    os.chdir(Path(__file__).parent)

    # Create results directory
    os.makedirs("results", exist_ok=True)

    # Create and run GUI
    root = tk.Tk()
    app = IIIndexationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()