#!/usr/bin/env python3
"""
Upload indexation results to Google Sheets
"""

import sys
import argparse
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from google_sheets_integration import main as sheets_main

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Upload indexation results to Google Sheets"
    )

    parser.add_argument(
        "--results-dir", "-r",
        default="results",
        help="Directory containing CSV results files"
    )

    parser.add_argument(
        "--sheet-name", "-s",
        default="Website Indexation Results",
        help="Google Sheets document name"
    )

    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()

    # Change to script directory
    os.chdir(Path(__file__).parent)

    # Change to results directory
    if Path(args.results_dir).exists():
        os.chdir(args.results_dir)

    # Run sheets integration
    try:
        sheets_main()
    except KeyboardInterrupt:
        print("\n⚠️  Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()