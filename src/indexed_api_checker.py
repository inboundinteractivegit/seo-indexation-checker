#!/usr/bin/env python3
"""
IsIndexed.com Integration
Third-party API for bulk URL indexation checking
"""

import requests
import json
import time
from datetime import datetime

class IndexedAPIChecker:
    def __init__(self, api_key=None):
        """Initialize IsIndexed.com API checker"""
        self.api_key = api_key
        self.base_url = "https://tool.isindexed.com/api"
        self.headers = {
            'User-Agent': 'II-Indexation-Checker/1.0',
            'Content-Type': 'application/json'
        }
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'

    def check_api_status(self):
        """Check if API is available"""
        if not self.api_key:
            return False, "No API key provided"

        # For now, return a placeholder since we don't have the exact API endpoint
        # GSC is working as primary method, so this is fallback only
        try:
            # Test basic connectivity to isindexed.com
            response = requests.get(
                "https://www.isindexed.com/en/",
                headers={'User-Agent': 'II-Indexation-Checker/1.0'},
                timeout=10
            )

            if response.status_code == 200:
                return True, "IsIndexed.com service available (API endpoints need configuration)"
            else:
                return False, f"Service unavailable: {response.status_code}"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def check_indexation_status(self, urls, stop_event=None):
        """
        Check indexation status for multiple URLs

        Args:
            urls: List of URLs to check
            stop_event: Threading event to signal when to stop checking

        Returns:
            List of results with status information
        """
        if not self.api_key:
            print("[ERROR] IsIndexed API: No API key configured")
            return []

        if not urls:
            return []

        # For now, return empty results since API endpoints need to be configured
        # GSC is working as primary method, so this fallback isn't critical
        print(f"[INFO] IsIndexed API: Service available but API endpoints need configuration")
        print(f"[INFO] Contact IsIndexed.com for API access details")
        print(f"[INFO] Using Google Search fallback instead")

        return []  # Return empty to trigger Google Search fallback

    def _check_single_url(self, url):
        """Check a single URL (fallback method)"""
        try:
            payload = {'url': url}

            response = requests.post(
                f"{self.base_url}/check-single",
                headers=self.headers,
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                indexed = data.get('indexed', False)

                return {
                    'url': url,
                    'status': "INDEXED" if indexed else "NOT INDEXED",
                    'method': "IndexedAPI (single)",
                    'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'details': data.get('details', '')
                }
            else:
                return {
                    'url': url,
                    'status': f"ERROR: HTTP {response.status_code}",
                    'method': "IndexedAPI (single)",
                    'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'details': 'API request failed'
                }

        except Exception as e:
            return {
                'url': url,
                'status': f"ERROR: {str(e)}",
                'method': "IndexedAPI (single)",
                'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'details': 'Request exception'
            }

    def get_credits_remaining(self):
        """Get remaining API credits"""
        if not self.api_key:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/credits",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('credits', 0)
            else:
                return None

        except Exception:
            return None

# Test function
def test_indexed_api():
    """Test IndexedAPI functionality"""
    print("Testing IndexedAPI...")

    # This would need a real API key to test
    api_key = "your-api-key-here"
    checker = IndexedAPIChecker(api_key)

    # Test URLs
    test_urls = [
        "https://example.com",
        "https://example.com/page1",
        "https://example.com/page2"
    ]

    # Check status
    is_valid, message = checker.check_api_status()
    print(f"API Status: {message}")

    if is_valid:
        results = checker.check_indexation_status(test_urls)
        print(f"Results: {len(results)} URLs checked")
        for result in results:
            print(f"  {result['url']}: {result['status']}")

if __name__ == "__main__":
    test_indexed_api()