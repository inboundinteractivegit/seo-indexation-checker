#!/usr/bin/env python3
"""
Test IsIndexed.com API endpoints to understand their structure
"""

import requests
import json

def test_isindexed_endpoints():
    """Test various IsIndexed.com API endpoints"""

    # Common base URLs to try
    base_urls = [
        "https://tool.isindexed.com/api",
        "https://api.isindexed.com",
        "https://www.isindexed.com/api",
        "https://isindexed.com/api"
    ]

    # Common endpoint paths to try
    endpoints = [
        "/check",
        "/bulk",
        "/status",
        "/credits",
        "/v1/check",
        "/v1/bulk"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json'
    }

    print("Testing IsIndexed.com API endpoints...")
    print("=" * 50)

    for base_url in base_urls:
        print(f"\nTesting base URL: {base_url}")

        # Test base URL first
        try:
            response = requests.get(base_url, headers=headers, timeout=5)
            print(f"  Base URL: HTTP {response.status_code} - {response.text[:100]}...")
        except Exception as e:
            print(f"  Base URL: ERROR - {str(e)}")

        # Test endpoints
        for endpoint in endpoints:
            full_url = base_url + endpoint
            try:
                # Try GET first
                response = requests.get(full_url, headers=headers, timeout=5)
                print(f"  GET {endpoint}: HTTP {response.status_code}")

                if response.status_code == 200:
                    print(f"    Content: {response.text[:200]}...")
                elif response.status_code == 405:  # Method not allowed, try POST
                    test_data = {"urls": ["https://example.com"]}
                    post_response = requests.post(full_url, headers=headers, json=test_data, timeout=5)
                    print(f"  POST {endpoint}: HTTP {post_response.status_code}")
                    if post_response.status_code != 404:
                        print(f"    Content: {post_response.text[:200]}...")

            except Exception as e:
                print(f"  {endpoint}: ERROR - {str(e)}")

def test_direct_website():
    """Test the main website for any API clues"""

    try:
        response = requests.get("https://www.isindexed.com/en/", timeout=10)
        print(f"\nMain website: HTTP {response.status_code}")

        # Look for API references in the page
        content = response.text.lower()
        api_keywords = ['api', 'endpoint', 'documentation', 'bulk', 'check']

        for keyword in api_keywords:
            if keyword in content:
                print(f"Found '{keyword}' on main page")

    except Exception as e:
        print(f"Main website error: {e}")

if __name__ == "__main__":
    test_isindexed_endpoints()
    test_direct_website()