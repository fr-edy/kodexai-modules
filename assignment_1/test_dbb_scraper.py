import pytest
from datetime import datetime, timedelta
import feedparser
from unittest.mock import Mock, patch
import requests

from dbb_scraper import (
    BaseScraper,
    BundesbankScraper,
    Publication,
    ValidationError,
    ParserException,
    TooManyRetries,
)


# Fixtures
@pytest.fixture
def base_scraper():
    return BaseScraper("test_scraper")


@pytest.fixture
def bundesbank_scraper():
    return BundesbankScraper()


@pytest.fixture
def sample_publication():
    return Publication(
        web_title="Test Publication",
        web_url="https://example.com/article",
        published_at=datetime.now(),
        related_urls=["https://example.com/related"],
    )


@pytest.fixture
def mock_response() -> Mock:
    mock = Mock(spec=requests.Response)
    mock.status_code = 200
    mock.text = "<html><body>Test content</body></html>"
    return mock


# Test Publication Class
class TestPublication:

    def test_valid_publication(self, sample_publication: Publication):
        assert isinstance(sample_publication, Publication)

    def test_invalid_title_length(self):
        with pytest.raises(ValidationError):
            Publication(
                web_title="a" * 501,
                web_url="https://example.com",
                published_at=datetime.now(),
            )

    def test_invalid_date_future(self):
        with pytest.raises(ValidationError):
            Publication(
                web_title="Test",
                web_url="https://example.com",
                published_at=datetime.now() + timedelta(days=2),
            )

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            Publication(
                web_title="Test", web_url="invalid-url", published_at=datetime.now()
            )


# Test BaseScraper Class
class TestBaseScraper:
    def test_initialization(self, base_scraper: BaseScraper):
        assert base_scraper.debug is False
        assert isinstance(base_scraper.session, requests.Session)

    @patch("requests.Session.request")
    def test_request_success(
        self,
        mock_request,
        base_scraper: BaseScraper,
        mock_response: requests.Response,
    ):
        mock_request.return_value = mock_response
        response = base_scraper._request("https://example.com", "GET", "GET")
        assert response.status_code == 200

    @patch("requests.Session.request")
    def test_request_retry(
        self, mock_request: requests.Response, base_scraper: BaseScraper
    ):
        mock_request.side_effect = requests.RequestException()
        with pytest.raises(TooManyRetries):
            base_scraper._request("https://example.com", "GET", "GET")


# Test BundesbankScraper Class
class TestBundesbankScraper:

    def test_parse_rss_articles_empty(self, bundesbank_scraper: BundesbankScraper):
        empty_feed = feedparser.FeedParserDict({"entries": []})
        with pytest.raises(ParserException):
            bundesbank_scraper.parse_rss_articles(empty_feed)

    def test_parse_rss_articles_valid(self, bundesbank_scraper: BundesbankScraper):
        mock_entry = feedparser.FeedParserDict(
            {
                "title": "Test Article",
                "link": "https://example.com/article",
                "published": "Wed, 22 Jan 2025 12:00:00 GMT",
                "enclosures": [],
                "description": "Description",
                "dc_date": "2025-01-22T12:00:00Z",
            }
        )
        feed = feedparser.FeedParserDict()
        feed["entries"] = [mock_entry]
        publications = bundesbank_scraper.parse_rss_articles(feed)
        assert len(publications) == 1
        assert publications[0].web_title == "Test Article"


# Integration Tests
@pytest.mark.integration
class TestIntegration:
    def test_full_web_scrape(self, bundesbank_scraper: BundesbankScraper) -> None:
        publications = bundesbank_scraper.load_web_link(
            "https://www.bundesbank.de/de/presse/stellungnahmen"
        )
        assert len(publications) > 0
        for pub in publications:
            assert isinstance(pub, Publication)

    def test_full_rss_scrape(self, bundesbank_scraper: BundesbankScraper) -> None:
        publications = bundesbank_scraper.load_rss_link(
            "https://www.bundesbank.de/service/rss/de/633286/feed.rss"
        )
        assert len(publications) > 0
        for pub in publications:
            assert isinstance(pub, Publication)


# Run tests with: pytest test_scraper.py -v
