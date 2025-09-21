#!/usr/bin/env python3
"""
Test Austin Fence & Deck Builders indexation checking
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from indexation_checker import check_website_indexation

def main():
    """Test Austin Fence & Deck Builders specifically"""
    print("Austin Fence & Deck Builders Indexation Test")
    print("=" * 50)

    # Load the specific configuration for Austin Fence & Deck Builders
    austin_config = {
        "name": "Austin Fence & Deck Builders",
        "description": "Austin Fence & Deck with GSC access and IndexedAPI",
        "max_urls": 10,  # Limited for testing
        "enabled": True,
        "gsc_available": True,
        "sitemap_urls": [
            "https://austinfenceanddeck.com/post-sitemap.xml",
            "https://austinfenceanddeck.com/page-sitemap.xml"
        ],
        "indexed_api_key": "5d3a782984b4cfeab30e21e70f74e2e5",
        "checking_method": "auto"
    }

    print(f"Testing: {austin_config['name']}")
    print(f"Method: {austin_config['checking_method']}")
    print(f"IndexedAPI Key: {'***' + austin_config['indexed_api_key'][-4:]}")
    print(f"Max URLs: {austin_config['max_urls']}")
    print()

    try:
        # Run the check
        results = check_website_indexation(austin_config)

        if results:
            print(f"\n=== RESULTS ===")
            print(f"Total URLs checked: {len(results)}")

            # Count by status
            indexed = sum(1 for r in results if 'INDEXED' in r.get('status', ''))
            not_indexed = sum(1 for r in results if 'NOT' in r.get('status', ''))
            errors = sum(1 for r in results if 'ERROR' in r.get('status', ''))

            print(f"Indexed: {indexed}")
            print(f"Not indexed: {not_indexed}")
            print(f"Errors: {errors}")

            # Show method used
            if results:
                method = results[0].get('method', 'Unknown')
                print(f"Method used: {method}")

            # Show first few results
            print(f"\nFirst 5 results:")
            for i, result in enumerate(results[:5]):
                print(f"  {i+1}. {result.get('url', 'No URL')[:60]}... - {result.get('status', 'No status')}")

        else:
            print("[ERROR] No results returned")

    except Exception as e:
        print(f"[ERROR] Exception during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()