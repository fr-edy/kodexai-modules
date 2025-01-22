from dataclasses import field, dataclass
from datetime import datetime
from io import BytesIO
import logging
import time
import urllib.parse

import feedparser
import requests
from lxml import etree

# Constants
DATE_FORMAT_RSS = "%a, %d %b %Y %H:%M:%S %Z"
DATE_FORMAT_WEB = "%d.%m.%Y"
DEBUG = True
TIMEOUT_AFTER_SECONDS = 15
RETRY_LIMIT = 5
BUNDESBANK_BASE_URL = "https://www.bundesbank.de"
CHROME_DATA = {
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-platform": '"macOS"',
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


# Errors
class ParserException(Exception):
    """Custom exception for parser-related errors."""

    pass


class TooManyRetries(Exception):
    """Custom exception for network-related errors."""

    pass


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

class BundesbankScraper(BaseScraper):
    def __init__(self, debug: bool = False) -> None:
        super().__init__("dbb_scraper", debug=debug)
        self.base = BUNDESBANK_BASE_URL

    def parse_rss_articles(self, feed: feedparser.FeedParserDict) -> list[Publication]:
        """
        Parse RSS feed content and extract articles.

        Args:
            feed (feedparser.FeedParserDict): Parsed RSS feed

        Returns:
            list[Publication]: List of parsed Publication objects

        Raises:
            ParserException: If RSS parsing fails
        """
        try:
            publications = []

            for entry in feed.entries:
                try:
                    title = entry.title
                    link = entry.link
                    published_at = entry.published

                    # Get enclosure URL if available
                    related_urls = (
                        [enclosure.href for enclosure in entry.enclosures]
                        if "enclosures" in entry
                        else []
                    )

                    published_at_datetime = datetime.strptime(
                        published_at, DATE_FORMAT_RSS
                    )

                    publications.append(
                        Publication(
                            web_title=title,
                            web_url=link,
                            published_at=published_at_datetime,
                            related_urls=related_urls,
                        )
                    )

                except (AttributeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse RSS entry: {str(e)}")
                    continue

            return publications

        except Exception as e:
            raise ParserException(f"Failed to parse RSS content: {str(e)}")

    def _parse_article(self, article: etree._Element) -> Publication | None:
        try:
            # Extract required elements
            link_elem = article.xpath(".//a[contains(@class, 'teasable__link')]")

            link = urllib.parse.urljoin(self.base, link_elem[0].get("href"))
            title_elem = article.xpath(
                ".//div[contains(@class, 'teasable__title--marked')]//div"
            )
            web_title = title_elem[0].text.strip() if title_elem else None

            # Parse publication date
            published_at = None
            description = article.xpath(".//div[contains(@class, 'teasable__text')]//p")
            if description:
                description_text = description[0].text.strip()
                try:
                    date_str = description_text.split(":")[0].strip()
                    published_at = datetime.strptime(date_str, DATE_FORMAT_WEB)
                except (ValueError, IndexError):
                    self.logger.warning(
                        f"Failed to parse date from: {description_text}"
                    )

            if web_title and link and published_at:
                return Publication(
                    web_title=web_title,
                    web_url=link,
                    published_at=published_at,
                    related_urls=[],
                )
            else:
                self.logger.warning("Failed to parse web_title, link or published_at")

        except Exception as e:
            self.logger.warning(f"Failed to parse article: {str(e)}")
            return None

    def parse_web_articles(self, tree: etree._ElementTree) -> list[Publication]:
        """
        Parse web page content and extract articles.

        Args:
            tree (etree._ElementTree): Parsed HTML tree

        Returns:
            list[Publication]: List of parsed Publication objects

        Raises:
            ParserException: If HTML parsing fails
        """
        try:
            publications: list[Publication] = []

            article_list: etree._ElementTree = tree.xpath(
                '//*[@id="main-content"]/div/div/main/div[2]/div/div/nav/ul'
            )[0]
            
            articles = article_list.xpath(
                ".//div[contains(@class, 'collection__item')]"
            )

            for article in articles:
                if pub := self._parse_article(article):
                    if not is_pdf(pub.web_url):
                        pub.related_urls = self.get_article_related_urls(pub.web_url)
                    publications.append(pub)

            return publications

        except Exception as e:
            raise ParserException(f"Failed to parse web content: {str(e)}")

    def parse_related_urls(self, tree: etree._ElementTree) -> list[str]:
        files_list: list[etree._ElementTree] = tree.xpath(
            '//*[@id="main-content"]/div/div/main/nav/ul/li'
        )
        file_urls: list[str] = []

        for file in files_list:
            link_elem = file.xpath(".//a")
            file_urls.append(link_elem[0].get("href"))

        return file_urls

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

    rss_pubs = s.load_rss_link(f"{BUNDESBANK_BASE_URL}/service/rss/de/633286/feed.rss")
    print("rss_pubs:")
    for pub in rss_pubs:
        print(f" - {pub.web_title}")

    web_pubs = s.load_web_link(f"{BUNDESBANK_BASE_URL}/de/presse/stellungnahmen")
    print("\n\nweb_pubs:")
    for pub in web_pubs:
        print(f" - {pub.published_at} ({len(pub.related_urls)} related)")

    pdf_bytes = s.download_file(
        f"{BUNDESBANK_BASE_URL}/resource/blob/696204/ffdf2c3e5dc30961892a835482998453/472B63F073F071307366337C94F8C870/2016-01-11-ogaw-download.pdf"
    )
    with open("sample_pdf.pdf", "wb") as f:
        f.write(pdf_bytes)
    # print("\n\nDownloaded PDF, saved to sample_pdf.pdf")
