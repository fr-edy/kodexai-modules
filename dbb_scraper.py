from dataclasses import field, dataclass
from datetime import datetime, timedelta
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
TIMEOUT_AFTER_SECONDS = 15
RETRY_LIMIT = 5
BUNDESBANK_BASE_URL = "https://www.bundesbank.de"
CHROME_DATA = {
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-platform": '"macOS"',
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
MAX_TITLE_LENGTH = 500  # Maximum reasonable title length
MIN_TITLE_LENGTH = 3    # Minimum reasonable title length
MAX_RELATED_URLS = 50   # Maximum reasonable number of related URLs
FUTURE_TOLERANCE = timedelta(days=1)  # Allow dates up to 1 day in the future
PAST_TOLERANCE = timedelta(days=(datetime.now() - datetime(2000, 1, 1)).days)  # Reasonable past date limit (since 2000)


# Errors
class ParserException(Exception):
    """Custom exception for parser-related errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details or {}

class TooManyRetries(Exception):
    """Custom exception for network-related errors."""
    pass

class ValidationError(Exception):
    """Custom exception for data validation errors."""
    def __init__(self, message: str, field: str, value: any):
        super().__init__(f"{message} - Field: {field}, Value: {value}")
        self.field = field
        self.value = value


# Utils
def is_pdf(url: str) -> bool:
    parsed_url = urllib.parse.urlparse(url)
    return parsed_url.path.lower().endswith(".pdf")


# Base scraping class
class BaseScraper:
    def __init__(self, id: str, debug: bool = False) -> None:
        self.debug = debug
        self.session = requests.Session()
        self.header_config = self._initialize_headers()
        self.logger = self._initialize_logger(id, debug)

    def _initialize_headers(self) -> dict[str, dict[str, str]]:
        return {
            "GET": {
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
                "sec-ch-ua": CHROME_DATA["sec-ch-ua"],
                "sec-ch-ua-platform": CHROME_DATA["sec-ch-ua-platform"],
                "user-agent": CHROME_DATA["user-agent"],
            },
            "RSS": {
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
                "sec-ch-ua": CHROME_DATA["sec-ch-ua"],
                "sec-ch-ua-platform": CHROME_DATA["sec-ch-ua-platform"],
                "user-agent": CHROME_DATA["user-agent"],
            },
            "PDF": {
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
                "sec-ch-ua": CHROME_DATA["sec-ch-ua"],
                "sec-ch-ua-platform": CHROME_DATA["sec-ch-ua-platform"],
                "user-agent": CHROME_DATA["user-agent"],
            },
        }

    def _initialize_logger(self, id: str, debug: bool) -> logging.Logger:
        """Initialize logger with appropriate logging level.
        
        Args:
            id (str): Logger identifier
            debug (bool): Whether to enable debug logging
            
        Returns:
            logging.Logger: Configured logger instance
        """
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(id)

    def retry_wait(self, seconds: int = 2) -> None:
        """Wait between retry attempts.
        
        Args:
            seconds (int): Number of seconds to wait. Defaults to 2.
        """
        time.sleep(seconds)

    def _request(
        self, url: str, method: str, config: str, expected: int = 200, retries: int = 0
    ) -> requests.Response:
        """Make HTTP request with retry logic.
        
        Args:
            url (str): Target URL
            method (str): HTTP method
            config (str): Header configuration key
            expected (int): Expected HTTP status code. Defaults to 200.
            retries (int): Current retry attempt count. Defaults to 0.
            
        Returns:
            requests.Response: Response object
            
        Raises:
            TooManyRetries: When retry limit is exceeded
        """
        try:
            if retries > RETRY_LIMIT:
                raise TooManyRetries(f"Failed to get {url} after {RETRY_LIMIT} attempts")

            resp = self.session.request(
                method,
                url,
                headers=self.header_config[config],
                timeout=TIMEOUT_AFTER_SECONDS,
            )

            if resp.status_code != expected:
                self.logger.warning(f"Unexpected status code {resp.status_code} for {url}")
                self.retry_wait()
                return self._request(
                    url, method, config, expected=expected, retries=retries + 1
                )

            return resp
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            self.retry_wait()
            return self._request(
                url, method, config, expected=expected, retries=retries + 1
            )

    def get_page(self, url: str) -> requests.Response:
        """Get webpage content.
        
        Args:
            url (str): Target URL
            
        Returns:
            requests.Response: Response object
        """
        return self._request(url, "GET", "GET")

    def get_page_as_tree(self, url: str) -> etree._ElementTree:
        """Get webpage content as parsed HTML tree.
        
        Args:
            url (str): Target URL
            
        Returns:
            etree._ElementTree: Parsed HTML tree
        """
        page = self.get_page(url)
        parser = etree.HTMLParser()
        tree = etree.parse(BytesIO(page.text.encode("utf-8")), parser)
        return tree

    def get_rss_feed(self, url: str) -> feedparser.FeedParserDict:
        """Get and parse RSS feed content.
        
        Args:
            url (str): RSS feed URL
            
        Returns:
            feedparser.FeedParserDict: Parsed RSS feed
        """
        resp = self._request(url, "GET", "RSS")
        return feedparser.parse(resp.text)

    def download_file(self, url: str) -> bytes:
        """Download file content.
        
        Args:
            url (str): File URL
            
        Returns:
            bytes: File content
        """
        config = "PDF" if is_pdf(url) else "GET"
        resp = self._request(url, "GET", config)
        return resp.content
    
    
@dataclass
class Publication:
    web_title: str
    published_at: datetime
    web_url: str
    related_urls: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate publication data after initialization."""
        self._validate_title()
        self._validate_date()
        self._validate_url()
        self._validate_related_urls()

    def _validate_title(self):
        """Validate title length and content."""
        if not isinstance(self.web_title, str):
            raise ValidationError("Title must be a string", "web_title", self.web_title)
        if not MIN_TITLE_LENGTH <= len(self.web_title) <= MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Title length must be between {MIN_TITLE_LENGTH} and {MAX_TITLE_LENGTH} characters",
                "web_title",
                self.web_title
            )

    def _validate_date(self):
        """Validate publication date is within reasonable bounds."""
        if not isinstance(self.published_at, datetime):
            raise ValidationError("Published date must be a datetime object", "published_at", self.published_at)
        
        now = datetime.now()
        if self.published_at > now + FUTURE_TOLERANCE:
            raise ValidationError("Publication date cannot be too far in the future", "published_at", self.published_at)
        if self.published_at < now - PAST_TOLERANCE:
            raise ValidationError("Publication date cannot be too far in the past", "published_at", self.published_at)

    def _validate_url(self):
        """Validate web URL format and structure."""
        if not isinstance(self.web_url, str):
            raise ValidationError("URL must be a string", "web_url", self.web_url)
        
        try:
            parsed = urllib.parse.urlparse(self.web_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationError("Invalid URL format", "web_url", self.web_url)
        except Exception as e:
            raise ValidationError(f"URL parsing failed: {str(e)}", "web_url", self.web_url)

    def _validate_related_urls(self):
        """Validate related URLs list."""
        if not isinstance(self.related_urls, list):
            raise ValidationError("Related URLs must be a list", "related_urls", self.related_urls)
        
        if len(self.related_urls) > MAX_RELATED_URLS:
            raise ValidationError(
                f"Too many related URLs (max: {MAX_RELATED_URLS})",
                "related_urls",
                len(self.related_urls)
            )

        for url in self.related_urls:
            if not isinstance(url, str):
                raise ValidationError("Related URL must be a string", "related_urls", url)
            try:
                parsed = urllib.parse.urlparse(url)
                if not all([parsed.scheme, parsed.netloc]):
                    raise ValidationError("Invalid related URL format", "related_urls", url)
            except Exception as e:
                raise ValidationError(f"Related URL parsing failed: {str(e)}", "related_urls", url)


class BundesbankScraper(BaseScraper):
    def __init__(self, debug: bool = False) -> None:
        super().__init__("dbb_scraper", debug=debug)
        self.base = BUNDESBANK_BASE_URL

    def parse_rss_articles(self, feed: feedparser.FeedParserDict) -> list[Publication]:
        """Parse RSS feed content and extract articles with enhanced validation."""
        if not feed.entries:
            raise ParserException("Empty RSS feed", {"feed_status": feed.get("status", "unknown")})

        publications = []
        errors = []

        for entry in feed.entries:
            try:
                # Validate required fields exist
                if not all(hasattr(entry, attr) for attr in ['title', 'link', 'published']):
                    missing_attrs = [attr for attr in ['title', 'link', 'published'] 
                                   if not hasattr(entry, attr)]
                    raise ParserException(f"Missing required attributes: {missing_attrs}")

                # Clean and validate title
                title = entry.title.strip()
                
                # Validate and parse date
                try:
                    published_at = datetime.strptime(entry.published, DATE_FORMAT_RSS)
                except ValueError as e:
                    raise ParserException(f"Invalid date format: {str(e)}")

                # Validate URL
                if not entry.link.startswith(('http://', 'https://')):
                    raise ParserException(f"Invalid URL format: {entry.link}")

                # Get and validate enclosures
                related_urls = []
                if hasattr(entry, 'enclosures'):
                    for enclosure in entry.enclosures:
                        if not hasattr(enclosure, 'href'):
                            continue
                        url = enclosure.href
                        if url.startswith(('http://', 'https://')):
                            related_urls.append(url)

                # Create and validate publication
                pub = Publication(
                    web_title=title,
                    web_url=entry.link,
                    published_at=published_at,
                    related_urls=related_urls
                )
                publications.append(pub)

            except (ParserException, ValidationError) as e:
                errors.append({
                    'entry': entry.get('title', 'Unknown'),
                    'error': str(e),
                    'details': getattr(e, 'details', {})
                })
                self.logger.warning(f"Failed to parse RSS entry: {str(e)}")
                continue

        if errors:
            self.logger.warning(f"Encountered {len(errors)} errors while parsing RSS feed")
            for error in errors:
                self.logger.debug(f"RSS parsing error: {error}")

        if not publications:
            raise ParserException("No valid publications found in RSS feed")

        return publications

    def _parse_article(self, article: etree._Element) -> Optional[Publication]:
        """Parse single article with enhanced validation."""
        try:
            # Extract and validate link
            link_elem = article.xpath(".//a[contains(@class, 'teasable__link')]")
            if not link_elem:
                raise ParserException("Link element not found")
            
            link = urllib.parse.urljoin(self.base, link_elem[0].get("href"))
            if not link:
                raise ParserException("Empty link")

            # Extract and validate title
            title_elem = article.xpath(".//div[contains(@class, 'teasable__title--marked')]//div")
            if not title_elem:
                raise ParserException("Title element not found")
            
            web_title = title_elem[0].text.strip()
            if not web_title:
                raise ParserException("Empty title")

            # Parse and validate publication date
            description = article.xpath(".//div[contains(@class, 'teasable__text')]//p")
            if not description:
                raise ParserException("Description element not found")

            description_text = description[0].text.strip()
            try:
                date_str = description_text.split(":")[0].strip()
                published_at = datetime.strptime(date_str, DATE_FORMAT_WEB)
            except (ValueError, IndexError) as e:
                raise ParserException(f"Failed to parse date: {str(e)}")

            # Create and validate publication
            return Publication(
                web_title=web_title,
                web_url=link,
                published_at=published_at,
                related_urls=[]
            )

        except Exception as e:
            self.logger.warning(f"Failed to parse article: {str(e)}")
            return None

    def parse_web_articles(self, tree: etree._ElementTree) -> list[Publication]:
        """Parse web articles with enhanced validation and error collection."""
        try:
            publications = []
            errors = []

            article_list = tree.xpath('//*[@id="main-content"]/div/div/main/div[2]/div/div/nav/ul')
            if not article_list:
                raise ParserException("Article list not found")

            articles = article_list[0].xpath(".//div[contains(@class, 'collection__item')]")
            if not articles:
                raise ParserException("No articles found in list")

            for article in articles:
                try:
                    pub = self._parse_article(article)
                    if pub:
                        if not is_pdf(pub.web_url):
                            pub.related_urls = self.get_article_related_urls(pub.web_url)
                        publications.append(pub)
                except (ParserException, ValidationError) as e:
                    errors.append({
                        'article': article.get('class', 'Unknown'),
                        'error': str(e),
                        'details': getattr(e, 'details', {})
                    })
                    continue

            if errors:
                self.logger.warning(f"Encountered {len(errors)} errors while parsing web articles")
                for error in errors:
                    self.logger.debug(f"Web parsing error: {error}")

            if not publications:
                raise ParserException("No valid publications found")

            return publications

        except Exception as e:
            raise ParserException(f"Failed to parse web content: {str(e)}")

    def parse_related_urls(self, tree: etree._ElementTree) -> list[str]:
        """Parse related URLs with validation."""
        try:
            files_list = tree.xpath('//*[@id="main-content"]/div/div/main/nav/ul/li')
            if not files_list:
                return []

            file_urls = []
            for file in files_list:
                try:
                    link_elem = file.xpath(".//a")
                    if not link_elem:
                        continue
                        
                    url = link_elem[0].get("href")
                    if not url:
                        continue

                    # Basic URL validation
                    parsed = urllib.parse.urlparse(url)
                    if not all([parsed.scheme, parsed.netloc]):
                        url = urllib.parse.urljoin(self.base, url)
                    
                    file_urls.append(url)
                except Exception as e:
                    self.logger.warning(f"Failed to parse related URL: {str(e)}")
                    continue

            return file_urls[:MAX_RELATED_URLS]  # Limit number of related URLs

        except Exception as e:
            self.logger.error(f"Failed to parse related URLs: {str(e)}")
            return []
        
    def load_rss_link(self, url: str) -> list[Publication]:
        self.logger.info(f"Getting rss feed from {url}")
        rss_feed = self.get_rss_feed(url)
        return self.parse_rss_articles(rss_feed)

    def load_web_link(self, url: str) -> list[Publication]:
        self.logger.info(f"Getting articles on for {url}")
        tree = self.get_page_as_tree(url)
        return self.parse_web_articles(tree)

    def get_article_related_urls(self, article_url: str) -> list[str]:
        self.logger.info(f"Getting related urls for {article_url}")
        tree = self.get_page_as_tree(article_url)
        return self.parse_related_urls(tree)


# Example usage
if __name__ == "__main__":
    s = BundesbankScraper(False)
    

    try:
        rss_pubs = s.load_rss_link(f"{BUNDESBANK_BASE_URL}/service/rss/de/633286/feed.rss")
        print(f"Successfully parsed {len(rss_pubs)} RSS publications")
    except ParserException as e:
        print(f"Failed to parse RSS feed: {str(e)}")
        if e.details:
            print(f"Error details: {e.details}")
    except ValidationError as e:
        print(f"Validation error: {str(e)}")
        print(f"Field: {e.field}, Value: {e.value}")
        
    try:
        web_pubs = s.load_web_link(f"{BUNDESBANK_BASE_URL}/de/presse/stellungnahmen")
        print(f"Successfully parsed {len(web_pubs)} WEB publications")
    except ParserException as e:
        print(f"Failed to parse WEB feed: {str(e)}")
        if e.details:
            print(f"Error details: {e.details}")
    except ValidationError as e:
        print(f"Validation error: {str(e)}")
        print(f"Field: {e.field}, Value: {e.value}")

        
    pdf_bytes = s.download_file(
        f"{BUNDESBANK_BASE_URL}/resource/blob/696204/ffdf2c3e5dc30961892a835482998453/472B63F073F071307366337C94F8C870/2016-01-11-ogaw-download.pdf"
    )
    with open("sample_pdf.pdf", "wb") as f:
        f.write(pdf_bytes)
    # print("\n\nDownloaded PDF, saved to sample_pdf.pdf")
