import logging
import unicodedata
from datetime import datetime
from urllib.parse import urljoin

from lxml.etree import HTML

from models import Regulators, RegUpdateTypes, RegulatorPublication
from utils2 import load_page_content

log = logging.getLogger(__name__)

REGULATOR = Regulators.ECB

def load_publications(publications_url: str, updates_type: RegUpdateTypes) -> list[RegulatorPublication]:
    """Loads the last 10 publications from the ECB website and extracts the PDF links (regulations only)."""
    
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
    """Loads and parses the most recent publications from the ECB website.
    
    Args:
        url: The URL to fetch publications from
        updates_type: Type of regulatory updates to process
        
    Returns:
        List of RegulatorPublication objects
    """
    html = HTML(load_page_content(url))
    parsed_publications = []
    
    # Get matching dt/dd pairs that contain publication info
    for dt, dd in zip(html.xpath(".//dt"), html.xpath(".//dd")):
        # Extract core publication data
        date_text = dt.xpath(".//text()")[0].strip()
        title_element = dd.xpath(".//a")
        title_text = title_element[0].text.strip()
        web_url = urljoin(REGULATOR.base_url, title_element[0].get('href'))

        # Get any PDF links from the description
        related_urls = [
            urljoin(REGULATOR.base_url, href.strip())
            for href in dd.xpath(".//dl//a/@href")
        ]

        # Create publication object with normalized text
        publication = RegulatorPublication(
            regulator=REGULATOR,
            type=updates_type,
            web_title=unicodedata.normalize("NFKC", title_text),
            published_at=datetime.strptime(date_text, "%d %B %Y"),
            web_url=web_url,
            category="",
            related_urls=related_urls
        )
        parsed_publications.append(publication)
    
    log.info(f"Found {len(parsed_publications)} publication links on the ECB page {url}")
    return parsed_publications

def _get_related_links(publication_url: str) -> list[str]:
    """Extracts the PDF links from the publication page."""
    # html = HTML(load_page_content(publication_url))
    # pdf_links = html.xpath("//a[contains(@href, '.pdf')]/@href")
    
    # return [urljoin(REGULATOR.base_url, link) for link in pdf_links]

    return []