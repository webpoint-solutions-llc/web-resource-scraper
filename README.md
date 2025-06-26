# Web Resource Scraper

A Python tool for automatically downloading PDF and PowerPoint files from websites while maintaining the site's hierarchical folder structure.

## Features

🔍 **Smart Resource Detection**
- Automatically finds PDF, PPT, and PPTX files on web pages
- Detects both direct links and embedded resources
- Handles various URL formats and edge cases

📁 **Intelligent Folder Organization**
- Creates nested folder structures based on website hierarchy
- Uses page titles and URL paths for meaningful folder names
- Maintains logical organization that mirrors the source website

🏷️ **Smart File Naming**
- Generates descriptive filenames from link text
- Cleans up filenames to be filesystem-compatible
- Handles duplicate files automatically

🛡️ **Respectful Scraping**
- Includes delays between requests to avoid overwhelming servers
- Uses appropriate headers to identify the scraper
- Tracks downloaded files to avoid duplicates

📋 **Preview Mode**
- See what files will be downloaded before actually downloading
- Preview the folder structure that will be created
- Verify file names and locations

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/web-resource-scraper.git
cd web-resource-scraper
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv scraper_env

# Activate virtual environment
# On Windows:
scraper_env\Scripts\activate
# On macOS/Linux:
source scraper_env/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` file, install dependencies manually:

```bash
pip install requests beautifulsoup4 pathlib
```

## Quick Start

### Basic Usage

1. **Edit the script** to add your target URLs:

```python
pages_to_scrape = [
    "https://example.com/resources",
    "https://example.com/documents",
    # Add more URLs here
]
```

2. **Run in preview mode** to see what will be downloaded:

```bash
python resource_scraper.py
```

3. **Enable actual downloading** by uncommenting the download section in the script.

### Example Usage

```python
from resource_scraper import ResourceScraper

# Initialize scraper
scraper = ResourceScraper("https://example.com", download_folder="my_downloads")

# URLs to scrape
urls = [
    "https://example.com/page1",
    "https://example.com/page2"
]

# Preview what will be downloaded
scraper.scrape_multiple_pages(urls, preview_only=True)

# Actually download the files
downloaded = scraper.scrape_multiple_pages(urls)
```

## Configuration Options

### Scraper Parameters

```python
scraper = ResourceScraper(
    base_url="https://example.com",           # Base URL for the website
    download_folder="downloaded_resources"    # Folder to save files
)
```

### Customizing File Types

By default, the scraper looks for PDF, PPT, and PPTX files. To modify this, edit the `find_resources()` method:

```python
# Look for additional file types
if any(full_url.lower().endswith(ext) for ext in [".pdf", ".ppt", ".pptx", ".doc", ".docx"]):
```

### Adjusting Delays

To be more or less aggressive with scraping speed, modify the delay values:

```python
# In download_file method
time.sleep(0.5)  # Delay between individual file downloads

# In scrape_multiple_pages method  
time.sleep(1)    # Delay between pages
```

## Folder Structure

The scraper creates folders based on the website's structure:

```
downloaded_resources/
├── special-sabbaths/
│   ├── advent_hope_pdf.pdf
│   └── mission_emphasis_pptx.pptx
├── evangelism/
│   ├── public_evangelism_guide.pdf
│   └── personal_witnessing_slides.pptx
└── health-ministry/
    ├── health_seminar_materials.pdf
    └── cooking_class_presentation.pptx
```

## Advanced Usage

### Custom Folder Naming

Override the folder naming logic by modifying the `get_folder_path()` method:

```python
def custom_folder_naming(self, page_url, page_title):
    # Your custom logic here
    return custom_folder_path
```

### Filtering Resources

Add custom filtering logic in the `find_resources()` method:

```python
# Example: Only download files with specific keywords
if any(keyword in link_text.lower() for keyword in ['guide', 'manual', 'presentation']):
    resources.append(resource_info)
```

### Handling Authentication

For sites requiring authentication, modify the session:

```python
# Add authentication
scraper.session.auth = ('username', 'password')

# Or use cookies
scraper.session.cookies.update({'session_id': 'your_session_id'})
```

## Troubleshooting

### Common Issues

**Permission Errors**
```bash
# Make sure you have write permissions to the download folder
chmod 755 downloaded_resources/
```

**SSL Certificate Errors**
```python
# Add to scraper initialization if needed
scraper.session.verify = False  # Not recommended for production
```

**Rate Limiting**
```python
# Increase delays if you're being rate limited
time.sleep(2)  # Increase delay between requests
```

### Debug Mode

Enable verbose output by adding print statements or using Python's logging module:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## File Structure

```
web-resource-scraper/
├── resource_scraper.py      # Main scraper class
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── examples/               # Example scripts
│   ├── basic_usage.py
│   └── advanced_usage.py
└── tests/                  # Unit tests (optional)
    └── test_scraper.py
```

## Dependencies

- **requests** (>=2.25.0) - HTTP library for making web requests
- **beautifulsoup4** (>=4.9.0) - HTML/XML parser for extracting data
- **pathlib** (built-in) - Object-oriented filesystem paths

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Ethics and Legal Considerations

### Responsible Usage

- **Respect robots.txt**: Check the website's robots.txt file before scraping
- **Rate limiting**: Don't overwhelm servers with too many requests
- **Terms of service**: Review and comply with website terms of service
- **Copyright**: Ensure you have permission to download copyrighted content
- **Personal use**: This tool is designed for personal/educational use

### Best Practices

1. Always test with a small number of pages first
2. Use preview mode to verify what will be downloaded
3. Implement appropriate delays between requests
4. Monitor your network usage and server response times
5. Be prepared to stop scraping if requested by site administrators

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with detailed information about your problem
4. Include error messages, URLs being scraped, and your Python version

## Changelog

### v1.0.0
- Initial release
- Basic PDF/PPT scraping functionality
- Nested folder structure creation
- Preview mode
- Smart filename generation

---

**⚠️ Disclaimer**: This tool is for educational and personal use only. Users are responsible for ensuring compliance with website terms of service, copyright laws, and ethical scraping practices.
