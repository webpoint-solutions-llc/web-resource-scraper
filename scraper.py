import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
from pathlib import Path
import re


class ResourceScraper:
    def __init__(self, base_url, download_folder="downloaded_resources"):
        self.base_url = base_url
        self.download_folder = download_folder
        self.session = requests.Session()
        # Add headers to avoid being blocked
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # Create download folder
        Path(self.download_folder).mkdir(exist_ok=True)

        # Track downloaded files to avoid duplicates
        self.downloaded_files = set()

    def clean_filename(self, text, max_length=100):
        """Clean and format text to be a valid filename"""
        if not text or not text.strip():
            return None

        # Remove HTML tags if any
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up the text
        text = text.strip()

        # Convert to lowercase
        text = text.lower()

        # Replace invalid filename characters
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        text = re.sub(invalid_chars, "_", text)

        # Replace multiple spaces/underscores with single underscore
        text = re.sub(r"[\s_]+", "_", text)

        # Remove leading/trailing underscores and dots
        text = text.strip("_.")

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length].rstrip("_.")

        return text if text else None

    def get_file_extension(self, url):
        """Extract file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()

        if path.endswith(".pdf"):
            return ".pdf"
        elif path.endswith(".ppt"):
            return ".ppt"
        elif path.endswith(".pptx"):
            return ".pptx"
        elif path.endswith(".docx"):
            return ".docx"
        elif path.endswith(".xls"):
            return ".xls"
        elif path.endswith(".mp4"):
            return ".mp4"
        elif path.endswith(".doc"):
            return ".doc"
        else:
            # Try to detect from URL parameters or guess
            if "pdf" in url.lower():
                return ".pdf"
            elif "ppt" in url.lower():
                return ".pptx"
            elif "docx" in url.lower():
                return ".docx"
            elif "xls" in url.lower():
                return ".xls"
            elif "mp4" in url.lower():
                return ".mp4"
            elif "doc" in url.lower():
                return ".doc"
            else:
                return ".pdf"  # Default fallback

    def generate_filename(self, link_text, original_url, fallback_name=None):
        """Generate a clean filename from link text"""
        extension = self.get_file_extension(original_url)

        # Try to use link text first
        clean_text = self.clean_filename(link_text)

        if clean_text and len(clean_text) > 2:  # Ensure meaningful name
            filename = f"{clean_text}{extension}"
        elif fallback_name:
            # Use provided fallback
            clean_fallback = self.clean_filename(fallback_name)
            filename = (
                f"{clean_fallback}{extension}"
                if clean_fallback
                else f"document{extension}"
            )
        else:
            # Use original filename from URL
            original_name = os.path.basename(urlparse(original_url).path)
            if original_name and "." in original_name:
                filename = original_name
            else:
                filename = f"document{extension}"

        return filename

    def get_page_content(self, url):
        """Fetch and parse a webpage"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def find_resources(self, soup, page_url):
        """Find all PDF and PPT resources on a page with their link text"""
        resources = []

        # Look for direct links to PDFs and PPTs
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(page_url, href)

            # Check if it's a PDF or PPT file
            if any(
                full_url.lower().endswith(ext)
                for ext in [".pdf", ".ppt", ".pptx", ".docx", ".xls", ".mp4", ".doc"]
            ) or any(
                ext in full_url.lower()
                for ext in ["pdf", "ppt", "xls", "docx", "mp4", "doc"]
            ):

                # Get link text and clean it
                link_text = link.get_text(strip=True)

                # Also check for title attribute as fallback
                title_attr = link.get("title", "")

                # Generate filename based on link text
                filename = self.generate_filename(
                    link_text, full_url, fallback_name=title_attr
                )

                resources.append(
                    {
                        "url": full_url,
                        "filename": filename,
                        "link_text": link_text,
                        "title": title_attr,
                        "original_filename": os.path.basename(urlparse(full_url).path),
                    }
                )

        # Also check embedded objects and iframes
        for embed in soup.find_all(["embed", "object", "iframe"]):
            src = embed.get("src") or embed.get("data")
            if src:
                full_url = urljoin(page_url, src)
                if any(
                    full_url.lower().endswith(ext)
                    for ext in [
                        ".pdf",
                        ".ppt",
                        ".pptx",
                        ".docx",
                        ".xls",
                        ".mp4",
                        ".doc",
                    ]
                ):

                    # For embedded content, try to find nearby text or title
                    title_text = embed.get("title", "") or embed.get("alt", "")

                    filename = self.generate_filename(
                        title_text, full_url, fallback_name="Embedded_Resource"
                    )

                    resources.append(
                        {
                            "url": full_url,
                            "filename": filename,
                            "link_text": title_text or "Embedded resource",
                            "title": title_text,
                            "original_filename": os.path.basename(
                                urlparse(full_url).path
                            ),
                        }
                    )

        return resources

    def download_file(self, url, filename):
        """Download a single file"""
        if url in self.downloaded_files:
            print(f"Already downloaded: {filename}")
            return True

        try:
            print(f"Downloading: {filename}")
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            filepath = os.path.join(self.download_folder, filename)

            # Handle duplicate filenames
            counter = 1
            original_filepath = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(original_filepath)
                filepath = f"{name}_{counter}{ext}"
                counter += 1

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.downloaded_files.add(url)
            print(f"✓ Downloaded: {os.path.basename(filepath)}")
            return True

        except requests.RequestException as e:
            print(f"✗ Failed to download {filename}: {e}")
            return False

    def scrape_page(self, page_url, preview_only=False):
        """Scrape a single page for resources"""
        print(f"\n--- Scraping: {page_url} ---")

        soup = self.get_page_content(page_url)
        if not soup:
            return []

        resources = self.find_resources(soup, page_url)
        print(f"Found {len(resources)} resources on this page")

        if preview_only:
            print("\n--- PREVIEW MODE - Files that would be downloaded: ---")
            for i, resource in enumerate(resources, 1):
                print(f"{i}. Link text: '{resource['link_text']}'")
                print(f"   Generated filename: {resource['filename']}")
                print(f"   Original filename: {resource['original_filename']}")
                print(f"   URL: {resource['url']}")
                print()
            return resources

        downloaded = []
        for resource in resources:
            print(f"\nFound: '{resource['link_text']}'")
            print(f"Generated filename: {resource['filename']}")
            print(f"Original filename: {resource['original_filename']}")

            if self.download_file(resource["url"], resource["filename"]):
                downloaded.append(resource)

            # Be respectful - add small delay between downloads
            time.sleep(0.5)

        return downloaded

    def scrape_multiple_pages(self, page_urls, preview_only=False):
        """Scrape multiple pages"""
        all_downloaded = []

        for i, url in enumerate(page_urls, 1):
            print(f"\n=== Processing Page {i}/{len(page_urls)} ===")
            downloaded = self.scrape_page(url, preview_only=preview_only)
            all_downloaded.extend(downloaded)

            # Delay between pages to be respectful
            if not preview_only:
                time.sleep(1)

        return all_downloaded


# Usage Example
if __name__ == "__main__":
    # Initialize scraper
    scraper = ResourceScraper("https://www.sabbathschoolpersonalministries.org")

    # List of pages to scrape (add your actual URLs)
    pages_to_scrape = [
        "https://www.sabbathschoolpersonalministries.org/acs_iicd",
        # Add more pages as needed
    ]

    # PREVIEW MODE - See what files would be downloaded and their names
    print("=== PREVIEW MODE ===")
    scraper.scrape_multiple_pages(pages_to_scrape, preview_only=True)

    # Uncomment the lines below to actually download after previewing

""""
    # Actual download
    print("\n=== STARTING ACTUAL DOWNLOAD ===")
    downloaded_resources = scraper.scrape_multiple_pages(pages_to_scrape)

    print(f"\n=== SUMMARY ===")
    print(f"Total resources downloaded: {len(downloaded_resources)}")
    print(f"Files saved to: {scraper.download_folder}")

    # Print list of downloaded files with their link text
    for resource in downloaded_resources:
        print(f"- {resource['filename']} (from: '{resource['link_text']}')")
"""
