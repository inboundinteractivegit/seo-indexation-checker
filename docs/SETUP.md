# 🔧 Setup Guide

Complete setup instructions for the SEO Indexation Checker.

## Prerequisites

- Python 3.7 or higher
- Google account with admin access to your websites
- Basic command line knowledge

## Step 1: Installation

### Download the Tool

```bash
git clone https://github.com/your-company/seo-indexation-checker.git
cd seo-indexation-checker
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the automated setup:

```bash
python setup.py
```

## Step 2: Google Cloud Setup

### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "New Project"
3. Name it: `seo-indexation-checker`
4. Click "Create"

### Enable APIs

1. Search for "Google Search Console API"
2. Click "Enable"
3. Search for "Google Sheets API" (optional)
4. Click "Enable"

### Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **"Create Service Account"**
3. Name: `indexation-checker`
4. Click **"Create"**
5. Skip optional steps

### Download Credentials

1. Click on your service account
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **"JSON"**
5. Download the file
6. Rename to: `search_console_credentials.json`
7. Place in: `config/` directory

## Step 3: Search Console Access

### Add Service Account to Properties

For each website you want to monitor:

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select your property
3. Click **Settings** (gear icon)
4. Click **"Users and permissions"**
5. Click **"Add user"**
6. Enter the service account email from your JSON file
7. Set permission to **"Full User"**
8. Click **"Add"**

### Find Service Account Email

Open `config/search_console_credentials.json` and look for:

```json
{
  "client_email": "indexation-checker@your-project.iam.gserviceaccount.com"
}
```

## Step 4: Configure Websites

### Create Configuration File

Copy the example configuration:

```bash
cp config/websites.example.json config/websites.json
```

### Edit Configuration

Edit `config/websites.json`:

```json
{
  "websites": [
    {
      "name": "Your Website",
      "sitemap_url": "https://yoursite.com/sitemap_index.xml",
      "exclude_sitemaps": ["local-sitemap.xml"],
      "enabled": true,
      "gsc_available": true
    }
  ]
}
```

### Configuration Options

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Display name for website | Yes |
| `sitemap_url` | Main sitemap or sitemap index URL | Yes* |
| `sitemap_urls` | Array of specific sitemap URLs | Yes* |
| `exclude_sitemaps` | Sitemaps to skip (by filename) | No |
| `enabled` | Whether to check this website | No |
| `gsc_available` | Has Search Console access | No |

*Either `sitemap_url` OR `sitemap_urls` required

## Step 5: Google Sheets (Optional)

### Setup Sheets Integration

1. Enable Google Sheets API in Google Cloud
2. Use same service account credentials
3. Create a Google Sheet
4. Share with service account email
5. Give "Editor" permission

### Test Sheets Integration

```bash
python upload_to_sheets.py
```

## Step 6: Test Installation

### Run Basic Check

```bash
python check_indexation.py --verbose
```

### Expected Output

```
=== Universal Indexation Checker with Google Search Console API ===
Started at: 2025-09-20 15:30:00

=== Checking: Your Website ===
[OK] Search Console API client initialized successfully
[INFO] GSC Properties available: 1
[INFO] Using Google Search Console API for Your Website
Found 150 URLs to check
[INFO] Checking 150 URLs against Search Console data...
[OK] Results saved to: your_website_indexation_results.csv

=== FINAL SUMMARY ===
Your Website:
  Method: Search Console Data
  Total URLs: 150
  Indexed: 142 (94.7%)
  File: your_website_indexation_results.csv
```

## Troubleshooting

### Common Issues

**"Credentials file not found"**
- Ensure file is named exactly: `search_console_credentials.json`
- Check file is in `config/` directory

**"No properties found"**
- Verify service account email is added to Search Console
- Check permissions are set to "Full User"
- Wait 5-10 minutes after adding

**"Permission denied" errors**
- Verify Google APIs are enabled
- Check service account has correct permissions

**"No URLs found"**
- Verify sitemap URLs are correct and accessible
- Check sitemap format is valid XML
- Ensure exclude_sitemaps isn't blocking everything

### Getting Help

1. Check [FAQ](FAQ.md)
2. Review [examples](../examples/)
3. Open an [issue](https://github.com/your-company/seo-indexation-checker/issues)

## Advanced Configuration

### Scheduling Checks

Use cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/seo-indexation-checker && python check_indexation.py
```

### Multiple Environments

Create separate config files:

```
config/
├── websites.production.json
├── websites.staging.json
└── websites.development.json
```

Use with:

```bash
python check_indexation.py --config config/websites.production.json
```

### Custom Output Location

```bash
python check_indexation.py --output-dir /custom/path/results
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Restrict service account permissions** to minimum required
3. **Use environment variables** for sensitive data in production
4. **Regularly rotate** service account keys
5. **Monitor API usage** in Google Cloud Console

---

**Next:** [Usage Examples](USAGE.md)