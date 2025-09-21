#!/usr/bin/env python3
"""
Universal Dynamic Website Indexation Checker with Google Search Console API
This script fetches fresh URLs from sitemaps and checks indexation using GSC API when available,
falls back to Google search for other sites.
"""

import requests
import time
import csv
import json
from urllib.parse import quote_plus
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Import our checkers
from search_console_checker import SearchConsoleChecker
from indexed_api_checker import IndexedAPIChecker

def fetch_urls_from_sitemap_index(sitemap_index_url, exclude_sitemaps=None):
    """
    Fetch URLs from a sitemap index XML file that contains references to other sitemaps.
    Returns a list of URLs.
    """
    if exclude_sitemaps is None:
        exclude_sitemaps = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(sitemap_index_url, headers=headers)
        response.raise_for_status()

        # Parse XML to find individual sitemaps
        root = ET.fromstring(response.content)
        sitemap_urls = []

        for elem in root:
            for child in elem:
                if child.tag.endswith('loc'):
                    sitemap_url = child.text
                    # Check if this sitemap should be excluded
                    should_exclude = any(exclude in sitemap_url for exclude in exclude_sitemaps)
                    if not should_exclude:
                        sitemap_urls.append(sitemap_url)

        print(f"  Found {len(sitemap_urls)} sitemaps in index")

        # Fetch URLs from each individual sitemap
        all_urls = []
        for sitemap_url in sitemap_urls:
            print(f"  Processing sitemap: {sitemap_url}")
            sitemap_urls_batch = fetch_urls_from_sitemap(sitemap_url)
            all_urls.extend(sitemap_urls_batch)
            time.sleep(1)  # Be polite

        return all_urls

    except Exception as e:
        print(f"Error fetching sitemap index: {e}")
        return []

def fetch_urls_from_sitemap(sitemap_url):
    """
    Fetch URLs from a single sitemap XML file.
    Returns a list of URLs.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(sitemap_url, headers=headers)
        response.raise_for_status()

        # Parse XML to find URLs
        root = ET.fromstring(response.content)
        urls = []

        for elem in root:
            for child in elem:
                if child.tag.endswith('loc'):
                    urls.append(child.text)

        return urls

    except Exception as e:
        print(f"Error fetching sitemap {sitemap_url}: {e}")
        return []

def check_indexation_google_search(url):
    """
    Check if a URL is indexed using Google search (fallback method)
    """
    import random

    # Rotate user agents to avoid detection
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    try:
        search_query = f"site:{url}"
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"

        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            if "did not match any documents" in response.text or "No results found" in response.text:
                return "NOT INDEXED", "Google Search"
            else:
                return "INDEXED", "Google Search"
        elif response.status_code == 429:
            print(f"    Rate limited for {url} - need longer delays")
            return "RATE LIMITED", f"Google Search (HTTP {response.status_code})"
        else:
            print(f"    HTTP {response.status_code} for {url}")
            return "ERROR", f"Google Search (HTTP {response.status_code})"

    except Exception as e:
        print(f"    Exception for {url}: {str(e)}")
        return "ERROR", f"Google Search ({str(e)})"

def normalize_website_url(url):
    """Normalize website URL for Search Console property matching"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    if not url.endswith('/'):
        url += '/'
    return url

def get_base_domain(url):
    """Extract base domain from URL"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc

def check_website_indexation(website_config, stop_event=None):
    """
    Check indexation for a single website using best available method

    Args:
        website_config: Configuration dictionary for the website
        stop_event: Threading event to signal when to stop checking
    """
    print(f"\n=== Checking: {website_config['name']} ===")

    # Initialize checkers
    gsc_checker = SearchConsoleChecker('config/google_credentials.json')
    gsc_available = gsc_checker.service is not None

    # Initialize IndexedAPI checker if configured
    indexed_api_key = website_config.get('indexed_api_key', None)
    indexed_api_checker = IndexedAPIChecker(indexed_api_key) if indexed_api_key else None
    indexed_api_available = indexed_api_checker is not None

    # Get available GSC properties
    gsc_properties = []
    if gsc_available:
        gsc_properties = [prop['url'] for prop in gsc_checker.get_properties()]
        print(f"[INFO] GSC Properties available: {len(gsc_properties)}")

    # Fetch URLs from sitemaps
    all_urls = []

    if 'sitemap_url' in website_config:
        # Single sitemap index
        print(f"Fetching URLs from sitemap index: {website_config['sitemap_url']}")
        exclude_sitemaps = website_config.get('exclude_sitemaps', [])
        all_urls = fetch_urls_from_sitemap_index(website_config['sitemap_url'], exclude_sitemaps)

    elif 'sitemap_urls' in website_config:
        # Multiple specific sitemaps
        print(f"Fetching URLs from {len(website_config['sitemap_urls'])} sitemaps")
        for sitemap_url in website_config['sitemap_urls']:
            print(f"  Processing: {sitemap_url}")
            urls = fetch_urls_from_sitemap(sitemap_url)
            all_urls.extend(urls)
            time.sleep(1)

    if not all_urls:
        print(f"No URLs found for {website_config['name']}")
        return []

    # Check for stop signal before processing
    if stop_event and stop_event.is_set():
        print("[STOP] Check stopped by user")
        return []

    print(f"Found {len(all_urls)} URLs to check")

    # Apply URL limit for reasonable processing time
    max_urls = website_config.get('max_urls', 100)  # Default limit of 100 URLs
    if len(all_urls) > max_urls:
        print(f"[LIMIT] Limiting to first {max_urls} URLs (from {len(all_urls)} total)")
        all_urls = all_urls[:max_urls]

    # Determine which method to use (Priority: GSC > IndexedAPI > Google Search)
    website_domain = get_base_domain(all_urls[0]) if all_urls else ""
    gsc_property_url = None

    # Check if we have GSC access for this domain
    if gsc_available:
        for prop_url in gsc_properties:
            prop_domain = get_base_domain(prop_url)
            if website_domain in prop_domain or prop_domain in website_domain:
                gsc_property_url = prop_url
                break

    # Choose checking method based on availability and configuration
    preferred_method = website_config.get('checking_method', 'auto')  # auto, gsc, indexed_api, google_search

    if preferred_method == 'gsc' and gsc_property_url:
        print(f"[INFO] Using Google Search Console API (preferred) for {website_config['name']}")
        print(f"[INFO] GSC Property: {gsc_property_url}")
        results = gsc_checker.check_indexation_status(gsc_property_url, all_urls, stop_event=stop_event)

    elif preferred_method == 'indexed_api' and indexed_api_available:
        print(f"[INFO] Using IndexedAPI (preferred) for {website_config['name']}")
        results = indexed_api_checker.check_indexation_status(all_urls, stop_event=stop_event)

    elif preferred_method == 'google_search':
        print(f"[INFO] Using Google Search (preferred) for {website_config['name']}")
        results = []
        for i, url in enumerate(all_urls, 1):
            if stop_event and stop_event.is_set():
                print(f"[STOP] Check stopped by user after processing {i-1}/{len(all_urls)} URLs")
                break
            print(f"Checking {i}/{len(all_urls)}: {url}")
            status, method = check_indexation_google_search(url)
            results.append({
                'url': url,
                'status': status,
                'method': method,
                'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            if i % 20 == 0:
                print(f"  Processed {i} URLs, taking a short break...")
                time.sleep(2)
            else:
                time.sleep(0.5)

    else:
        # Auto mode - use best available method with fallback
        results = []

        # Try GSC first if available
        if gsc_property_url:
            print(f"[INFO] Using Google Search Console API (auto) for {website_config['name']}")
            print(f"[INFO] GSC Property: {gsc_property_url}")
            results = gsc_checker.check_indexation_status(gsc_property_url, all_urls, stop_event=stop_event)

            # Check if GSC actually worked (returned non-empty results)
            if not results:
                print("[WARN] GSC returned no results, falling back to next method")

        # If GSC failed or not available, try IndexedAPI
        if not results and indexed_api_available:
            print(f"[INFO] Using IndexedAPI (fallback) for {website_config['name']}")
            print(f"[INFO] Fast and reliable bulk checking")
            results = indexed_api_checker.check_indexation_status(all_urls, stop_event=stop_event)

            # Check if IndexedAPI actually worked
            if not results:
                print("[WARN] IndexedAPI returned no results, falling back to Google Search")

        # If both GSC and IndexedAPI failed, use Google Search fallback
        if not results:
            print(f"[INFO] Using Google Search fallback for {website_config['name']}")
            print(f"[WARN] Primary methods failed, using Google Search as last resort")

            # Use Google search fallback
            results = []
            for i, url in enumerate(all_urls, 1):
                # Check for stop signal
                if stop_event and stop_event.is_set():
                    print(f"[STOP] Check stopped by user after processing {i-1}/{len(all_urls)} URLs")
                    break

                print(f"Checking {i}/{len(all_urls)}: {url}")

                status, method = check_indexation_google_search(url)

                results.append({
                    'url': url,
                    'status': status,
                    'method': method,
                    'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                # Adaptive rate limiting for Google search
                if 'RATE LIMITED' in status:
                    print(f"  Rate limited! Taking longer break...")
                    time.sleep(10)  # Longer delay on rate limit
                elif i % 10 == 0:
                    print(f"  Processed {i} URLs, taking a break...")
                    time.sleep(3)  # Longer base delay
                else:
                    time.sleep(1.5)  # Increased base delay to avoid rate limits

    return results

def save_results_to_csv(results, website_name):
    """Save results to CSV file"""
    if not results:
        print(f"No results to save for {website_name}")
        return None

    # Create filename
    safe_name = website_name.lower().replace(' ', '_').replace('&', 'and')
    filename = f"{safe_name}_indexation_results.csv"

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

        print(f"Results saved to: {filename}")
        return filename

    except Exception as e:
        print(f"Error saving results: {e}")
        return None

def main():
    """Main function to check all enabled websites"""
    print("=== Universal Indexation Checker with Google Search Console API ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load website configuration
    try:
        with open('websites_config.json', 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        print("Error: websites_config.json not found")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in websites_config.json")
        return

    # Check each enabled website
    total_results = []

    for website in config['websites']:
        if not website.get('enabled', True):
            print(f"Skipping disabled website: {website['name']}")
            continue

        try:
            results = check_website_indexation(website)
            if results:
                filename = save_results_to_csv(results, website['name'])
                if filename:
                    total_results.append({
                        'website': website['name'],
                        'filename': filename,
                        'total_urls': len(results),
                        'indexed': sum(1 for r in results if 'INDEXED' in r['status']),
                        'method': results[0]['method'] if results else 'Unknown'
                    })

        except Exception as e:
            print(f"Error checking {website['name']}: {e}")
            continue

    # Print summary
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if total_results:
        for result in total_results:
            indexed_rate = (result['indexed'] / result['total_urls'] * 100) if result['total_urls'] > 0 else 0
            print(f"\n{result['website']}:")
            print(f"  Method: {result['method']}")
            print(f"  Total URLs: {result['total_urls']}")
            print(f"  Indexed: {result['indexed']} ({indexed_rate:.1f}%)")
            print(f"  File: {result['filename']}")
    else:
        print("No results generated")

if __name__ == "__main__":
    main()