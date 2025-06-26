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

        # Track folder structure
        self.folder_structure = {}

    def clean_filename(self, text, max_length=100):
        """Clean and format text to be a valid filename"""
        if not text or not text.strip():
            return None

        # Remove HTML tags if any
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up the text
        text = text.strip()

        # Replace invalid filename characters (including those invalid for folder names)
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

    def create_folder_name(self, url, page_title=None):
        """Generate a folder name based on URL path and page title"""
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.split("/") if part]

        # Use the last meaningful part of the URL path
        folder_name = None
        if path_parts:
            folder_name = self.clean_filename(path_parts[-1])

        # If we have a page title, use it (cleaned)
        if page_title:
            title_cleaned = self.clean_filename(page_title)
            if title_cleaned and len(title_cleaned) > len(folder_name or ""):
                folder_name = title_cleaned

        # Fallback to a generic name based on URL
        if not folder_name:
            domain = parsed_url.netloc.replace("www.", "")
            folder_name = self.clean_filename(domain) or "webpage"

        return folder_name

    def get_page_title(self, soup):
        """Extract page title from soup"""
        # Try multiple methods to get a meaningful page title
        title = None

        # Method 1: Page title tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Method 2: Main heading
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

        # Method 3: Meta title
        if not title:
            meta_title = soup.find("meta", attrs={"name": "title"}) or soup.find(
                "meta", attrs={"property": "og:title"}
            )
            if meta_title:
                title = meta_title.get("content", "").strip()

        return title

    def get_folder_path(self, page_url, page_title=None):
        """Generate the full folder path for a given page"""
        if page_url in self.folder_structure:
            return self.folder_structure[page_url]

        parsed_url = urlparse(page_url)
        path_parts = [part for part in parsed_url.path.split("/") if part]

        folder_parts = []

        # Create nested structure based on URL path
        if len(path_parts) > 0:
            for part in path_parts:
                clean_part = self.clean_filename(part)
                if clean_part:
                    folder_parts.append(clean_part)

        # If we have a page title and it's different from the last path part, use it
        if page_title:
            title_cleaned = self.clean_filename(page_title)
            if title_cleaned and (
                not folder_parts or title_cleaned != folder_parts[-1]
            ):
                # Replace the last part with the title if it's more descriptive
                if folder_parts:
                    folder_parts[-1] = title_cleaned
                else:
                    folder_parts.append(title_cleaned)

        # If no meaningful folder structure, create one based on domain
        if not folder_parts:
            domain = parsed_url.netloc.replace("www.", "")
            folder_parts = [self.clean_filename(domain) or "website"]

        # Create the full path
        folder_path = os.path.join(self.download_folder, *folder_parts)

        # Cache it
        self.folder_structure[page_url] = folder_path

        return folder_path

    def ensure_folder_exists(self, folder_path):
        """Create folder structure if it doesn't exist"""
        Path(folder_path).mkdir(parents=True, exist_ok=True)

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
        else:
            # Try to detect from URL parameters or guess
            if "pdf" in url.lower():
                return ".pdf"
            elif "ppt" in url.lower():
                return ".pptx"
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
                full_url.lower().endswith(ext) for ext in [".pdf", ".ppt", ".pptx"]
            ) or any(ext in full_url.lower() for ext in ["pdf", "ppt"]):

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
                    full_url.lower().endswith(ext) for ext in [".pdf", ".ppt", ".pptx"]
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

    def download_file(self, url, filepath):
        """Download a single file to specified path"""
        if url in self.downloaded_files:
            print(f"Already downloaded: {os.path.basename(filepath)}")
            return True

        try:
            print(f"Downloading: {os.path.basename(filepath)}")
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            # Handle duplicate filenames
            counter = 1
            original_filepath = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(original_filepath)
                filepath = f"{name}_{counter}{ext}"
                counter += 1

            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.downloaded_files.add(url)
            print(f"✓ Downloaded: {filepath}")
            return True

        except requests.RequestException as e:
            print(f"✗ Failed to download {os.path.basename(filepath)}: {e}")
            return False

    def scrape_page(self, page_url, preview_only=False):
        """Scrape a single page for resources"""
        print(f"\n--- Scraping: {page_url} ---")

        soup = self.get_page_content(page_url)
        if not soup:
            return []

        # Get page title for folder naming
        page_title = self.get_page_title(soup)
        print(f"Page title: {page_title}")

        # Determine folder path for this page
        folder_path = self.get_folder_path(page_url, page_title)
        print(f"Folder path: {folder_path}")

        resources = self.find_resources(soup, page_url)
        print(f"Found {len(resources)} resources on this page")

        if preview_only:
            print("\n--- PREVIEW MODE - Files that would be downloaded: ---")
            for i, resource in enumerate(resources, 1):
                full_filepath = os.path.join(folder_path, resource["filename"])
                print(f"{i}. Link text: '{resource['link_text']}'")
                print(f"   Generated filename: {resource['filename']}")
                print(f"   Full path: {full_filepath}")
                print(f"   Original filename: {resource['original_filename']}")
                print(f"   URL: {resource['url']}")
                print()
            return resources

        # Create folder if not in preview mode
        self.ensure_folder_exists(folder_path)

        downloaded = []
        for resource in resources:
            print(f"\nFound: '{resource['link_text']}'")
            print(f"Generated filename: {resource['filename']}")
            print(f"Original filename: {resource['original_filename']}")

            full_filepath = os.path.join(folder_path, resource["filename"])

            if self.download_file(resource["url"], full_filepath):
                resource["downloaded_path"] = full_filepath
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

    def print_folder_structure(self):
        """Print the created folder structure"""
        print("\n=== FOLDER STRUCTURE ===")
        for url, folder_path in self.folder_structure.items():
            relative_path = os.path.relpath(folder_path, self.download_folder)
            print(f"URL: {url}")
            print(f"Folder: {relative_path}")
            print()


# Usage Example
if __name__ == "__main__":
    # Initialize scraper
    scraper = ResourceScraper("https://www.sabbathschoolpersonalministries.org")

    # List of pages to scrape (add your actual URLs)
    pages_to_scrape = [
        "https://www.sabbathschoolpersonalministries.org/special-sabbaths",
        # Add more pages as needed
    ]

    # PREVIEW MODE - See what files would be downloaded and their folder structure
    print("=== PREVIEW MODE ===")
    scraper.scrape_multiple_pages(pages_to_scrape, preview_only=True)
    scraper.print_folder_structure()

    # Uncomment the lines below to actually download after previewing
    # Actual download
    print("\n=== STARTING ACTUAL DOWNLOAD ===")
    downloaded_resources = scraper.scrape_multiple_pages(pages_to_scrape)

    print(f"\n=== SUMMARY ===")
    print(f"Total resources downloaded: {len(downloaded_resources)}")
    print(f"Files saved to: {scraper.download_folder}")

    # Print folder structure
    scraper.print_folder_structure()

    # Print list of downloaded files with their paths
    for resource in downloaded_resources:
        if "downloaded_path" in resource:
            relative_path = os.path.relpath(
                resource["downloaded_path"], scraper.download_folder
            )
            print(f"- {relative_path} (from: '{resource['link_text']}')")
