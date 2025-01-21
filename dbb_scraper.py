from dataclasses import field, dataclass
from typing import List, Optional
import urllib.parse
from datetime import datetime
import requests
from lxml import etree
from io import BytesIO
import logging
import time
import feedparser

# Constants
DATE_FORMAT_RSS = "%a, %d %b %Y %H:%M:%S %Z"
DATE_FORMAT_WEB = "%d.%m.%Y"
# DEBUG = True
TIMEOUT_AFTER_SECONDS = 15
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


# Base scraping class
class BaseScraper:
    def __init__(self, id: str, debug: bool = False) -> None:
        self.debug = debug
        self.session = requests.Session()

        self.header_config = {
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

        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = logging.getLogger(id)

    def retry_wait(self, seconds: int = 2) -> None:
        time.sleep(seconds)

    def _request(
        self, url: str, method: str, config: str, expected: int = 200, retries: int = 0
    ) -> requests.Response:
        resp = self.session.request(
            method,
            url,
            headers=self.header_config[config],
            timeout=TIMEOUT_AFTER_SECONDS,
        )

        if resp.status_code != expected:
            self.retry_wait()
            return self._request(url, config, expected=expected, retries=retries + 1)

        return resp

    def get_page(self, url: str) -> requests.Response:
        return self._request(url, "GET", "GET")

    def get_rss_feed(self, url: str) -> feedparser.FeedParserDict:
        resp = self._request(url, "GET", "RSS")
        return feedparser.parse(resp.text)

    def download_file(self, url: str) -> BytesIO:
        config = "PDF" if url.endswith(".pdf") else "GET"
        resp = self._request(url, "GET", config)
        return resp.content


@dataclass
class Publication:
    web_title: str
    published_at: datetime
    web_url: str
    related_urls: List[str] = field(default_factory=list)


class BundesbankScraper(BaseScraper):
    def __init__(self, debug=False):
        super().__init__("dbb_scraper", debug=debug)
        self.base = BUNDESBANK_BASE_URL

    def parse_rss_articles(self, feed: feedparser.FeedParserDict) -> List[Publication]:
        """
        Parse RSS feed content and extract articles.

        Args:
            content (str): Raw RSS XML content

        Returns:
            List[Publication]: List of parsed Publication objects

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

    def _parse_article(self, article) -> Optional[Publication]:
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

    def parse_web_articles(self, content: str) -> List[Publication]:
        """
        Parse web page content and extract articles.

        Args:
            content (str): Raw HTML content

        Returns:
            List[Publication]: List of parsed Publication objects

        Raises:
            ParserException: If HTML parsing fails
        """
        try:
            parser = etree.HTMLParser()
            tree = etree.parse(BytesIO(content.encode("utf-8")), parser)
            publications = []

            article_list = tree.xpath(
                '//*[@id="main-content"]/div/div/main/div[2]/div/div/nav/ul'
            )[0]
            articles = article_list.xpath(
                ".//div[contains(@class, 'collection__item')]"
            )

            for article in articles:
                if pub := self._parse_article(article):
                    publications.append(pub)

            return publications

        except Exception as e:
            raise ParserException(f"Failed to parse web content: {str(e)}")

    def load_rss_link(self, url: str) -> List[Publication]:
        rss_feed = self.get_rss_feed(url)
        return self.parse_rss_articles(rss_feed)

    def load_web_link(self, url: str) -> List[Publication]:
        data = self.get_page(url)
        return self.parse_web_articles(data.text)


# Example usage
if __name__ == "__main__":
    s = BundesbankScraper(False)

    rss_pubs = s.load_rss_link(f"{BUNDESBANK_BASE_URL}/service/rss/de/633286/feed.rss")
    print("rss_pubs:")
    for pub in rss_pubs:
        print(f" - {pub}")

    web_pubs = s.load_web_link(f"{BUNDESBANK_BASE_URL}/de/presse/stellungnahmen")
    print("\n\nweb_pubs:")
    for pub in web_pubs:
        print(f" - {pub}")

    pdf_bytes = s.download_file(
        f"{BUNDESBANK_BASE_URL}/resource/blob/696204/ffdf2c3e5dc30961892a835482998453/472B63F073F071307366337C94F8C870/2016-01-11-ogaw-download.pdf"
    )
    with open("sample_pdf.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("\n\nDownloaded PDF, saved to sample_pdf.pdf")
