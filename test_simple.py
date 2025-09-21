#!/usr/bin/env python3
"""
Simple functionality testing for II Indexation Checker
"""

import sys
import os
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("II Indexation Checker - Quick Functionality Test")
    print("=" * 50)

    # Test 1: File structure
    print("\n[TEST 1] Checking file structure...")
    required_files = [
        "ii_indexation_gui_modern.py",
        "src/indexation_checker.py",
        "src/indexed_api_checker.py",
        "config/websites.json"
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[PASS] {file_path}")
        else:
            print(f"[FAIL] {file_path} - NOT FOUND")

    # Test 2: Configuration loading
    print("\n[TEST 2] Testing configuration loading...")
    try:
        with open("config/websites.json", 'r') as f:
            config = json.load(f)
        websites = config.get('websites', [])
        print(f"[PASS] Configuration loaded - {len(websites)} websites found")
        for website in websites:
            print(f"  - {website.get('name', 'Unknown')}")
    except Exception as e:
        print(f"[FAIL] Configuration loading failed: {e}")

    # Test 3: Module imports
    print("\n[TEST 3] Testing module imports...")
    try:
        from indexation_checker import check_website_indexation
        print("[PASS] indexation_checker imported")
    except ImportError as e:
        print(f"[FAIL] indexation_checker import failed: {e}")

    try:
        from indexed_api_checker import IndexedAPIChecker
        print("[PASS] indexed_api_checker imported")
    except ImportError as e:
        print(f"[FAIL] indexed_api_checker import failed: {e}")

    try:
        from search_console_checker import SearchConsoleChecker
        print("[PASS] search_console_checker imported")
    except ImportError as e:
        print(f"[FAIL] search_console_checker import failed: {e}")

    # Test 4: PyQt6 availability
    print("\n[TEST 4] Testing PyQt6 availability...")
    try:
        from PyQt6.QtWidgets import QApplication
        print("[PASS] PyQt6 is available for modern GUI")
    except ImportError as e:
        print(f"[FAIL] PyQt6 not available: {e}")

    # Test 5: IndexedAPI initialization
    print("\n[TEST 5] Testing IndexedAPI initialization...")
    try:
        from indexed_api_checker import IndexedAPIChecker
        api_checker = IndexedAPIChecker()
        print("[PASS] IndexedAPI checker initialized")

        # Test API status (without key)
        is_valid, message = api_checker.check_api_status()
        print(f"[INFO] API Status: {message}")
    except Exception as e:
        print(f"[FAIL] IndexedAPI initialization failed: {e}")

    print("\n" + "=" * 50)
    print("BASIC FUNCTIONALITY TEST COMPLETE")
    print("If all tests passed, the application should work for your team!")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()