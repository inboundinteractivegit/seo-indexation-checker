# 🚀 II Indexation Checker
## Inbound Interactive's Professional SEO Indexation Monitoring Tool

A powerful Python tool for monitoring website indexation status using Google Search Console API with intelligent fallbacks.

## ✨ Features

- 🎯 **Google Search Console API** integration for 100% accurate results
- 🔄 **Intelligent fallback** to Google search when GSC unavailable
- 📊 **Google Sheets integration** for automated reporting
- 🗂️ **Multi-website support** with JSON configuration
- 📈 **Historical tracking** with timestamps
- ⚡ **Sitemap auto-discovery** from XML sitemaps
- 🚀 **Rate limiting** and respectful crawling

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/inboundinteractivegit/seo-indexation-checker.git
cd seo-indexation-checker

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Google Search Console (Recommended)

```bash
# Run the setup script
python setup.py
```

Or follow the [detailed setup guide](docs/SETUP.md).

### 3. Configure Websites

Edit `config/websites.json`:

```json
{
  "websites": [
    {
      "name": "Your Website",
      "sitemap_url": "https://yoursite.com/sitemap_index.xml",
      "enabled": true,
      "gsc_available": true
    }
  ]
}
```

### 4. Run Indexation Check

**Option A: GUI Tool (Recommended)**
```bash
# Launch the user-friendly interface
python ii_indexation_gui.py

# Or double-click (Windows)
launch_ii_indexation.bat
```

**Option B: Command Line**
```bash
# Check all websites
python check_indexation.py

# Check specific website
python check_indexation.py --website "Your Website"

# Upload to Google Sheets
python upload_to_sheets.py
```

## 📊 Output Formats

- **CSV Files**: Detailed results with timestamps
- **Google Sheets**: Live dashboard with summaries
- **Console Output**: Real-time progress and summaries

## 🏢 Company Usage

### For SEO Teams
- Monitor indexation across multiple client websites
- Generate automated reports for stakeholders
- Track indexation trends over time

### For Developers
- Validate sitemap submissions after deployments
- Monitor new page indexation status
- Integrate with CI/CD pipelines

### For Marketing
- Track campaign page indexation
- Monitor competitor indexation (fallback method)
- Generate client reports automatically

## 📈 Methods & Accuracy

| Method | Accuracy | Rate Limits | Requirements |
|--------|----------|-------------|--------------|
| Google Search Console API | 100% | None | Website ownership |
| Google Search Fallback | ~85% | Yes | None |

## 🔧 Configuration

### Websites Configuration
Located in `config/websites.json`. Supports:
- Sitemap index URLs
- Multiple sitemap URLs
- Exclusion filters
- GSC property mapping

### Credentials
- `config/search_console_credentials.json` - GSC API access
- `config/google_sheets_credentials.json` - Sheets integration

## 📋 Requirements

- Python 3.7+
- Google Cloud Project (for APIs)
- Search Console access (recommended)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/your-company/seo-indexation-checker/issues)
- 💬 [Discussions](https://github.com/your-company/seo-indexation-checker/discussions)

## 📊 Example Output

```
=== FINAL SUMMARY ===
Your Website:
  Method: Search Console Data
  Total URLs: 1,247
  Indexed: 1,156 (92.7%)
  File: your_website_indexation_results.csv
```

---

**Made with ❤️ by Inbound Interactive SEO Team**