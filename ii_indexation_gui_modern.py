#!/usr/bin/env python3
"""
II Indexation Checker - Modern PyQt6 GUI
VS Code-inspired design with dark theme and modern components
"""

import sys
import json
import os
import threading
import time
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit, QLabel,
    QPushButton, QProgressBar, QComboBox, QLineEdit, QCheckBox,
    QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QFileDialog, QSpinBox,
    QRadioButton, QButtonGroup, QStatusBar, QMenuBar, QMenu,
    QSystemTrayIcon, QStyle, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, QRect, pyqtSlot, QSettings
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QPainter,
    QLinearGradient, QBrush, QAction, QFontDatabase
)

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from indexation_checker import check_website_indexation, save_results_to_csv
    from google_sheets_integration import GoogleSheetsIntegration
    from search_console_checker import SearchConsoleChecker
    from scheduler import IndexationScheduler
    from indexed_api_checker import IndexedAPIChecker
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required files are in the src/ directory")


class CopyableErrorDialog(QDialog):
    """Custom error dialog with copy functionality"""

    def __init__(self, parent=None, title="Error", message="", details=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Main message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-weight: bold; color: #dc3545; margin-bottom: 10px;")
        layout.addWidget(message_label)

        # Details text area (copyable)
        self.details_text = QTextEdit()
        self.details_text.setPlainText(details)
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                selection-background-color: #264f78;
            }
        """)
        layout.addWidget(self.details_text)

        # Buttons
        button_layout = QHBoxLayout()

        copy_button = QPushButton("Copy Error")
        copy_button.clicked.connect(self.copy_error)
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        button_layout.addWidget(copy_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #525252;
            }
        """)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #cccccc;
            }
            QLabel {
                color: #cccccc;
            }
        """)

    def copy_error(self):
        """Copy error details to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.details_text.toPlainText())

        # Show brief confirmation
        copy_button = self.sender()
        original_text = copy_button.text()
        copy_button.setText("Copied!")
        QTimer.singleShot(1000, lambda: copy_button.setText(original_text))


class ModernStyleSheet:
    """VS Code-inspired dark theme stylesheet"""

    @staticmethod
    def get_main_style():
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #cccccc;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
        }

        QWidget {
            background-color: #1e1e1e;
            color: #cccccc;
            font-size: 13px;
        }

        /* Sidebar/Tree Widget */
        QTreeWidget {
            background-color: #252526;
            border: none;
            outline: none;
            color: #cccccc;
            font-size: 13px;
            alternate-background-color: #2d2d30;
        }

        QTreeWidget::item {
            padding: 8px;
            border-bottom: 1px solid #3e3e42;
        }

        QTreeWidget::item:selected {
            background-color: #094771;
            color: #ffffff;
        }

        QTreeWidget::item:hover {
            background-color: #2a2d2e;
        }

        /* Text Areas */
        QTextEdit {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            color: #cccccc;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            padding: 10px;
        }

        /* Buttons */
        QPushButton {
            background-color: #0e639c;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 4px;
            min-height: 20px;
        }

        QPushButton:hover {
            background-color: #1177bb;
        }

        QPushButton:pressed {
            background-color: #0d5a94;
        }

        QPushButton:disabled {
            background-color: #464647;
            color: #969696;
        }

        /* Stop Button */
        QPushButton[objectName="stopButton"] {
            background-color: #d73a49;
        }

        QPushButton[objectName="stopButton"]:hover {
            background-color: #e53e3e;
        }

        /* Success Button */
        QPushButton[objectName="successButton"] {
            background-color: #28a745;
        }

        QPushButton[objectName="successButton"]:hover {
            background-color: #34ce57;
        }

        /* Input Fields */
        QLineEdit {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            color: #cccccc;
            padding: 8px;
            border-radius: 4px;
            font-size: 13px;
        }

        QLineEdit:focus {
            border: 1px solid #0e639c;
        }

        /* ComboBox */
        QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            color: #cccccc;
            padding: 8px;
            border-radius: 4px;
            min-width: 120px;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #cccccc;
            margin-right: 5px;
        }

        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            selection-background-color: #094771;
            color: #cccccc;
        }

        /* Progress Bar */
        QProgressBar {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            text-align: center;
            color: #cccccc;
            font-weight: bold;
        }

        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0e639c, stop:1 #1177bb);
            border-radius: 3px;
        }

        /* Tables */
        QTableWidget {
            background-color: #1e1e1e;
            alternate-background-color: #252526;
            gridline-color: #3e3e42;
            color: #cccccc;
            border: 1px solid #3e3e42;
            font-size: 12px;
        }

        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #3e3e42;
        }

        QTableWidget::item:selected {
            background-color: #094771;
        }

        QHeaderView::section {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 10px;
            border: none;
            border-bottom: 1px solid #3e3e42;
            font-weight: bold;
        }

        /* Group Boxes */
        QGroupBox {
            color: #cccccc;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            margin-top: 1ex;
            font-weight: bold;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 20px;
            padding: 0 8px 0 8px;
            color: #569cd6;
        }

        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #1e1e1e;
        }

        QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 12px 20px;
            border: none;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #1e1e1e;
            color: #ffffff;
            border-bottom: 2px solid #0e639c;
        }

        QTabBar::tab:hover:!selected {
            background-color: #3e3e42;
        }

        /* Splitter */
        QSplitter::handle {
            background-color: #3e3e42;
            width: 2px;
            height: 2px;
        }

        QSplitter::handle:hover {
            background-color: #569cd6;
        }

        /* Status Bar */
        QStatusBar {
            background-color: #007acc;
            color: white;
            font-weight: bold;
            border: none;
        }

        /* Checkboxes and Radio Buttons */
        QCheckBox {
            color: #cccccc;
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            border-radius: 3px;
        }

        QCheckBox::indicator:checked {
            background-color: #0e639c;
            image: none;
        }

        QRadioButton {
            color: #cccccc;
            spacing: 8px;
        }

        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            border-radius: 8px;
        }

        QRadioButton::indicator:checked {
            background-color: #0e639c;
        }

        /* Scrollbars */
        QScrollBar:vertical {
            background-color: #2d2d30;
            width: 12px;
            border: none;
        }

        QScrollBar::handle:vertical {
            background-color: #464647;
            border-radius: 6px;
            min-height: 20px;
            margin: 0px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #555556;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar:horizontal {
            background-color: #2d2d30;
            height: 12px;
            border: none;
        }

        QScrollBar::handle:horizontal {
            background-color: #464647;
            border-radius: 6px;
            min-width: 20px;
            margin: 0px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #555556;
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        """


class CheckThread(QThread):
    """Worker thread for running indexation checks"""

    progress_update = pyqtSignal(str)  # Status message
    result_ready = pyqtSignal(dict)    # Results
    finished_signal = pyqtSignal()     # Finished
    error_occurred = pyqtSignal(str)   # Error message

    def __init__(self, websites_config, selected_websites):
        super().__init__()
        self.websites_config = websites_config
        self.selected_websites = selected_websites
        self.stop_event = threading.Event()

    def stop_check(self):
        """Stop the running check"""
        self.stop_event.set()

    def run(self):
        """Run the indexation check in background"""
        try:
            results = {}
            total_websites = len(self.selected_websites)

            for i, website_name in enumerate(self.selected_websites, 1):
                if self.stop_event.is_set():
                    self.progress_update.emit(f"Check stopped by user after {i-1}/{total_websites} websites")
                    break

                # Find website config
                website = None
                for w in self.websites_config.get('websites', []):
                    if w['name'] == website_name:
                        website = w
                        break

                if not website:
                    continue

                self.progress_update.emit(f"Checking {website['name']} ({i}/{total_websites})...")

                # Run the check
                check_results = check_website_indexation(website, stop_event=self.stop_event)

                if check_results:
                    # Save results
                    filename = save_results_to_csv(check_results, website['name'])
                    indexed_count = sum(1 for r in check_results if 'INDEXED' in r['status'])

                    results[website['name']] = {
                        'results': check_results,
                        'filename': filename,
                        'total': len(check_results),
                        'indexed': indexed_count,
                        'rate': (indexed_count / len(check_results) * 100) if check_results else 0
                    }

                    self.progress_update.emit(f"✓ {website['name']}: {indexed_count}/{len(check_results)} indexed ({results[website['name']]['rate']:.1f}%)")

            self.result_ready.emit(results)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished_signal.emit()


class ModernIndexationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.websites_config = None
        self.current_check_thread = None
        self.scheduler = IndexationScheduler()

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the modern UI"""
        self.setWindowTitle("II Indexation Checker - Modern Interface")
        self.setGeometry(100, 100, 1400, 900)

        # Apply modern stylesheet
        self.setStyleSheet(ModernStyleSheet.get_main_style())

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main splitter (horizontal)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QHBoxLayout()
        central_widget_layout.addWidget(main_splitter)
        central_widget_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(central_widget_layout)

        # Left panel - Website management and controls
        self.create_left_panel(main_splitter)

        # Right panel - Results and logs
        self.create_right_panel(main_splitter)

        # Set splitter proportions
        main_splitter.setSizes([400, 1000])

        # Create status bar
        self.create_status_bar()

        # Create menu bar
        self.create_menu_bar()

    def create_left_panel(self, parent_splitter):
        """Create the left control panel"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        # Header
        header_label = QLabel("🚀 II Indexation Checker")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #569cd6;
                padding: 15px;
                background-color: #252526;
                border-bottom: 2px solid #007acc;
            }
        """)
        left_layout.addWidget(header_label)

        # Websites section
        websites_group = QGroupBox("Websites")
        websites_layout = QVBoxLayout()

        # Website tree
        self.websites_tree = QTreeWidget()
        self.websites_tree.setHeaderLabels(["Website", "Method", "Status"])
        self.websites_tree.setRootIsDecorated(False)
        self.websites_tree.setAlternatingRowColors(True)
        websites_layout.addWidget(self.websites_tree)

        # Website controls
        website_controls = QHBoxLayout()

        add_btn = QPushButton("Add Website")
        add_btn.clicked.connect(self.add_website)
        website_controls.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_website)
        website_controls.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_website)
        website_controls.addWidget(delete_btn)

        websites_layout.addLayout(website_controls)
        websites_group.setLayout(websites_layout)
        left_layout.addWidget(websites_group)

        # Actions section
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        # Check button
        self.check_btn = QPushButton("🔍 Start Indexation Check")
        self.check_btn.setObjectName("successButton")
        self.check_btn.clicked.connect(self.start_check)
        actions_layout.addWidget(self.check_btn)

        # Stop button (initially hidden)
        self.stop_btn = QPushButton("⏹ Stop Check")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_check)
        self.stop_btn.hide()
        actions_layout.addWidget(self.stop_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        actions_layout.addWidget(self.progress_bar)

        # Upload to Sheets button
        upload_btn = QPushButton("📊 Upload to Google Sheets")
        upload_btn.clicked.connect(self.upload_to_sheets)
        actions_layout.addWidget(upload_btn)

        # Other action buttons
        schedule_btn = QPushButton("⏰ Schedule Checks")
        schedule_btn.clicked.connect(self.open_scheduler)
        actions_layout.addWidget(schedule_btn)

        sheets_setup_btn = QPushButton("📊 Setup Google Sheets")
        sheets_setup_btn.clicked.connect(self.setup_google_sheets)
        actions_layout.addWidget(sheets_setup_btn)

        actions_group.setLayout(actions_layout)
        left_layout.addWidget(actions_group)

        # Add stretch to push everything to top
        left_layout.addStretch()

        parent_splitter.addWidget(left_widget)

    def create_right_panel(self, parent_splitter):
        """Create the right results panel"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout()

        # Results summary
        self.results_summary = QLabel("No checks completed yet")
        self.results_summary.setStyleSheet("""
            QLabel {
                background-color: #252526;
                padding: 15px;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-size: 14px;
                color: #cccccc;
            }
        """)
        results_layout.addWidget(self.results_summary)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Website", "Total URLs", "Indexed", "Rate"])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)

        results_tab.setLayout(results_layout)
        self.tab_widget.addTab(results_tab, "Results")

        # Console tab
        console_tab = QWidget()
        console_layout = QVBoxLayout()

        # Console header
        console_header = QLabel("Live Console Output")
        console_header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #569cd6;
                padding: 10px;
            }
        """)
        console_layout.addWidget(console_header)

        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        console_layout.addWidget(self.console_output)

        console_tab.setLayout(console_layout)
        self.tab_widget.addTab(console_tab, "Console")

        right_layout.addWidget(self.tab_widget)
        parent_splitter.addWidget(right_widget)

    def create_status_bar(self):
        """Create the modern status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Add permanent widgets
        self.status_bar.addPermanentWidget(QLabel("II Indexation Checker v2.0"))

    def create_menu_bar(self):
        """Create modern menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        open_action = QAction('Open Config', self)
        open_action.triggered.connect(self.open_config)
        file_menu.addAction(open_action)

        save_action = QAction('Save Config', self)
        save_action.triggered.connect(self.save_config)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')

        diagnostics_action = QAction('Run Diagnostics', self)
        diagnostics_action.triggered.connect(self.run_diagnostics)
        tools_menu.addAction(diagnostics_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_config(self):
        """Load websites configuration"""
        config_path = "config/websites.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    self.websites_config = json.load(file)
                    self.refresh_websites_tree()
                    self.log_message("Configuration loaded successfully")
            else:
                self.websites_config = {"websites": []}
                self.log_message("No configuration file found, starting with empty config")
        except Exception as e:
            self.log_message(f"Error loading config: {e}")
            self.websites_config = {"websites": []}

    def refresh_websites_tree(self):
        """Refresh the websites tree widget"""
        self.websites_tree.clear()

        if not self.websites_config:
            return

        for website in self.websites_config.get('websites', []):
            item = QTreeWidgetItem()

            # Website name
            item.setText(0, website['name'])

            # Method
            method = website.get('checking_method', 'auto')
            if method == 'gsc':
                method_display = "Google Search Console"
            elif method == 'indexed_api':
                method_display = "IndexedAPI"
            elif method == 'google_search':
                method_display = "Google Search"
            else:
                if website.get('gsc_available'):
                    method_display = "Auto (GSC)"
                elif website.get('indexed_api_key'):
                    method_display = "Auto (IndexedAPI)"
                else:
                    method_display = "Auto (Google Search)"

            item.setText(1, method_display)

            # Status
            status = "✓ Enabled" if website.get('enabled', True) else "✗ Disabled"
            item.setText(2, status)

            # Color coding
            if website.get('enabled', True):
                item.setForeground(0, QColor("#cccccc"))
            else:
                item.setForeground(0, QColor("#969696"))

            self.websites_tree.addTopLevelItem(item)

    def log_message(self, message):
        """Add message to console output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.console_output.append(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_check(self):
        """Start indexation check"""
        # Get selected websites
        selected_items = self.websites_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one website to check")
            return

        selected_websites = [item.text(0) for item in selected_items]

        # Update UI for checking state
        self.check_btn.hide()
        self.stop_btn.show()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        self.status_label.setText("Running indexation check...")
        self.log_message(f"Starting check for {len(selected_websites)} websites")

        # Start worker thread
        self.current_check_thread = CheckThread(self.websites_config, selected_websites)
        self.current_check_thread.progress_update.connect(self.update_progress)
        self.current_check_thread.result_ready.connect(self.display_results)
        self.current_check_thread.finished_signal.connect(self.check_finished)
        self.current_check_thread.error_occurred.connect(self.handle_error)
        self.current_check_thread.start()

    def stop_check(self):
        """Stop the current check"""
        if self.current_check_thread:
            self.log_message("Stopping check... Please wait...")
            self.current_check_thread.stop_check()
            self.status_label.setText("Stopping check...")

    @pyqtSlot(str)
    def update_progress(self, message):
        """Update progress message"""
        self.log_message(message)

    @pyqtSlot(dict)
    def display_results(self, results):
        """Display check results"""
        # Store results for potential upload
        self.last_results = results

        self.results_table.setRowCount(len(results))

        total_urls = 0
        total_indexed = 0

        for row, (website_name, data) in enumerate(results.items()):
            self.results_table.setItem(row, 0, QTableWidgetItem(website_name))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(data['total'])))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(data['indexed'])))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{data['rate']:.1f}%"))

            total_urls += data['total']
            total_indexed += data['indexed']

        # Update summary
        overall_rate = (total_indexed / total_urls * 100) if total_urls > 0 else 0
        summary_text = f"Check completed: {total_indexed}/{total_urls} URLs indexed ({overall_rate:.1f}%) - Results ready for upload"
        self.results_summary.setText(summary_text)

        # Switch to results tab
        self.tab_widget.setCurrentIndex(0)

    @pyqtSlot()
    def check_finished(self):
        """Clean up after check completion"""
        self.stop_btn.hide()
        self.check_btn.show()
        self.progress_bar.setVisible(False)
        self.status_label.setText("Check completed")
        self.log_message("Indexation check completed")

    @pyqtSlot(str)
    def handle_error(self, error_message):
        """Handle errors from worker thread"""
        self.log_message(f"Error: {error_message}")
        # Show copyable error dialog
        error_dialog = CopyableErrorDialog(
            self, "Indexation Check Error",
            "An error occurred during the indexation check:",
            error_message
        )
        error_dialog.exec()

    def add_website(self):
        """Add new website"""
        dialog = WebsiteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            website_data = dialog.get_website_data()
            if not self.websites_config:
                self.websites_config = {"websites": []}
            self.websites_config['websites'].append(website_data)
            self.save_config()
            self.refresh_websites_tree()
            self.log_message(f"Added website: {website_data['name']}")

    def edit_website(self):
        """Edit selected website"""
        selected_items = self.websites_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a website to edit")
            return

        website_name = selected_items[0].text(0)

        # Find website in config
        website_data = None
        website_index = None
        for i, website in enumerate(self.websites_config.get('websites', [])):
            if website['name'] == website_name:
                website_data = website
                website_index = i
                break

        if website_data:
            dialog = WebsiteDialog(self, website_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_website_data()
                self.websites_config['websites'][website_index] = updated_data
                self.save_config()
                self.refresh_websites_tree()
                self.log_message(f"Updated website: {updated_data['name']}")

    def delete_website(self):
        """Delete selected website"""
        selected_items = self.websites_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a website to delete")
            return

        website_name = selected_items[0].text(0)

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{website_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from config
            self.websites_config['websites'] = [
                w for w in self.websites_config.get('websites', [])
                if w['name'] != website_name
            ]
            self.save_config()
            self.refresh_websites_tree()
            self.log_message(f"Deleted website: {website_name}")

    def upload_to_sheets(self):
        """Upload results to Google Sheets"""
        try:
            if not hasattr(self, 'last_results') or not self.last_results:
                QMessageBox.warning(self, "No Results", "Please run an indexation check first to generate results to upload.")
                return

            self.log_message("Starting Google Sheets upload...")

            # Import and use the existing Google Sheets integration
            from google_sheets_integration import GoogleSheetsIntegration

            sheets_integration = GoogleSheetsIntegration()

            # Prepare results data for upload
            all_results = []
            for website_name, data in self.last_results.items():
                for result in data['results']:
                    result['website'] = website_name
                    all_results.append(result)

            if all_results:
                success = sheets_integration.upload_results(all_results)
                if success:
                    self.log_message("✅ Results uploaded to Google Sheets successfully!")
                    QMessageBox.information(self, "Success", "Results uploaded to Google Sheets successfully!")
                else:
                    self.log_message("❌ Failed to upload to Google Sheets")
                    QMessageBox.warning(self, "Upload Failed", "Failed to upload to Google Sheets. Check console for details.")
            else:
                QMessageBox.warning(self, "No Data", "No results data available to upload.")

        except Exception as e:
            error_msg = f"Error uploading to Google Sheets: {str(e)}"
            self.log_message(error_msg)
            # Show copyable error dialog
            error_dialog = CopyableErrorDialog(
                self, "Upload Error",
                "Error occurred while uploading to Google Sheets:",
                str(e)
            )
            error_dialog.exec()

    def open_scheduler(self):
        """Open scheduler dialog"""
        dialog = SchedulerDialog(self)
        dialog.exec()

    def setup_google_sheets(self):
        """Setup Google Sheets integration"""
        dialog = GoogleSheetsSetupDialog(self)
        dialog.exec()

    def show_google_sheets_setup_dialog(self):
        """Show Google Sheets setup instructions"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Google Sheets Setup")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout()

        # Instructions
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setHtml("""
        <h3>Google Sheets Setup Instructions</h3>

        <h4>1. Google Cloud Project Setup:</h4>
        <ul>
            <li>Go to <a href="https://console.cloud.google.com">Google Cloud Console</a></li>
            <li>Create a new project or select existing project</li>
            <li>Enable Google Sheets API</li>
            <li>Create a Service Account</li>
            <li>Download the JSON credentials file</li>
        </ul>

        <h4>2. Credentials File:</h4>
        <ul>
            <li>Save the JSON file as: <code>config/google_sheets_credentials.json</code></li>
            <li>The file should contain: type, project_id, private_key, client_email, etc.</li>
        </ul>

        <h4>3. Google Sheets Permission:</h4>
        <ul>
            <li>Create a Google Sheet for your results</li>
            <li>Share the sheet with your service account email</li>
            <li>Give "Editor" permissions</li>
        </ul>

        <h4>4. Configuration:</h4>
        <ul>
            <li>Update the spreadsheet ID in the integration settings</li>
            <li>Test the connection using the upload feature</li>
        </ul>

        <p><strong>Note:</strong> For detailed setup, please refer to the original Tkinter GUI which has a full setup wizard.</p>
        """)

        layout.addWidget(instructions)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec()

    def open_config(self):
        """Open configuration file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Configuration", "", "JSON files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.websites_config = json.load(file)
                    self.refresh_websites_tree()
                    self.log_message(f"Loaded configuration from: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration:\n{e}")

    def save_config(self):
        """Save configuration file"""
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/websites.json", 'w') as file:
                json.dump(self.websites_config, file, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")

    def run_diagnostics(self):
        """Run system diagnostics"""
        self.log_message("Running system diagnostics...")
        # Add diagnostic code here

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About II Indexation Checker",
            "II Indexation Checker v2.0\n"
            "Modern PyQt6 Interface\n\n"
            "Features:\n"
            "• Google Search Console integration\n"
            "• IndexedAPI support\n"
            "• Google Search fallback\n"
            "• Advanced scheduling\n"
            "• Google Sheets integration\n\n"
            "© 2025 Inbound Interactive"
        )


class WebsiteDialog(QDialog):
    """Modern dialog for adding/editing websites"""

    def __init__(self, parent=None, website_data=None):
        super().__init__(parent)
        self.website_data = website_data
        self.init_ui()

        if website_data:
            self.populate_form()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Add/Edit Website")
        self.setModal(True)
        self.resize(500, 400)

        # Apply parent's stylesheet
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())

        layout = QVBoxLayout()

        # Form
        form_layout = QFormLayout()

        # Website name
        self.name_edit = QLineEdit()
        form_layout.addRow("Website Name:", self.name_edit)

        # Description
        self.description_edit = QLineEdit()
        form_layout.addRow("Description:", self.description_edit)

        # Sitemap URLs
        self.sitemap_edit = QTextEdit()
        self.sitemap_edit.setMaximumHeight(100)
        form_layout.addRow("Sitemap URLs\n(one per line):", self.sitemap_edit)

        # Max URLs
        self.max_urls_spin = QSpinBox()
        self.max_urls_spin.setRange(1, 10000)
        self.max_urls_spin.setValue(100)
        form_layout.addRow("Max URLs:", self.max_urls_spin)

        # Enabled checkbox
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        form_layout.addRow("", self.enabled_check)

        # GSC available
        self.gsc_check = QCheckBox("Google Search Console Available")
        form_layout.addRow("", self.gsc_check)

        # IndexedAPI key
        self.indexed_api_edit = QLineEdit()
        self.indexed_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("IndexedAPI Key:", self.indexed_api_edit)

        # Checking method
        method_group = QGroupBox("Checking Method")
        method_layout = QVBoxLayout()

        self.method_group = QButtonGroup()

        self.auto_radio = QRadioButton("Auto (Best Available)")
        self.auto_radio.setChecked(True)
        self.method_group.addButton(self.auto_radio, 0)
        method_layout.addWidget(self.auto_radio)

        self.gsc_radio = QRadioButton("Google Search Console")
        self.method_group.addButton(self.gsc_radio, 1)
        method_layout.addWidget(self.gsc_radio)

        self.indexed_api_radio = QRadioButton("IndexedAPI")
        self.method_group.addButton(self.indexed_api_radio, 2)
        method_layout.addWidget(self.indexed_api_radio)

        self.google_search_radio = QRadioButton("Google Search")
        self.method_group.addButton(self.google_search_radio, 3)
        method_layout.addWidget(self.google_search_radio)

        method_group.setLayout(method_layout)

        layout.addLayout(form_layout)
        layout.addWidget(method_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def populate_form(self):
        """Populate form with existing website data"""
        if not self.website_data:
            return

        self.name_edit.setText(self.website_data.get('name', ''))
        self.description_edit.setText(self.website_data.get('description', ''))

        # Sitemap URLs
        if 'sitemap_url' in self.website_data:
            self.sitemap_edit.setPlainText(self.website_data['sitemap_url'])
        elif 'sitemap_urls' in self.website_data:
            self.sitemap_edit.setPlainText('\n'.join(self.website_data['sitemap_urls']))

        self.max_urls_spin.setValue(self.website_data.get('max_urls', 100))
        self.enabled_check.setChecked(self.website_data.get('enabled', True))
        self.gsc_check.setChecked(self.website_data.get('gsc_available', False))
        self.indexed_api_edit.setText(self.website_data.get('indexed_api_key', ''))

        # Checking method
        method = self.website_data.get('checking_method', 'auto')
        if method == 'gsc':
            self.gsc_radio.setChecked(True)
        elif method == 'indexed_api':
            self.indexed_api_radio.setChecked(True)
        elif method == 'google_search':
            self.google_search_radio.setChecked(True)
        else:
            self.auto_radio.setChecked(True)

    def get_website_data(self):
        """Get website data from form"""
        sitemap_text = self.sitemap_edit.toPlainText().strip()
        sitemap_lines = [line.strip() for line in sitemap_text.split('\n') if line.strip()]

        data = {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'max_urls': self.max_urls_spin.value(),
            'enabled': self.enabled_check.isChecked(),
            'gsc_available': self.gsc_check.isChecked()
        }

        # Sitemap URLs
        if len(sitemap_lines) == 1:
            data['sitemap_url'] = sitemap_lines[0]
        elif len(sitemap_lines) > 1:
            data['sitemap_urls'] = sitemap_lines

        # IndexedAPI key
        if self.indexed_api_edit.text().strip():
            data['indexed_api_key'] = self.indexed_api_edit.text().strip()

        # Checking method
        checked_id = self.method_group.checkedId()
        if checked_id == 1:
            data['checking_method'] = 'gsc'
        elif checked_id == 2:
            data['checking_method'] = 'indexed_api'
        elif checked_id == 3:
            data['checking_method'] = 'google_search'
        else:
            data['checking_method'] = 'auto'

        return data


class GoogleSheetsSetupDialog(QDialog):
    """Complete Google Sheets setup wizard for PyQt6"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()
        self.check_current_setup()

    def init_ui(self):
        """Initialize the Google Sheets setup UI"""
        self.setWindowTitle("Google Sheets Integration Setup")
        self.setModal(True)
        self.resize(700, 800)

        # Apply parent's stylesheet
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())

        layout = QVBoxLayout()

        # Header
        header_label = QLabel("📊 Google Sheets Integration Setup")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #569cd6;
                padding: 15px;
                background-color: #252526;
                border-bottom: 2px solid #007acc;
            }
        """)
        layout.addWidget(header_label)

        # Status section
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Checking Google Sheets configuration...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Credentials section
        creds_group = QGroupBox("1. Google Cloud Credentials")
        creds_layout = QVBoxLayout()

        # Instructions
        instructions = QLabel("""
        <b>Step 1:</b> Create Google Cloud Project and Service Account<br>
        • Go to <a href="https://console.cloud.google.com">Google Cloud Console</a><br>
        • Create new project or select existing<br>
        • Enable Google Sheets API<br>
        • Create Service Account<br>
        • Download JSON credentials file
        """)
        instructions.setTextFormat(Qt.TextFormat.RichText)
        instructions.setOpenExternalLinks(True)
        instructions.setWordWrap(True)
        creds_layout.addWidget(instructions)

        # File upload section
        file_layout = QHBoxLayout()
        self.creds_file_label = QLabel("No credentials file selected")
        file_layout.addWidget(self.creds_file_label)

        browse_btn = QPushButton("Browse for Credentials File")
        browse_btn.clicked.connect(self.browse_credentials_file)
        file_layout.addWidget(browse_btn)

        creds_layout.addLayout(file_layout)

        # Test connection button
        self.test_creds_btn = QPushButton("Test Credentials")
        self.test_creds_btn.clicked.connect(self.test_credentials)
        self.test_creds_btn.setEnabled(False)
        creds_layout.addWidget(self.test_creds_btn)

        creds_group.setLayout(creds_layout)
        layout.addWidget(creds_group)

        # Spreadsheet setup section
        sheet_group = QGroupBox("2. Google Sheets Configuration")
        sheet_layout = QFormLayout()

        # Spreadsheet ID
        self.spreadsheet_id_edit = QLineEdit()
        self.spreadsheet_id_edit.setPlaceholderText("Enter your Google Sheets ID (from the URL)")
        sheet_layout.addRow("Spreadsheet ID:", self.spreadsheet_id_edit)

        # Worksheet name
        self.worksheet_name_edit = QLineEdit()
        self.worksheet_name_edit.setText("Indexation Results")
        sheet_layout.addRow("Worksheet Name:", self.worksheet_name_edit)

        # Instructions for getting spreadsheet ID
        sheet_instructions = QLabel("""
        <b>How to get Spreadsheet ID:</b><br>
        1. Create a new Google Sheet<br>
        2. Share it with your service account email (give Editor access)<br>
        3. Copy the ID from the URL: https://docs.google.com/spreadsheets/d/<b>SPREADSHEET_ID</b>/edit
        """)
        sheet_instructions.setTextFormat(Qt.TextFormat.RichText)
        sheet_instructions.setWordWrap(True)
        sheet_layout.addRow("", sheet_instructions)

        # Test sheet connection
        self.test_sheet_btn = QPushButton("Test Sheet Connection")
        self.test_sheet_btn.clicked.connect(self.test_sheet_connection)
        self.test_sheet_btn.setEnabled(False)
        sheet_layout.addRow("", self.test_sheet_btn)

        sheet_group.setLayout(sheet_layout)
        layout.addWidget(sheet_group)

        # Configuration summary
        summary_group = QGroupBox("3. Configuration Summary")
        summary_layout = QVBoxLayout()

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save Configuration")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self.save_configuration)
        button_layout.addWidget(save_btn)

        test_upload_btn = QPushButton("Test Upload")
        test_upload_btn.clicked.connect(self.test_upload)
        button_layout.addWidget(test_upload_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def check_current_setup(self):
        """Check current Google Sheets configuration"""
        try:
            # Check for credentials file
            creds_path = "config/google_sheets_credentials.json"
            if os.path.exists(creds_path):
                self.status_label.setText("✅ Google Sheets credentials file found")
                self.status_label.setStyleSheet("color: #28a745;")
                self.creds_file_label.setText(f"✅ {creds_path}")
                self.test_creds_btn.setEnabled(True)

                # Load existing configuration if available
                try:
                    # Check if there's a sheets config
                    config_path = "config/sheets_config.json"
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            config = json.load(f)

                        self.spreadsheet_id_edit.setText(config.get('spreadsheet_id', ''))
                        self.worksheet_name_edit.setText(config.get('worksheet_name', 'Indexation Results'))
                        self.test_sheet_btn.setEnabled(True)

                except Exception as e:
                    pass

            else:
                self.status_label.setText("❌ Google Sheets credentials not configured")
                self.status_label.setStyleSheet("color: #dc3545;")

        except Exception as e:
            self.status_label.setText(f"❌ Error checking configuration: {e}")
            self.status_label.setStyleSheet("color: #dc3545;")

    def browse_credentials_file(self):
        """Browse for credentials file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Google Cloud Credentials File", "", "JSON files (*.json)"
        )

        if file_path:
            try:
                # Validate the credentials file
                with open(file_path, 'r') as f:
                    creds = json.load(f)

                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in creds]

                if missing_fields:
                    QMessageBox.warning(
                        self, "Invalid Credentials",
                        f"Credentials file is missing required fields: {', '.join(missing_fields)}"
                    )
                    return

                # Copy to config directory
                os.makedirs("config", exist_ok=True)
                dest_path = "config/google_credentials.json"

                with open(dest_path, 'w') as f:
                    json.dump(creds, f, indent=2)

                self.creds_file_label.setText(f"✅ {dest_path}")
                self.test_creds_btn.setEnabled(True)

                QMessageBox.information(
                    self, "Success",
                    f"Credentials file saved to {dest_path}"
                )

            except json.JSONDecodeError:
                QMessageBox.warning(self, "Invalid File", "Selected file is not valid JSON")
            except Exception as e:
                # Show copyable error dialog
                error_dialog = CopyableErrorDialog(
                    self, "File Processing Error",
                    "Error occurred while processing credentials file:",
                    str(e)
                )
                error_dialog.exec()

    def test_credentials(self):
        """Test Google Sheets credentials"""
        try:
            from google_sheets_integration import GoogleSheetsIntegration

            # Explicitly specify the credentials file path
            creds_path = "config/google_credentials.json"
            sheets = GoogleSheetsIntegration(credentials_file=creds_path)
            if sheets.setup_client():
                QMessageBox.information(
                    self, "Success",
                    "✅ Google Sheets credentials are valid and working!"
                )
                self.test_sheet_btn.setEnabled(True)
            else:
                QMessageBox.warning(
                    self, "Failed",
                    "❌ Could not connect with current credentials"
                )

        except Exception as e:
            # Show copyable error dialog
            error_dialog = CopyableErrorDialog(
                self, "Credentials Test Error",
                "Error occurred while testing Google Sheets credentials:",
                str(e)
            )
            error_dialog.exec()

    def test_sheet_connection(self):
        """Test connection to specific spreadsheet"""
        spreadsheet_id = self.spreadsheet_id_edit.text().strip()
        worksheet_name = self.worksheet_name_edit.text().strip()

        if not spreadsheet_id:
            QMessageBox.warning(self, "Missing Information", "Please enter a Spreadsheet ID")
            return

        try:
            from google_sheets_integration import GoogleSheetsIntegration

            # Explicitly specify the credentials file path
            creds_path = "config/google_credentials.json"
            sheets = GoogleSheetsIntegration(credentials_file=creds_path)

            # Test connection to specific sheet
            if sheets.test_sheet_access(spreadsheet_id, worksheet_name):
                QMessageBox.information(
                    self, "Success",
                    f"✅ Successfully connected to spreadsheet!\nWorksheet: {worksheet_name}"
                )
                self.update_summary()
            else:
                QMessageBox.warning(
                    self, "Connection Failed",
                    "❌ Could not access the spreadsheet. Please check:\n"
                    "• Spreadsheet ID is correct\n"
                    "• Sheet is shared with your service account email\n"
                    "• Service account has Editor permissions"
                )

        except Exception as e:
            # Show copyable error dialog
            error_dialog = CopyableErrorDialog(
                self, "Sheet Connection Error",
                "Error occurred while testing sheet connection:",
                str(e)
            )
            error_dialog.exec()

    def save_configuration(self):
        """Save the Google Sheets configuration"""
        spreadsheet_id = self.spreadsheet_id_edit.text().strip()
        worksheet_name = self.worksheet_name_edit.text().strip()

        if not spreadsheet_id:
            QMessageBox.warning(self, "Missing Information", "Please enter a Spreadsheet ID")
            return

        try:
            config = {
                'spreadsheet_id': spreadsheet_id,
                'worksheet_name': worksheet_name,
                'configured_date': datetime.now().isoformat()
            }

            os.makedirs("config", exist_ok=True)
            with open("config/sheets_config.json", 'w') as f:
                json.dump(config, f, indent=2)

            QMessageBox.information(
                self, "Success",
                "✅ Google Sheets configuration saved successfully!"
            )

            self.update_summary()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving configuration: {e}")

    def test_upload(self):
        """Test uploading sample data to Google Sheets"""
        try:
            from google_sheets_integration import GoogleSheetsIntegration

            # Create sample test data
            test_data = [{
                'url': 'https://example.com/test',
                'status': 'INDEXED',
                'method': 'Test Method',
                'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'website': 'Test Upload'
            }]

            # Explicitly specify the credentials file path
            creds_path = "config/google_credentials.json"
            sheets = GoogleSheetsIntegration(credentials_file=creds_path)

            if sheets.upload_results(test_data):
                QMessageBox.information(
                    self, "Success",
                    "✅ Test upload successful!\nCheck your Google Sheet for the test data."
                )
            else:
                QMessageBox.warning(
                    self, "Upload Failed",
                    "❌ Test upload failed. Please check your configuration and try again."
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during test upload: {e}")

    def update_summary(self):
        """Update the configuration summary"""
        summary_parts = []

        # Credentials status
        if os.path.exists("config/google_sheets_credentials.json"):
            summary_parts.append("✅ Credentials: Configured")
        else:
            summary_parts.append("❌ Credentials: Not configured")

        # Sheet configuration
        spreadsheet_id = self.spreadsheet_id_edit.text().strip()
        worksheet_name = self.worksheet_name_edit.text().strip()

        if spreadsheet_id:
            summary_parts.append(f"✅ Spreadsheet ID: {spreadsheet_id}")
            summary_parts.append(f"✅ Worksheet: {worksheet_name}")
        else:
            summary_parts.append("❌ Spreadsheet: Not configured")

        # Configuration file
        if os.path.exists("config/sheets_config.json"):
            summary_parts.append("✅ Configuration: Saved")
        else:
            summary_parts.append("❌ Configuration: Not saved")

        self.summary_text.setPlainText("\n".join(summary_parts))


class SchedulerDialog(QDialog):
    """Modern scheduler dialog for PyQt6"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        """Initialize the scheduler UI"""
        self.setWindowTitle("Indexation Check Scheduler")
        self.setModal(True)
        self.resize(600, 500)

        # Apply parent's stylesheet
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())

        layout = QVBoxLayout()

        # Header
        header_label = QLabel("⏰ Schedule Automatic Indexation Checks")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #569cd6;
                padding: 15px;
                background-color: #252526;
                border-bottom: 2px solid #007acc;
            }
        """)
        layout.addWidget(header_label)

        # Scheduler implementation - simplified for now
        info_label = QLabel("""
        <h3>Advanced Scheduling Available</h3>
        <p>The full scheduling functionality with multiple options (hourly, daily, weekly, monthly)
        is currently available in the original Tkinter interface.</p>

        <p><strong>To access advanced scheduling:</strong></p>
        <ul>
            <li>Use the launcher: <code>launch_ii_indexation.bat</code></li>
            <li>Click the "⏰ Schedule" button in the original interface</li>
            <li>Configure your preferred schedule and automation settings</li>
        </ul>

        <p><strong>Available Schedule Types:</strong></p>
        <ul>
            <li>Every X hours (custom interval)</li>
            <li>Daily at specific time</li>
            <li>Weekly on chosen day</li>
            <li>Bi-weekly (every 2 weeks)</li>
            <li>Monthly on specific day</li>
        </ul>

        <p>The modern PyQt6 interface will have full scheduling in a future update.</p>
        """)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()

        open_original_btn = QPushButton("Open Original Scheduler")
        open_original_btn.setObjectName("successButton")
        open_original_btn.clicked.connect(self.open_original_scheduler)
        button_layout.addWidget(open_original_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def open_original_scheduler(self):
        """Launch the original Tkinter GUI for scheduling"""
        try:
            import subprocess
            subprocess.Popen(["launch_ii_indexation.bat"], shell=True)
            QMessageBox.information(
                self, "Launcher Started",
                "The original interface has been launched.\nUse the ⏰ Schedule button for advanced scheduling options."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not launch original interface: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("II Indexation Checker")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Inbound Interactive")

    # Create and show main window
    window = ModernIndexationGUI()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()