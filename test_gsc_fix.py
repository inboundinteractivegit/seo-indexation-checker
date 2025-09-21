#!/usr/bin/env python3
"""
Google Search Console Fix Tester
Quick diagnostic tool to test GSC API connectivity
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gsc_connectivity():
    """Test Google Search Console API connectivity"""
    print("Google Search Console API Fix Tester")
    print("=" * 50)
    print()

    # 1. Check credentials
    print("1. Checking credentials file...")
    try:
        with open('config/google_credentials.json', 'r') as f:
            creds = json.load(f)

        project_id = creds.get('project_id', 'NOT FOUND')
        client_email = creds.get('client_email', 'NOT FOUND')

        print(f"   [OK] Credentials loaded successfully")
        print(f"   Project ID: {project_id}")
        print(f"   Service Account: {client_email}")

        if project_id == 'indexation-checker-472711':
            print("   [OK] Correct project ID found")
        else:
            print(f"   [ERROR] Unexpected project ID: {project_id}")

    except Exception as e:
        print(f"   [ERROR] Error loading credentials: {e}")
        return False

    print()

    # 2. Test API initialization
    print("2. Testing API initialization...")
    try:
        from search_console_checker import SearchConsoleChecker

        gsc = SearchConsoleChecker('config/google_credentials.json')

        if gsc.service:
            print("   [OK] Search Console API client initialized")
            print(f"   Stored project ID: {getattr(gsc, 'project_id', 'NOT SET')}")
        else:
            print("   [ERROR] Failed to initialize API client")
            return False

    except Exception as e:
        print(f"   [ERROR] Error during initialization: {e}")
        return False

    print()

    # 3. Test API call
    print("3. Testing API call...")
    try:
        properties = gsc.get_properties()

        if isinstance(properties, list):
            print(f"   [SUCCESS] API call successful!")
            print(f"   Properties found: {len(properties)}")

            if len(properties) > 0:
                print("   Available properties:")
                for prop in properties:
                    print(f"      - {prop}")
            else:
                print("   [INFO] No properties found (this is normal for new accounts)")
                print("   [TIP] Add websites to Google Search Console first")

            return True

    except Exception as e:
        error_str = str(e)
        print(f"   [ERROR] API call failed: {e}")

        # Analyze error
        if '571882533378' in error_str:
            print()
            print("   [DIAGNOSIS] Google routing cache issue")
            print("   [SOLUTION] Enable Search Console API in correct project")
            print("   [URL] https://console.developers.google.com/apis/api/searchconsole.googleapis.com/overview?project=indexation-checker-472711")

        elif 'accessNotConfigured' in error_str:
            print()
            print("   [DIAGNOSIS] API not enabled")
            print("   [SOLUTION] Enable Google Search Console API")

        elif 'forbidden' in error_str.lower():
            print()
            print("   [DIAGNOSIS] Permission issue")
            print("   [SOLUTION] Check service account permissions")

        return False

    print()

def main():
    """Main test function"""
    success = test_gsc_connectivity()

    print()
    print("=" * 50)

    if success:
        print("[SUCCESS] GSC API WORKING!")
        print("[READY] Your Google Search Console integration is ready!")
        print("[TIP] You can now use GSC as the primary checking method")
    else:
        print("[ATTENTION] GSC API NEEDS ATTENTION")
        print("[ACTION] Follow the diagnostic suggestions above")
        print("[INFO] The tool will continue using fallback methods")

    print()
    print("[FALLBACK] Methods available:")
    print("   1. IndexedAPI (when DNS resolves)")
    print("   2. Google Search (always available)")
    print()

    input("Press Enter to exit...")

if __name__ == "__main__":
    main()