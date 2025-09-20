#!/usr/bin/env python3
"""
Interactive setup script for SEO Indexation Checker
Guides users through Google Cloud and Search Console setup
"""

import os
import json
import webbrowser
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🔍 SEO Indexation Checker - Setup Assistant")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    import sys
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    import subprocess
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Please run: pip install -r requirements.txt")
        return False

def create_config_directories():
    """Create necessary directories"""
    print("\n📁 Creating configuration directories...")

    dirs = ["config", "results", "logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created: {dir_name}/")

def setup_google_cloud():
    """Guide user through Google Cloud setup"""
    print("\n🌐 Google Cloud Setup")
    print("-" * 30)

    print("1. Setting up Google Cloud Project...")
    print("   Please follow these steps:")
    print("   - Go to: https://console.cloud.google.com")
    print("   - Create a new project")
    print("   - Enable Google Search Console API")
    print("   - Enable Google Sheets API (optional)")
    print("   - Create Service Account credentials")
    print("   - Download JSON key file")

    input("\nPress Enter when you have downloaded the credentials file...")

    # Help user place credentials file
    print("\n📋 Credentials File Setup")
    print("Please rename your downloaded file to:")
    print("   search_console_credentials.json")
    print("And place it in the 'config/' directory")

    cred_path = Path("config/search_console_credentials.json")
    while not cred_path.exists():
        input("Press Enter when the credentials file is in place...")
        if not cred_path.exists():
            print("❌ File not found. Please check the path and filename.")

    print("✅ Credentials file found!")
    return True

def setup_search_console():
    """Guide user through Search Console setup"""
    print("\n🔍 Search Console Setup")
    print("-" * 30)

    # Read service account email from credentials
    cred_path = Path("config/search_console_credentials.json")
    if cred_path.exists():
        try:
            with open(cred_path) as f:
                credentials = json.load(f)
                service_email = credentials.get("client_email", "")

            print(f"Service Account Email: {service_email}")
            print("\nPlease add this email to your Search Console properties:")
            print("1. Go to: https://search.google.com/search-console")
            print("2. For each website, go to Settings > Users and permissions")
            print("3. Add the service account email with 'Full User' permission")

            input("\nPress Enter when you've added the service account to your properties...")
            print("✅ Search Console access configured!")

        except Exception as e:
            print(f"❌ Error reading credentials: {e}")
            return False

    return True

def create_sample_config():
    """Create sample websites configuration"""
    print("\n⚙️  Creating sample configuration...")

    config = {
        "websites": [
            {
                "name": "Example Website",
                "sitemap_url": "https://example.com/sitemap_index.xml",
                "exclude_sitemaps": ["local-sitemap.xml"],
                "enabled": false,
                "gsc_available": false,
                "description": "Sample configuration - replace with your actual websites"
            }
        ]
    }

    config_path = Path("config/websites.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Sample configuration created: {config_path}")
    print("   Please edit this file with your actual websites")

def test_setup():
    """Test the setup"""
    print("\n🧪 Testing setup...")

    try:
        # Test imports
        import gspread
        from googleapiclient.discovery import build
        print("✅ Required packages imported successfully")

        # Test credentials
        cred_path = Path("config/search_console_credentials.json")
        if cred_path.exists():
            print("✅ Credentials file found")
        else:
            print("❌ Credentials file missing")
            return False

        print("✅ Setup test completed successfully!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function"""
    print_banner()

    # Check Python version
    if not check_python_version():
        return

    # Install dependencies
    if not install_dependencies():
        return

    # Create directories
    create_config_directories()

    # Setup Google Cloud
    if not setup_google_cloud():
        return

    # Setup Search Console
    if not setup_search_console():
        return

    # Create sample config
    create_sample_config()

    # Test setup
    if test_setup():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit config/websites.json with your websites")
        print("2. Run: python check_indexation.py")
        print("3. Check the results/ directory for output files")
    else:
        print("\n❌ Setup incomplete. Please check the errors above.")

if __name__ == "__main__":
    main()