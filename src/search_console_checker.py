#!/usr/bin/env python3
"""
Google Search Console Indexation Checker
Uses GSC API to check indexation status accurately
"""

import json
import csv
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

class SearchConsoleChecker:
    def __init__(self, credentials_file=None):
        """Initialize Search Console API client"""
        self.credentials_file = credentials_file or 'search_console_credentials.json'
        self.service = None
        self.setup_client()

    def setup_client(self):
        """Setup Google Search Console API client"""
        try:
            if not os.path.exists(self.credentials_file):
                print(f"[ERROR] Credentials file {self.credentials_file} not found.")
                print("Please make sure you downloaded the JSON file from Google Cloud")
                return False

            # Define the scope
            scopes = ['https://www.googleapis.com/auth/webmasters.readonly']

            # Load credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )

            # Build the service
            self.service = build('searchconsole', 'v1', credentials=credentials)
            print("[OK] Search Console API client initialized successfully")
            return True

        except Exception as e:
            print(f"[ERROR] Error setting up Search Console client: {e}")
            return False

    def get_properties(self):
        """Get list of properties (websites) available"""
        if not self.service:
            print("[ERROR] Search Console client not initialized")
            return []

        try:
            request = self.service.sites().list()
            response = request.execute()

            properties = []
            if 'siteEntry' in response:
                for site in response['siteEntry']:
                    properties.append({
                        'url': site['siteUrl'],
                        'permission': site['permissionLevel']
                    })

            return properties

        except Exception as e:
            print(f"[ERROR] Error getting properties: {e}")
            return []

    def check_indexation_status(self, site_url, urls_to_check, days_back=90):
        """
        Check indexation status for URLs using Search Console data

        Args:
            site_url: The property URL (e.g., 'https://example.com/')
            urls_to_check: List of URLs to check
            days_back: How many days back to check (default 90)
        """
        if not self.service:
            print("[ERROR] Search Console client not initialized")
            return []

        try:
            # Prepare date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            results = []

            print(f"[INFO] Checking {len(urls_to_check)} URLs against Search Console data...")
            print(f"[INFO] Date range: {start_date} to {end_date}")

            # Get Search Console data for the site
            request = self.service.searchanalytics().query(
                siteUrl=site_url,
                body={
                    'startDate': start_date.strftime('%Y-%m-%d'),
                    'endDate': end_date.strftime('%Y-%m-%d'),
                    'dimensions': ['page'],
                    'rowLimit': 25000  # Maximum allowed
                }
            )

            response = request.execute()

            # Extract indexed pages from Search Console
            indexed_pages = set()
            if 'rows' in response:
                for row in response['rows']:
                    indexed_pages.add(row['keys'][0])

            print(f"[INFO] Found {len(indexed_pages)} pages with Search Console data")

            # Check each URL
            for url in urls_to_check:
                # Clean URL for comparison
                clean_url = url.strip()

                # Check if URL appears in Search Console data
                if clean_url in indexed_pages:
                    status = "INDEXED"
                    method = "Search Console Data"
                else:
                    # Try with and without trailing slash
                    alt_url = clean_url.rstrip('/') if clean_url.endswith('/') else clean_url + '/'
                    if alt_url in indexed_pages:
                        status = "INDEXED"
                        method = "Search Console Data (alt URL)"
                    else:
                        status = "NOT IN SEARCH CONSOLE DATA"
                        method = "Search Console Data"

                results.append({
                    'url': clean_url,
                    'status': status,
                    'method': method,
                    'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            return results

        except Exception as e:
            print(f"[ERROR] Error checking indexation: {e}")
            return []

    def save_results_to_csv(self, results, filename):
        """Save results to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['URL', 'Status', 'Method', 'Check_Date'])

                for result in results:
                    writer.writerow([
                        result['url'],
                        result['status'],
                        result['method'],
                        result['check_date']
                    ])

            print(f"[OK] Results saved to {filename}")
            return True

        except Exception as e:
            print(f"[ERROR] Error saving results: {e}")
            return False

def main():
    """Test the Search Console checker"""
    # Initialize checker
    checker = SearchConsoleChecker()

    if not checker.service:
        print("Cannot proceed without Search Console access")
        return

    # Get available properties
    print("\n=== Available Properties ===")
    properties = checker.get_properties()

    if not properties:
        print("No properties found. Make sure you added the service account to your Search Console properties.")
        return

    for i, prop in enumerate(properties):
        print(f"{i+1}. {prop['url']} (Permission: {prop['permission']})")

    # For demo, let's use the first property
    if properties:
        site_url = properties[0]['url']
        print(f"\n[INFO] Testing with property: {site_url}")

        # Test with a few sample URLs (you can modify this)
        test_urls = [
            site_url,  # Homepage
            site_url + "about/",
            site_url + "contact/"
        ]

        print(f"[INFO] Testing with {len(test_urls)} sample URLs")

        # Check indexation
        results = checker.check_indexation_status(site_url, test_urls)

        if results:
            # Save results
            filename = f"search_console_test_results.csv"
            checker.save_results_to_csv(results, filename)

            # Show summary
            indexed = sum(1 for r in results if r['status'] == 'INDEXED')
            total = len(results)
            print(f"\n=== Summary ===")
            print(f"Total URLs checked: {total}")
            print(f"Indexed: {indexed}")
            print(f"Not in SC data: {total - indexed}")
            print(f"Results saved to: {filename}")

if __name__ == "__main__":
    main()