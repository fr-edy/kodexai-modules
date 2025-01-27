import logging
import unicodedata
from datetime import datetime
from urllib.parse import urljoin

from lxml.etree import HTML

from models import Regulators, RegUpdateTypes, RegulatorPublication
from utils import load_page_content

log = logging.getLogger(__name__)

REGULATOR = Regulators.MAS


def load_publications(publications_url: str, updates_type: RegUpdateTypes) -> list[RegulatorPublication]:
    """Loads the last 10 publications from the MAS website and extracts the PDF links (regulations only)."""

    publications = []
    for publication in _load_last_publications(publications_url, updates_type):
        log.info(f"Processing {publication}")

        if updates_type == RegUpdateTypes.REGULATION:
            publication.related_urls += _get_related_links(publication.web_url)
            log.info(f"Found {len(publication.related_urls)} related links for {publication}")

        log.info(f"Scraped publication: {publication}")
        publications.append(publication)
    return publications


def _load_last_publications(url: str, updates_type: RegUpdateTypes) -> list[RegulatorPublication]:
    """Loads the last 10 publications (no pagination handling) from the MAS website.
    It parses the publications feed and scrapes the pub date, URL, title and opt focus area tag from the preview.
    Throws exceptions if something major goes wrong."""
    html = HTML(load_page_content(url))
    publications = html.xpath("//li[@class='mas-search-page__result']")
    log.info(f"Found {len(publications)} publication links on the MAS page {url}")

    parsed_publications = []
    for publication in publications:
        date_text_elements = publication.xpath(".//div[contains(@class, 'ts:xs') and contains(text(), 'Date:')]/text()")
        link_elements = publication.xpath(".//a[contains(@class, 'mas-link--no-underline')]/@href")
        title_elements = publication.xpath(
            ".//a[contains(@class, 'mas-link--no-underline')]" "/span[@class='mas-link__text']/text()"
        )
        category_elements = publication.xpath(".//div[contains(@class, 'mas-tag__text')]/text()")

        if not date_text_elements or not link_elements or not title_elements or not category_elements:
            log.warning(f"Skipping a publication due to missing data.")
            continue

        pub = RegulatorPublication(
            regulator=REGULATOR,
            type=updates_type,
            web_title=unicodedata.normalize("NFKC", title_elements[0].strip()),  # Correct the encoding
            published_at=datetime.strptime(date_text_elements[0].strip().split(": ")[1], "%d %B %Y"),
            web_url=urljoin(REGULATOR.base_url, link_elements[0].strip()),
            category=category_elements[0].strip(),
        )
        log.info(f"Scraped publication: {pub}")
        parsed_publications.append(pub)

    return parsed_publications


def _get_related_links(url: str) -> list[str]:
    """Extracts the related links (other articles and PDFs) from a MAS publication page."""
    html = HTML(load_page_content(url))
    related_link_elements = html.xpath("//a[contains(@href, '.pdf')]/@href")
    related_link_elements += html.xpath(
        "//div[contains(@class, 'related-to-this-regulation-listing--result')]"
        "//h1[contains(@class, 'mas-search-card__title')]/a/@href"
    )

    return [urljoin(REGULATOR.base_url, link.strip()) for link in related_link_elements]
