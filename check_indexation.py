#!/usr/bin/env python3
"""
Main entry point for SEO Indexation Checker
"""

import sys
import argparse
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from indexation_checker import main as check_main

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Check website indexation status using Google Search Console API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--website", "-w",
        help="Check specific website by name"
    )

    parser.add_argument(
        "--config", "-c",
        default="config/websites.json",
        help="Path to websites configuration file"
    )

    parser.add_argument(
        "--output-dir", "-o",
        default="results",
        help="Output directory for results"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()

    # Change to script directory
    os.chdir(Path(__file__).parent)

    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)

    # Set environment variables for the checker
    os.environ["INDEXATION_CONFIG"] = args.config
    os.environ["INDEXATION_OUTPUT_DIR"] = args.output_dir

    if args.website:
        os.environ["INDEXATION_SPECIFIC_WEBSITE"] = args.website

    if args.verbose:
        os.environ["INDEXATION_VERBOSE"] = "1"

    # Run the checker
    try:
        check_main()
    except KeyboardInterrupt:
        print("\n⚠️  Indexation check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()