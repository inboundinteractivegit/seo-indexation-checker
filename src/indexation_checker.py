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

# Import our Search Console checker
from search_console_checker import SearchConsoleChecker

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
    try:
        search_query = f"site:{url}"
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            if "did not match any documents" in response.text or "No results found" in response.text:
                return "NOT INDEXED", "Google Search"
            else:
                return "INDEXED", "Google Search"
        else:
            return "ERROR", f"Google Search (HTTP {response.status_code})"

    except Exception as e:
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

def check_website_indexation(website_config):
    """
    Check indexation for a single website using best available method
    """
    print(f"\n=== Checking: {website_config['name']} ===")

    # Initialize Search Console checker
    gsc_checker = SearchConsoleChecker('search_console_credentials.json')
    gsc_available = gsc_checker.service is not None

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

    print(f"Found {len(all_urls)} URLs to check")

    # Determine which method to use
    website_domain = get_base_domain(all_urls[0]) if all_urls else ""
    gsc_property_url = None

    # Check if we have GSC access for this domain
    if gsc_available:
        for prop_url in gsc_properties:
            prop_domain = get_base_domain(prop_url)
            if website_domain in prop_domain or prop_domain in website_domain:
                gsc_property_url = prop_url
                break

    if gsc_property_url:
        print(f"[INFO] Using Google Search Console API for {website_config['name']}")
        print(f"[INFO] GSC Property: {gsc_property_url}")

        # Use GSC API
        results = gsc_checker.check_indexation_status(gsc_property_url, all_urls)

    else:
        print(f"[INFO] Using Google Search fallback for {website_config['name']}")
        print(f"[WARN] For better accuracy, add this site to Search Console and grant access to the service account")

        # Use Google search fallback
        results = []
        for i, url in enumerate(all_urls, 1):
            print(f"Checking {i}/{len(all_urls)}: {url}")

            status, method = check_indexation_google_search(url)

            results.append({
                'url': url,
                'status': status,
                'method': method,
                'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # Rate limiting for Google search
            if i % 10 == 0:
                print(f"  Processed {i} URLs, taking a short break...")
                time.sleep(5)
            else:
                time.sleep(2)

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