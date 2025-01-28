import logging
# import mas_scraper
import ecb_scraper
from models import RegulatorPublication, Regulators, RegUpdateTypes
from datetime import datetime

log = logging.getLogger(__name__)


# def mas_load_regulations():
#     """Method is given as an example for reference."""
#     regulator = Regulators.MAS
#     namespace = "mas-regulations"
#     updates_type = RegUpdateTypes.REGULATION
#     regulations_link = (  # Page 1, sorted by date DESC, all except for annual and sustainability reports
#         "https://www.mas.gov.sg/publications?page=1&sort=mas_date_tdt%20desc"
#         "&content_type=Financial%20Stability%20Reviews&content_type=Recent%20Economic%20Developments"
#         "&content_type=FATF%20Statement&content_type=Macroeconomic%20Reviews&content_type=Staff%20Papers"
#         "&content_type=Money%20and%20Banking%20Monthly%20Statistical%20Bulletin&content_type=Economic%20Essays"
#         "&content_type=Monographs%2FInformation%20Papers&content_type=Consultations"
#     )

#     try:
#         regulations = mas_scraper.load_publications(regulations_link, updates_type=updates_type)
#         log.info(f"Found {len(regulations)} {regulator.value} {updates_type.value} items")
#     except Exception as e:
#         log.error(f"Failed to load {regulator.value} {updates_type.value}", exc_info=e)
#         return

#     for publication in regulations:
#         process_publication(publication, namespace)


# def mas_load_news():
#     """Method is given as an example for reference."""
#     regulator = Regulators.MAS
#     namespace = "mas-news"
#     updates_type = RegUpdateTypes.NEWS
#     news_links = [
#         # Page 1, sorted by date DESC, link per sector, all sectors except for Insurance
#         "https://www.mas.gov.sg/news?page=1&sort=mas_date_tdt%20desc&sectors=Capital%20Markets",
#         "https://www.mas.gov.sg/news?page=1&sort=mas_date_tdt%20desc&sectors=Banking",
#         "https://www.mas.gov.sg/news?page=1&sort=mas_date_tdt%20desc&sectors=Payments",
#     ]

#     news: list[RegulatorPublication] = []
#     for link in news_links:
#         try:
#             news += mas_scraper.load_publications(link, updates_type=updates_type)
#             log.info(f"Found {len(news)} {regulator.value} {updates_type.value} items")
#         except Exception as e:
#             log.error(f"Failed to load {regulator.value} {updates_type.value} from {link}", exc_info=e)
#             continue

#     for publication in news:
#         process_publication(publication, namespace)


def _load_ecb_content(content_type: RegUpdateTypes, namespace: str, urls: list[str], db_fetch_amount: int = 10):
    """
    Generic function to load ECB content (regulations or news)
    
    Args:
        content_type: Type of content to load (REGULATION or NEWS)
        namespace: Namespace for processing
        urls: List of URLs to scrape
        db_fetch_amount: Number of items to fetch from database
    """
    regulator = Regulators.ECB
    
    # Load from database first
    publications = ecb_scraper.load_publications_from_db(content_type, amount_to_fetch=db_fetch_amount)
    log.info(f"Loaded {len(publications)} {regulator.value} {content_type.value} items from database")
    
    # Load from web pages
    for url in urls:
        try:
            publications += ecb_scraper.load_publications(url, updates_type=content_type)
            log.info(f"Found {len(publications)} {regulator.value} {content_type.value} items")
        except Exception as e:
            log.error(f"Failed to load {regulator.value} {content_type.value} from {url}", exc_info=e)
            continue

    # Process all publications
    for publication in publications:
        process_publication(publication, namespace)

def ecb_load_regulations():
    """
    Loads ECB regulations from their supervisory website.
    Handles dynamic content loading from 2015 to current year.
    """
    regulation_urls = [
        f"https://www.ecb.europa.eu/press/accounts/{year}/html/index_include.en.html"
        for year in range(2015, datetime.now().year + 1)
    ]
    
    _load_ecb_content(
        content_type=RegUpdateTypes.REGULATION,
        namespace="ecb-regulations",
        urls=regulation_urls
    )

def ecb_load_news():
    """Loads ECB news from their website."""
    news_urls = ["https://www.ecb.europa.eu/press/stats/paysec/html/index.en.html"]
    
    _load_ecb_content(
        content_type=RegUpdateTypes.NEWS,
        namespace="ecb-news",
        urls=news_urls
    )


def process_publication(publication: RegulatorPublication, namespace: str):
    """Dummy method to imitate the real flow."""
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ecb_load_regulations()
    ecb_load_news()