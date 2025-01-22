from dataclasses import field, dataclass
from datetime import datetime
from io import BytesIO
import logging
import time
import urllib.parse
from typing import Optional

import feedparser
import requests
from lxml import etree

# Constants
DATE_FORMAT_RSS = "%a, %d %b %Y %H:%M:%S %Z"
DATE_FORMAT_WEB = "%d.%m.%Y"
TIMEOUT_SECONDS = 15
RETRY_LIMIT = 5
BASE_URL = "https://www.bundesbank.de"

# Browser headers
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "de-DE,de;q=0.9,en;q=0.8,en-US;q=0.7",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-platform": '"macOS"',
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


@dataclass
class Publication:
    web_title: str
    published_at: datetime
    web_url: str
    related_urls: list[str] = field(default_factory=list)


class ScraperException(Exception):
    """Base exception for scraper-related errors."""
    pass


def setup_logger(debug: bool = False) -> logging.Logger:
    """Configure logging."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('dbb_scraper')


def is_pdf(url: str) -> bool:
    """Check if URL points to a PDF file."""
    return url.lower().endswith('.pdf')


def make_request(url: str, session: requests.Session, retry_count: int = 0) -> requests.Response:
    """Make HTTP request with retry logic."""
    try:
        if retry_count >= RETRY_LIMIT:
            raise ScraperException(f"Max retries ({RETRY_LIMIT}) exceeded for {url}")

        response = session.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        if response.status_code != 200:
            time.sleep(2)  # Simple backoff
            return make_request(url, session, retry_count + 1)
        
        return response
    except requests.RequestException as e:
        if retry_count < RETRY_LIMIT:
            time.sleep(2)
            return make_request(url, session, retry_count + 1)
        raise ScraperException(f"Failed to fetch {url}: {str(e)}")


def load_rss_link(rss_url: str, logger: Optional[logging.Logger] = None) -> list[Publication]:
    """Load and parse RSS feed content."""
    if logger is None:
        logger = setup_logger()
    
    logger.info(f"Fetching RSS feed: {rss_url}")
    session = requests.Session()
    
    try:
        response = make_request(rss_url, session)
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            logger.warning("No entries found in RSS feed")
            return []
        
        publications = []
        for entry in feed.entries:
            try:
                # Basic validation of required fields
                if not all(hasattr(entry, attr) for attr in ['title', 'link', 'published']):
                    continue
                
                # Parse publication date
                pub_date = datetime.strptime(entry.published, DATE_FORMAT_RSS)
                
                # Get related URLs from enclosures
                related_urls = []
                if hasattr(entry, 'enclosures'):
                    related_urls = [
                        enc.href for enc in entry.enclosures 
                        if hasattr(enc, 'href') and enc.href.startswith(('http://', 'https://'))
                    ]
                
                pub = Publication(
                    web_title=entry.title.strip(),
                    web_url=entry.link,
                    published_at=pub_date,
                    related_urls=related_urls
                )
                publications.append(pub)
                
            except Exception as e:
                logger.warning(f"Failed to parse RSS entry: {str(e)}")
                continue
        
        return publications
        
    except Exception as e:
        logger.error(f"Failed to load RSS feed: {str(e)}")
        raise


def load_web_link(web_url: str, logger: Optional[logging.Logger] = None) -> list[Publication]:
    """Load and parse web page content."""
    if logger is None:
        logger = setup_logger()
    
    logger.info(f"Fetching web page: {web_url}")
    session = requests.Session()
    
    try:
        # Get and parse main page
        response = make_request(web_url, session)
        parser = etree.HTMLParser()
        tree = etree.parse(BytesIO(response.content), parser)
        
        publications = []
        articles = tree.xpath('//*[@id="main-content"]//div[contains(@class, "collection__item")]')
        
        for article in articles:
            try:
                # Extract title and link
                link_elem = article.xpath('.//a[contains(@class, "teasable__link")]')
                title_elem = article.xpath('.//div[contains(@class, "teasable__title--marked")]//div')
                date_elem = article.xpath('.//div[contains(@class, "teasable__text")]//p')
                
                if not all([link_elem, title_elem, date_elem]):
                    continue
                
                link = urllib.parse.urljoin(BASE_URL, link_elem[0].get('href'))
                title = title_elem[0].text.strip()
                
                # Parse date from description
                date_str = date_elem[0].text.strip().split(':')[0].strip()
                pub_date = datetime.strptime(date_str, DATE_FORMAT_WEB)
                
                related_urls = []
                if not is_pdf(link):
                    # Get related URLs from article page
                    try:
                        article_resp = make_request(link, session)
                        article_tree = etree.parse(BytesIO(article_resp.content), parser)
                        # Get related URLs using the same approach as original
                        files_list = article_tree.xpath('//*[@id="main-content"]/div/div/main/nav/ul/li')
                        related_urls = []
                        
                        for file in files_list:
                            try:
                                link_elem = file.xpath(".//a")
                                if not link_elem:
                                    continue
                                    
                                url = link_elem[0].get("href")
                                if not url:
                                    continue

                                # Handle relative URLs
                                if not url.startswith(('http://', 'https://')):
                                    url = urllib.parse.urljoin(BASE_URL, url)
                                
                                related_urls.append(url)
                            except Exception as e:
                                logger.warning(f"Failed to parse related URL: {str(e)}")
                                continue
                    except Exception as e:
                        logger.warning(f"Failed to get related URLs for {link}: {str(e)}")
                
                pub = Publication(
                    web_title=title,
                    web_url=link,
                    published_at=pub_date,
                    related_urls=related_urls
                )
                publications.append(pub)
                
            except Exception as e:
                logger.warning(f"Failed to parse article: {str(e)}")
                continue
        
        return publications
        
    except Exception as e:
        logger.error(f"Failed to load web page: {str(e)}")
        raise


def download_file(file_url: str, logger: Optional[logging.Logger] = None) -> BytesIO:
    """Download file content."""
    if logger is None:
        logger = setup_logger()
        
    logger.info(f"Downloading file: {file_url}")
    session = requests.Session()
    
    try:
        response = make_request(file_url, session)
        return BytesIO(response.content)
    except Exception as e:
        logger.error(f"Failed to download file: {str(e)}")
        raise


if __name__ == "__main__":
    logger = setup_logger(debug=False)
    
    try:
        # Test RSS feed scraping
        rss_pubs = load_rss_link(
            "https://www.bundesbank.de/service/rss/de/633286/feed.rss",
            logger
        )
        print(f"\nFound {len(rss_pubs)} RSS publications")
        
        # Test web page scraping
        web_pubs = load_web_link(
            "https://www.bundesbank.de/de/presse/stellungnahmen",
            logger
        )
        print(f"\nFound {len(web_pubs)} web publications")
        print("\nWeb Publications:")
        print("-" * 140)
        print(f"{'Title':<60} {'Date':<20} {'Related URLs':<15} {'URL':<37}")
        print("-" * 140)
        for pub in web_pubs: print(f"{pub.web_title[:57]+'...':<60} {pub.published_at.strftime('%Y-%m-%d'):<20} {len(pub.related_urls):<15} {pub.web_url[:40]+'...':<40}")

        # Test file download
        pdf_buffer = download_file(
            "https://www.bundesbank.de/resource/blob/696204/ffdf2c3e5dc30961892a835482998453/472B63F073F071307366337C94F8C870/2016-01-11-ogaw-download.pdf",
            logger
        )
        print("\nSuccessfully downloaded PDF file")
        
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")