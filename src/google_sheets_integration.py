#!/usr/bin/env python3
"""
Google Sheets Integration for Indexation Checker
Automatically uploads indexation results to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import csv
import json
from datetime import datetime
import os

class GoogleSheetsIntegration:
    def __init__(self, credentials_file=None):
        """
        Initialize Google Sheets integration

        Setup Instructions:
        1. Go to Google Cloud Console (console.cloud.google.com)
        2. Create a new project or select existing
        3. Enable Google Sheets API and Google Drive API
        4. Create Service Account credentials
        5. Download JSON key file
        6. Share your Google Sheet with the service account email
        """
        self.credentials_file = credentials_file or 'config/google_credentials.json'
        self.client = None
        self.setup_client()

    def setup_client(self):
        """Setup Google Sheets client with service account credentials"""
        try:
            if not os.path.exists(self.credentials_file):
                print(f"ERROR: Credentials file {self.credentials_file} not found.")
                print("\nSetup Instructions:")
                print("1. Go to Google Cloud Console (console.cloud.google.com)")
                print("2. Create a new project or select existing")
                print("3. Enable Google Sheets API and Google Drive API")
                print("4. Create Service Account credentials")
                print("5. Download JSON key file as 'google_credentials.json'")
                print("6. Share your Google Sheet with the service account email")
                return False

            # Define the scope
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Load credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )

            # Initialize the client
            self.client = gspread.authorize(credentials)
            print("[OK] Google Sheets client initialized successfully")
            return True

        except Exception as e:
            print(f"[ERROR] Error setting up Google Sheets client: {e}")
            return False

    def test_sheet_access(self, spreadsheet_id, worksheet_name=None):
        """Test access to a specific spreadsheet and worksheet"""
        try:
            if not self.client:
                print("[ERROR] Google Sheets client not initialized")
                return False

            # Try to open the spreadsheet by ID
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            print(f"[OK] Successfully accessed spreadsheet: {spreadsheet.title}")

            # If worksheet name is provided, test access to specific worksheet
            if worksheet_name:
                try:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                    print(f"[OK] Successfully accessed worksheet: {worksheet_name}")
                except gspread.WorksheetNotFound:
                    print(f"[WARN] Worksheet '{worksheet_name}' not found, but spreadsheet is accessible")
                    # This is still considered success - we can create the worksheet later
                    return True

            return True

        except gspread.SpreadsheetNotFound:
            print(f"[ERROR] Spreadsheet with ID '{spreadsheet_id}' not found or not accessible")
            return False
        except gspread.exceptions.APIError as e:
            print(f"[ERROR] Google Sheets API error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Error testing sheet access: {e}")
            return False

    def get_or_create_sheet(self, sheet_name, website_name):
        """Get existing sheet or create new one"""
        try:
            # Try to open existing sheet
            sheet = self.client.open(sheet_name)
            print(f"[SHEET] Opened existing sheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            # Create new sheet
            sheet = self.client.create(sheet_name)
            print(f"[SHEET] Created new sheet: {sheet_name}")

        # Get or create worksheet for this website
        try:
            worksheet = sheet.worksheet(website_name)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=website_name, rows=1000, cols=10)
            # Add headers
            worksheet.append_row(['URL', 'Status', 'Check_Date'])
            print(f"[NEW] Created new worksheet: {website_name}")

        return worksheet

    def normalize_website_name(self, filename):
        """Normalize website names to prevent duplicate tabs"""
        # Extract base name from filename
        base_name = filename.split('_indexation')[0].lower()

        # Mapping for consistent naming
        name_mapping = {
            'abercrombie': 'Abercrombie Jewelry',
            'abercrombie_jewelry': 'Abercrombie Jewelry',
            'austinfence': 'Austin Fence',
            'austin_fence': 'Austin Fence',
            'austin_fence_company': 'Austin Fence Company'
        }

        return name_mapping.get(base_name, base_name.replace('_', ' ').title())

    def upload_results(self, csv_file_path, sheet_name=None, website_name=None):
        """Upload CSV results to Google Sheets"""
        if not self.client:
            print("[ERROR] Google Sheets client not initialized")
            return False

        try:
            # Extract website name from filename if not provided
            if not website_name:
                filename = os.path.basename(csv_file_path)
                website_name = self.normalize_website_name(filename)

            # Use default sheet name if not provided
            if not sheet_name:
                sheet_name = "Website Indexation Results"

            # Get worksheet
            worksheet = self.get_or_create_sheet(sheet_name, website_name)

            # Read CSV data
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)

            if len(rows) <= 1:  # Only header or empty
                print(f"[WARN]  No data to upload from {csv_file_path}")
                return False

            # Skip header row when appending (it already exists in sheet)
            data_rows = rows[1:]

            # Get current timestamp for this batch
            batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if this is a single-date CSV (like from latest results)
            # or historical CSV (already has dates)
            if len(data_rows) > 0 and len(data_rows[0]) >= 3:
                # Has date column, upload as-is
                worksheet.append_rows(data_rows)
                print(f"[OK] Uploaded {len(data_rows)} rows to {website_name} worksheet")
            else:
                # Add timestamp to rows without dates
                timestamped_rows = []
                for row in data_rows:
                    if len(row) >= 2:
                        timestamped_rows.append([row[0], row[1], batch_timestamp])

                worksheet.append_rows(timestamped_rows)
                print(f"[OK] Uploaded {len(timestamped_rows)} rows with timestamp to {website_name} worksheet")

            return True

        except Exception as e:
            print(f"[ERROR] Error uploading to Google Sheets: {e}")
            return False

    def create_summary_sheet(self, sheet_name="Website Indexation Results"):
        """Create a summary sheet with overview data"""
        try:
            sheet = self.client.open(sheet_name)

            # Create or get summary worksheet
            try:
                summary_ws = sheet.worksheet("Summary")
            except gspread.WorksheetNotFound:
                summary_ws = sheet.add_worksheet(title="Summary", rows=100, cols=10)
                # Add headers
                summary_ws.append_row([
                    'Website', 'Total URLs', 'Indexed', 'Not Indexed',
                    'Indexation Rate', 'Last Updated'
                ])

            # Get all worksheets (except Summary)
            worksheets = [ws for ws in sheet.worksheets() if ws.title != "Summary"]

            summary_data = []
            for ws in worksheets:
                try:
                    # Get latest data for this website
                    all_values = ws.get_all_values()
                    if len(all_values) <= 1:  # Only header
                        continue

                    # Find most recent check date
                    latest_date = None
                    latest_data = []

                    for row in all_values[1:]:  # Skip header
                        if len(row) >= 3:
                            check_date = row[2]
                            if latest_date is None or check_date > latest_date:
                                if check_date != latest_date:
                                    latest_date = check_date
                                    latest_data = []
                                latest_data.append(row)
                            elif check_date == latest_date:
                                latest_data.append(row)

                    if latest_data:
                        total = len(latest_data)
                        indexed = sum(1 for row in latest_data if 'INDEXED' in row[1])
                        not_indexed = sum(1 for row in latest_data if 'NOT INDEXED' in row[1])
                        rate = f"{(indexed/total*100):.1f}%" if total > 0 else "0%"

                        summary_data.append([
                            ws.title, total, indexed, not_indexed, rate, latest_date
                        ])

                except Exception as e:
                    print(f"[WARN]  Error processing worksheet {ws.title}: {e}")

            if summary_data:
                # Clear existing summary data (keep headers)
                summary_ws.clear()
                summary_ws.append_row([
                    'Website', 'Total URLs', 'Indexed', 'Not Indexed',
                    'Indexation Rate', 'Last Updated'
                ])
                summary_ws.append_rows(summary_data)
                print(f"[OK] Updated summary sheet with {len(summary_data)} websites")

            return True

        except Exception as e:
            print(f"[ERROR] Error creating summary sheet: {e}")
            return False

def main():
    """Example usage"""
    # Initialize integration
    sheets = GoogleSheetsIntegration()

    if not sheets.client:
        print("Cannot proceed without Google Sheets access")
        return

    # Look for CSV files to upload
    csv_files = [f for f in os.listdir('.') if f.endswith('_indexation_results.csv')]

    if not csv_files:
        print("No indexation results CSV files found")
        return

    print(f"Found {len(csv_files)} CSV files to upload:")
    for file in csv_files:
        print(f"  - {file}")

    # Upload each file
    for csv_file in csv_files:
        print(f"\nUploading {csv_file}...")
        sheets.upload_results(csv_file)

    # Create summary
    print("\nCreating summary sheet...")
    sheets.create_summary_sheet()

    print("\n[OK] All done! Check your Google Sheets.")

if __name__ == "__main__":
    main()