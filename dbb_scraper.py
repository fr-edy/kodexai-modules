from dataclasses import field, dataclass
from datetime import datetime
import tls_client.response
from lxml import etree
from io import BytesIO
import tls_client
import logging
import time


# Constants
DATE_FORMAT_RSS = "%a, %d %b %Y %H:%M:%S %Z"
DATE_FORMAT_WEB = "%d.%m.%Y"
DEBUG = True
TIMEOUT_AFTER_SECONDS = 15
BUNDESBANK_BASE_URL = "https://www.bundesbank.de"


# Base scraping class
class BaseScraper:
    def __init__(self, id: str, debug: bool = False) -> None:
        self.debug = debug
        self.session = tls_client.Session("chrome_120")

        # TODO: implement headers from real chrome
        self.header_config = {
            "GET": {"order": [], "headers": {}},
            "RSS": {"order": [], "headers": {}},
            "PDF": {"order": [], "headers": {}},
        }

        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = logging.getLogger(id)
        self.session.timeout_seconds = TIMEOUT_AFTER_SECONDS

    def retry_wait(self, seconds: int = 2) -> None:
        time.sleep(seconds)

    def _request_get(
        self, url: str, config: str, expected: int = 200, retries: int = 0
    ) -> tls_client.response.Response:
        self.session.header_order = self.header_config[config]["order"]
        resp = self.session.get(url=url, headers=self.header_config[config]["headers"])

        if resp.status_code != expected:
            self.retry_wait()
            return self._request_get(
                url, config, expected=expected, retries=retries + 1
            )

        return resp

    def get_page(self, url: str) -> tls_client.response.Response:
        return self._request_get(url, "GET")

    def get_rss_feed(self, url: str):
        return self._request_get(url, "RSS")

    def download_file(self, url: str) -> BytesIO:
        config = "PDF" if url.endswith(".pdf") else "GET"
        resp = self._request_get(url, config)
        return resp.content


@dataclass
class Publication:
    web_title: str
    published_at: datetime
    web_url: str
    related_urls: list[str] = field(default_factory=list)


class BundesbankScraper(BaseScraper):
    def __init__(self, debug=False):
        super().__init__("dbb_scraper", debug=debug)
        self.base = BUNDESBANK_BASE_URL

    def load_rss_link(self, url: str) -> list[Publication]:
        rss_feed = self.get_rss_feed(url)
        # TODO: parse and return

    def load_web_link(self, url: str) -> list[Publication]:
        data = self.get_page(url)
        # TODO: parse and return


# Example usage
if __name__ == "__main__":
    s = BundesbankScraper(DEBUG)

    rss_pubs = s.load_rss_link(
        "https://www.bundesbank.de/service/rss/de/633286/feed.rss"
    )
    web_pubs = s.load_web_link("https://www.bundesbank.de/de/presse/stellungnahmen")
    pdf_bytes = s.download_file(
        "https://www.bundesbank.de/resource/blob/696204/ffdf2c3e5dc30961892a835482998453/472B63F073F071307366337C94F8C870/2016-01-11-ogaw-download.pdf"
    )
