import logging
import unicodedata
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Dict
from lxml.etree import HTML
from models import Regulators, RegUpdateTypes, RegulatorPublication
from utils import load_page_content


log = logging.getLogger(__name__)


def load_last_publications(
    url: str, updates_type: RegUpdateTypes, lazy_load: bool = False
) -> List[RegulatorPublication]:
    """Loads and parses the most recent publications from the ECB website."""
    if lazy_load:
        return _load_last_publications_lazy_loaded(url, updates_type)
    else:
        return _load_last_publications_server_side_rendered(url, updates_type)


def _load_last_publications_server_side_rendered(
    url: str, updates_type: RegUpdateTypes
) -> List[RegulatorPublication]:
    """Loads and parses the most recent publications from the ECB website."""
    try:
        resp_text = load_page_content(
            url,
            params={
                "block_resources": True,
                "wait": 0,
            },
        )

        return _parse_publications(resp_text, updates_type)
    except Exception as e:
        log.error(f"Error loading server side rendered publications: {str(e)}")
        return []


def _load_last_publications_lazy_loaded(
    url: str, updates_type: RegUpdateTypes
) -> List[RegulatorPublication]:
    """Loads and parses the most recent publications from the ECB website."""
    try:
        resp_text = load_page_content(
            url,
            params={
            "block_resources": True,
            "render_js": True,
            "wait_for": '//*[@id="main-wrapper"]//dl/dd[10]', # Wait for the 10 publications to load
            "window_width": 1920,
            "window_height": 1080,
            },
        )
        return _parse_publications(resp_text, updates_type)
    except Exception as e:
        log.error(f"Error loading lazy loaded publications: {str(e)}")
        return []


def _parse_publications(text: str, type: RegUpdateTypes) -> List[RegulatorPublication]:
    """Parses the ECB publications from the text content."""

    html = HTML(text)
    parsed_publications = []
    for dt, dd in zip(html.xpath(".//dt"), html.xpath(".//dd")):
        date_text = dt.xpath(".//text()")[0].strip()
        title_element = dd.xpath(".//a")
        title_text = title_element[0].text.strip()
        web_url = urljoin(Regulators.ECB.base_url, title_element[0].get("href"))
        related_urls = _filter_related_urls([
            urljoin(Regulators.ECB.base_url, href.strip())
            for href in dd.xpath(".//dl//a/@href")
        ])
        
        publication = RegulatorPublication(
            web_title=unicodedata.normalize("NFKC", title_text),
            published_at=datetime.strptime(date_text, "%d %B %Y"),
            web_url=web_url,
            related_urls=related_urls,
            regulator=Regulators.ECB,
            type=type,
        )
        parsed_publications.append(publication)

    if len(parsed_publications) < 10:
        log.warning(f"Found only {len(parsed_publications)} publications")

    log.info(f"Found {len(parsed_publications)} publications")
    return parsed_publications

def _filter_related_urls(urls: List[str]) -> List[str]:
    """Filter related URLs to only include unique English (.en.) version and remove duplicate urls.

    e.g. 
    this also filtered out as duplicates because the url query params are different but the content is the same:
        https://www.ecb.europa.eu/press/pdf/pis/ecb.pis231109_annex~f2f3134380.en.pdf
        https://www.ecb.europa.eu/press/pdf/pis/ecb.pis231109_annex~f2f3134380.en.pdf?60b65716cffd0fe791dec61726de5898
    """
    clean_urls = set()
    for url in urls:
        # Remove query parameters if present
        clean_url = url.split('?')[0]
        if '.en.' in clean_url:
            clean_urls.add(clean_url)
    return list(clean_urls)