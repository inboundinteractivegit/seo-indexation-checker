#!/usr/bin/env python3
"""
II Indexation Checker - Beautiful GUI Application
Inbound Interactive's Professional SEO Indexation Monitoring Tool
Modern, beautiful interface with professional styling
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

class ModernStyle:
    """Modern UI styling constants"""
    # Color Palette - Professional Blue/Gray theme
    PRIMARY = "#1a365d"      # Dark blue
    SECONDARY = "#2c5282"    # Medium blue
    ACCENT = "#4299e1"       # Light blue
    SUCCESS = "#38a169"      # Green
    WARNING = "#ed8936"      # Orange
    DANGER = "#e53e3e"       # Red

    # Neutral colors
    WHITE = "#ffffff"
    LIGHT_GRAY = "#f7fafc"
    MEDIUM_GRAY = "#e2e8f0"
    DARK_GRAY = "#2d3748"
    TEXT_DARK = "#1a202c"
    TEXT_LIGHT = "#718096"

    # Fonts
    FONT_TITLE = ("Segoe UI", 24, "bold")
    FONT_SUBTITLE = ("Segoe UI", 11)
    FONT_HEADER = ("Segoe UI", 12, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_SMALL = ("Segoe UI", 9)
    FONT_MONO = ("Consolas", 9)

class IIIndexationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("II Indexation Checker - Inbound Interactive")
        self.root.geometry("1200x800")
        self.root.configure(bg=ModernStyle.LIGHT_GRAY)
        self.root.minsize(1000, 600)

        # Configure style
        self.setup_styles()

        # Variables
        self.websites_config = None
        self.is_checking = False
        self.results = {}

        self.setup_ui()
        self.load_config()

    def setup_styles(self):
        """Setup modern ttk styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure modern button styles
        self.style.configure(
            "Modern.TButton",
            background=ModernStyle.ACCENT,
            foreground=ModernStyle.WHITE,
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10)
        )

        self.style.map(
            "Modern.TButton",
            background=[('active', ModernStyle.SECONDARY)]
        )

        # Primary button style
        self.style.configure(
            "Primary.TButton",
            background=ModernStyle.PRIMARY,
            foreground=ModernStyle.WHITE,
            borderwidth=0,
            focuscolor="none",
            padding=(25, 12)
        )

        self.style.map(
            "Primary.TButton",
            background=[('active', ModernStyle.SECONDARY)]
        )

        # Success button style
        self.style.configure(
            "Success.TButton",
            background=ModernStyle.SUCCESS,
            foreground=ModernStyle.WHITE,
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10)
        )

        # Warning button style
        self.style.configure(
            "Warning.TButton",
            background=ModernStyle.WARNING,
            foreground=ModernStyle.WHITE,
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10)
        )

    def create_modern_frame(self, parent, bg=None, padding=20):
        """Create a modern styled frame with shadow effect"""
        if bg is None:
            bg = ModernStyle.WHITE

        frame = tk.Frame(parent, bg=bg, relief='flat', bd=0)

        # Add subtle border
        border_frame = tk.Frame(parent, bg=ModernStyle.MEDIUM_GRAY, height=1)
        border_frame.pack(fill='x')

        return frame

    def setup_ui(self):
        """Setup the modern user interface"""
        # Header Section
        self.create_header()

        # Main Content Area
        main_container = tk.Frame(self.root, bg=ModernStyle.LIGHT_GRAY)
        main_container.pack(fill='both', expand=True, padx=30, pady=20)

        # Create two-column layout
        self.create_left_panel(main_container)
        self.create_right_panel(main_container)

        # Footer
        self.create_footer()

    def create_header(self):
        """Create beautiful header section"""
        header_frame = tk.Frame(self.root, bg=ModernStyle.PRIMARY, height=120)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        # Header content
        header_content = tk.Frame(header_frame, bg=ModernStyle.PRIMARY)
        header_content.pack(expand=True, fill='both', padx=40, pady=20)

        # Logo and title section
        title_section = tk.Frame(header_content, bg=ModernStyle.PRIMARY)
        title_section.pack(side='left', fill='y')

        # Main title
        title_label = tk.Label(
            title_section,
            text="🚀 II Indexation Checker",
            font=ModernStyle.FONT_TITLE,
            fg=ModernStyle.WHITE,
            bg=ModernStyle.PRIMARY
        )
        title_label.pack(anchor='w')

        # Subtitle
        subtitle_label = tk.Label(
            title_section,
            text="Professional SEO Indexation Monitoring • Inbound Interactive",
            font=ModernStyle.FONT_SUBTITLE,
            fg=ModernStyle.MEDIUM_GRAY,
            bg=ModernStyle.PRIMARY
        )
        subtitle_label.pack(anchor='w', pady=(5, 0))

        # Status section (right side)
        status_section = tk.Frame(header_content, bg=ModernStyle.PRIMARY)
        status_section.pack(side='right', fill='y')

        # Status indicator
        self.status_frame = tk.Frame(status_section, bg=ModernStyle.SUCCESS, padx=15, pady=8)
        self.status_frame.pack(side='top', anchor='e')

        self.status_label = tk.Label(
            self.status_frame,
            text="● Ready",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.WHITE,
            bg=ModernStyle.SUCCESS
        )
        self.status_label.pack()

    def create_left_panel(self, parent):
        """Create modern left control panel"""
        left_container = tk.Frame(parent, bg=ModernStyle.LIGHT_GRAY)
        left_container.pack(side='left', fill='y', padx=(0, 20))

        # Configuration Card
        config_card = self.create_card(left_container, "⚙️ Configuration", width=350)

        # Config file section
        config_section = tk.Frame(config_card, bg=ModernStyle.WHITE)
        config_section.pack(fill='x', pady=15)

        tk.Label(
            config_section,
            text="Configuration File",
            font=ModernStyle.FONT_HEADER,
            fg=ModernStyle.TEXT_DARK,
            bg=ModernStyle.WHITE
        ).pack(anchor='w')

        # Config file input
        config_input_frame = tk.Frame(config_section, bg=ModernStyle.WHITE)
        config_input_frame.pack(fill='x', pady=(10, 0))

        self.config_path_var = tk.StringVar(value="config/websites.json")
        config_entry = tk.Entry(
            config_input_frame,
            textvariable=self.config_path_var,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.LIGHT_GRAY,
            relief='flat',
            bd=10
        )
        config_entry.pack(side='left', fill='x', expand=True, ipady=8)

        browse_btn = ttk.Button(
            config_input_frame,
            text="Browse",
            style="Modern.TButton",
            command=self.browse_config
        )
        browse_btn.pack(side='right', padx=(10, 0))

        reload_btn = ttk.Button(
            config_section,
            text="🔄 Reload Configuration",
            style="Modern.TButton",
            command=self.load_config
        )
        reload_btn.pack(pady=(15, 0))

        # Websites section
        websites_section = tk.Frame(config_card, bg=ModernStyle.WHITE)
        websites_section.pack(fill='both', expand=True, pady=(20, 15))

        tk.Label(
            websites_section,
            text="Select Websites to Check",
            font=ModernStyle.FONT_HEADER,
            fg=ModernStyle.TEXT_DARK,
            bg=ModernStyle.WHITE
        ).pack(anchor='w')

        # Websites listbox with modern styling
        websites_container = tk.Frame(websites_section, bg=ModernStyle.MEDIUM_GRAY, bd=1, relief='solid')
        websites_container.pack(fill='both', expand=True, pady=(10, 0))

        self.websites_listbox = tk.Listbox(
            websites_container,
            selectmode='multiple',
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.WHITE,
            fg=ModernStyle.TEXT_DARK,
            selectbackground=ModernStyle.ACCENT,
            selectforeground=ModernStyle.WHITE,
            relief='flat',
            bd=0,
            activestyle='none'
        )

        scrollbar_websites = ttk.Scrollbar(websites_container, orient='vertical', command=self.websites_listbox.yview)
        self.websites_listbox.config(yscrollcommand=scrollbar_websites.set)

        self.websites_listbox.pack(side='left', fill='both', expand=True, padx=2, pady=2)
        scrollbar_websites.pack(side='right', fill='y')

        # Action Buttons
        self.create_action_buttons(config_card)

    def create_action_buttons(self, parent):
        """Create modern action buttons"""
        button_section = tk.Frame(parent, bg=ModernStyle.WHITE)
        button_section.pack(fill='x', pady=(20, 15))

        # Primary action button
        self.check_button = ttk.Button(
            button_section,
            text="🔍 Check Indexation",
            style="Primary.TButton",
            command=self.start_check
        )
        self.check_button.pack(fill='x', pady=(0, 10))

        # Secondary buttons
        self.sheets_button = ttk.Button(
            button_section,
            text="📊 Upload to Google Sheets",
            style="Success.TButton",
            command=self.upload_to_sheets
        )
        self.sheets_button.pack(fill='x', pady=(0, 10))

        # Utility buttons frame
        utility_frame = tk.Frame(button_section, bg=ModernStyle.WHITE)
        utility_frame.pack(fill='x')

        results_btn = ttk.Button(
            utility_frame,
            text="📁 Results",
            style="Modern.TButton",
            command=self.open_results_folder
        )
        results_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))

        help_btn = ttk.Button(
            utility_frame,
            text="❓ Help",
            style="Modern.TButton",
            command=self.open_setup_guide
        )
        help_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))

    def create_right_panel(self, parent):
        """Create modern right results panel"""
        right_container = tk.Frame(parent, bg=ModernStyle.LIGHT_GRAY)
        right_container.pack(side='right', fill='both', expand=True)

        # Results Card
        results_card = self.create_card(right_container, "📊 Results & Activity Log")

        # Progress section
        progress_section = tk.Frame(results_card, bg=ModernStyle.WHITE)
        progress_section.pack(fill='x', pady=(15, 20))

        # Progress bar with modern styling
        self.progress = ttk.Progressbar(
            progress_section,
            mode='indeterminate',
            style="Modern.Horizontal.TProgressbar"
        )
        self.progress.pack(fill='x', pady=(0, 10))

        # Summary section
        self.summary_frame = tk.Frame(progress_section, bg=ModernStyle.LIGHT_GRAY, padx=20, pady=15)
        self.summary_frame.pack(fill='x')

        self.summary_label = tk.Label(
            self.summary_frame,
            text="No checks completed yet",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_LIGHT,
            bg=ModernStyle.LIGHT_GRAY
        )
        self.summary_label.pack()

        # Log section
        log_section = tk.Frame(results_card, bg=ModernStyle.WHITE)
        log_section.pack(fill='both', expand=True, pady=(0, 15))

        tk.Label(
            log_section,
            text="Activity Log",
            font=ModernStyle.FONT_HEADER,
            fg=ModernStyle.TEXT_DARK,
            bg=ModernStyle.WHITE
        ).pack(anchor='w', pady=(0, 10))

        # Modern log area
        log_container = tk.Frame(log_section, bg=ModernStyle.DARK_GRAY, bd=1, relief='solid')
        log_container.pack(fill='both', expand=True)

        self.results_text = scrolledtext.ScrolledText(
            log_container,
            font=ModernStyle.FONT_MONO,
            bg=ModernStyle.DARK_GRAY,
            fg=ModernStyle.LIGHT_GRAY,
            insertbackground=ModernStyle.ACCENT,
            relief='flat',
            bd=0,
            padx=15,
            pady=10
        )
        self.results_text.pack(fill='both', expand=True, padx=2, pady=2)

        # Configure text tags for colored output
        self.results_text.tag_configure("success", foreground=ModernStyle.SUCCESS)
        self.results_text.tag_configure("warning", foreground=ModernStyle.WARNING)
        self.results_text.tag_configure("error", foreground=ModernStyle.DANGER)
        self.results_text.tag_configure("info", foreground=ModernStyle.ACCENT)

    def create_card(self, parent, title, width=None):
        """Create a modern card-style container"""
        # Card container with shadow effect
        card_container = tk.Frame(parent, bg=ModernStyle.MEDIUM_GRAY)
        if width:
            card_container.pack(fill='y', pady=(0, 20), padx=2, ipadx=1, ipady=1)
            card_container.configure(width=width)
            card_container.pack_propagate(False)
        else:
            card_container.pack(fill='both', expand=True, pady=(0, 20), padx=2, ipadx=1, ipady=1)

        # Card content
        card = tk.Frame(card_container, bg=ModernStyle.WHITE)
        card.pack(fill='both', expand=True)

        # Card header
        header = tk.Frame(card, bg=ModernStyle.WHITE)
        header.pack(fill='x', padx=20, pady=(20, 0))

        tk.Label(
            header,
            text=title,
            font=ModernStyle.FONT_HEADER,
            fg=ModernStyle.TEXT_DARK,
            bg=ModernStyle.WHITE
        ).pack(anchor='w')

        return card

    def create_footer(self):
        """Create modern footer"""
        footer = tk.Frame(self.root, bg=ModernStyle.MEDIUM_GRAY, height=40)
        footer.pack(fill='x')
        footer.pack_propagate(False)

        footer_content = tk.Frame(footer, bg=ModernStyle.MEDIUM_GRAY)
        footer_content.pack(expand=True, fill='both', padx=30)

        tk.Label(
            footer_content,
            text="© 2025 Inbound Interactive • Professional SEO Tools",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_LIGHT,
            bg=ModernStyle.MEDIUM_GRAY
        ).pack(side='left', pady=12)

        tk.Label(
            footer_content,
            text="v2.0.0",
            font=ModernStyle.FONT_SMALL,
            fg=ModernStyle.TEXT_LIGHT,
            bg=ModernStyle.MEDIUM_GRAY
        ).pack(side='right', pady=12)

    def update_status(self, message, status_type="ready"):
        """Update status indicator with color coding"""
        colors = {
            "ready": ModernStyle.SUCCESS,
            "working": ModernStyle.WARNING,
            "error": ModernStyle.DANGER,
            "info": ModernStyle.ACCENT
        }

        self.status_frame.configure(bg=colors.get(status_type, ModernStyle.SUCCESS))
        self.status_label.configure(
            text=f"● {message}",
            bg=colors.get(status_type, ModernStyle.SUCCESS)
        )

    def log(self, message, log_type="info"):
        """Add message to results log with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding based on message content
        if "✅" in message or "success" in message.lower():
            tag = "success"
        elif "❌" in message or "error" in message.lower():
            tag = "error"
        elif "⚠️" in message or "warning" in message.lower():
            tag = "warning"
        else:
            tag = "info"

        self.results_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.results_text.see(tk.END)
        self.root.update_idletasks()

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
                self.log(f"❌ Config file not found: {config_path}")
                self.update_status("Config Error", "error")
                return

            with open(config_path, 'r') as file:
                self.websites_config = json.load(file)

            # Update websites listbox with beautiful formatting
            self.websites_listbox.delete(0, tk.END)
            for website in self.websites_config.get('websites', []):
                enabled_icon = "✅" if website.get('enabled', True) else "❌"
                gsc_icon = "🔗" if website.get('gsc_available', False) else "🔍"
                method = "GSC API" if website.get('gsc_available', False) else "Search Fallback"

                display_text = f"{enabled_icon} {website['name']}"
                subtext = f"    {gsc_icon} {method}"

                self.websites_listbox.insert(tk.END, display_text)
                if not website.get('enabled', True):
                    # Make disabled items gray
                    self.websites_listbox.itemconfig(tk.END, fg=ModernStyle.TEXT_LIGHT)

            # Select all enabled websites by default
            for i, website in enumerate(self.websites_config.get('websites', [])):
                if website.get('enabled', True):
                    self.websites_listbox.selection_set(i)

            self.log(f"✅ Loaded {len(self.websites_config.get('websites', []))} websites from configuration")
            self.update_status("Configuration Loaded", "ready")

        except Exception as e:
            self.log(f"❌ Error loading configuration: {e}")
            self.update_status("Config Error", "error")

    def start_check(self):
        """Start indexation check in background thread"""
        if self.is_checking:
            self.log("⚠️ Check already in progress...")
            return

        if not self.websites_config:
            messagebox.showerror("Configuration Error", "Please load a configuration file first")
            return

        selected_indices = self.websites_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Selection Required", "Please select at least one website to check")
            return

        self.is_checking = True
        self.check_button.configure(text="🔍 Checking...", state='disabled')
        self.progress.start()
        self.update_status("Checking Indexation", "working")

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
                    self.log(f"⚠️ Skipping disabled website: {website['name']}")
                    continue

                self.log(f"🔍 Checking indexation for: {website['name']}")

                # Run the check
                results = check_website_indexation(website)

                if results:
                    # Save results
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

                        self.log(f"✅ {website['name']}: {indexed_count}/{len(results)} URLs indexed ({rate:.1f}%)")
                    else:
                        self.log(f"❌ Failed to save results for {website['name']}")
                else:
                    self.log(f"❌ No results returned for {website['name']}")

            # Update summary with beautiful formatting
            if total_urls > 0:
                overall_rate = (total_indexed / total_urls * 100)
                summary_text = f"📊 Summary: {total_indexed:,}/{total_urls:,} URLs indexed ({overall_rate:.1f}%)"

                self.summary_label.configure(
                    text=summary_text,
                    font=ModernStyle.FONT_HEADER,
                    fg=ModernStyle.SUCCESS if overall_rate > 80 else ModernStyle.WARNING
                )
                self.log(f"🎉 Indexation check completed! {summary_text}")
            else:
                self.summary_label.configure(text="No results to summarize")

        except Exception as e:
            self.log(f"❌ Error during indexation check: {e}")
        finally:
            # Re-enable UI
            self.root.after(0, self.check_complete)

    def check_complete(self):
        """Called when check is complete"""
        self.is_checking = False
        self.check_button.configure(text="🔍 Check Indexation", state='normal')
        self.progress.stop()
        self.update_status("Check Complete", "ready")

    def upload_to_sheets(self):
        """Upload results to Google Sheets"""
        if not self.results:
            messagebox.showwarning("No Results", "No results to upload. Please run an indexation check first.")
            return

        try:
            self.log("📊 Uploading results to Google Sheets...")
            self.update_status("Uploading to Sheets", "working")

            # Initialize sheets integration
            sheets = GoogleSheetsIntegration('config/google_credentials.json')

            if not sheets.client:
                self.log("❌ Google Sheets integration not configured")
                messagebox.showerror("Configuration Error",
                    "Google Sheets integration not configured.\n\nPlease check your credentials file in config/google_credentials.json")
                self.update_status("Upload Failed", "error")
                return

            # Upload each result file
            uploaded = 0
            for website_name, data in self.results.items():
                filename = data['filename']
                if os.path.exists(filename):
                    success = sheets.upload_results(filename)
                    if success:
                        uploaded += 1
                        self.log(f"✅ Successfully uploaded {website_name} to Google Sheets")
                    else:
                        self.log(f"❌ Failed to upload {website_name}")

            # Create summary
            if uploaded > 0:
                sheets.create_summary_sheet()
                self.log(f"🎉 Successfully uploaded {uploaded} website(s) to Google Sheets!")
                self.update_status("Upload Complete", "ready")
                messagebox.showinfo("Upload Complete",
                    f"Successfully uploaded {uploaded} website(s) to Google Sheets!\n\nCheck your Google Sheets for the updated data.")
            else:
                self.log("❌ No files were uploaded to Google Sheets")
                self.update_status("Upload Failed", "error")

        except Exception as e:
            self.log(f"❌ Upload error: {e}")
            self.update_status("Upload Error", "error")
            messagebox.showerror("Upload Error", f"Failed to upload to Google Sheets:\n\n{e}")

    def open_results_folder(self):
        """Open results folder in file explorer"""
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Open folder based on OS
        import platform
        system = platform.system()

        try:
            if system == "Windows":
                os.startfile(results_dir)
            elif system == "Darwin":  # macOS
                os.system(f"open {results_dir}")
            else:  # Linux
                os.system(f"xdg-open {results_dir}")
            self.log(f"📁 Opened results folder: {os.path.abspath(results_dir)}")
        except Exception as e:
            self.log(f"❌ Failed to open results folder: {e}")

    def open_setup_guide(self):
        """Open setup guide"""
        setup_file = "docs/SETUP.md"
        if os.path.exists(setup_file):
            webbrowser.open(f"file://{os.path.abspath(setup_file)}")
            self.log("📖 Opened setup guide")
        else:
            webbrowser.open("https://github.com/inboundinteractivegit/seo-indexation-checker")
            self.log("🌐 Opened GitHub repository")

def main():
    """Main function"""
    # Change to script directory
    os.chdir(Path(__file__).parent)

    # Create results directory
    os.makedirs("results", exist_ok=True)

    # Create and run GUI
    root = tk.Tk()

    # Set window icon (if available)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass  # Icon file not found, continue without it

    app = IIIndexationGUI(root)

    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    # Welcome message
    app.log("🚀 Welcome to II Indexation Checker!")
    app.log("💼 Professional SEO tool by Inbound Interactive")
    app.log("📋 Load a configuration file and select websites to begin")
    app.log("─" * 60)

    root.mainloop()

if __name__ == "__main__":
    main()