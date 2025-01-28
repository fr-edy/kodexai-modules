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


def ecb_load_regulations():
    """
    Loads ECB regulations from their supervisory website.
    Note: Due to the lazy loading nature of the ECB website, this function needs to handle dynamic content loading.
    This function:
    1. Generates URLs for ECB regulation pages from 2013 to current year
    2. Scrapes publications from those pages
    3. Processes each found publication
    Args:
        None
    Returns:
        None
    Raises:
        Exception: If there's an error loading publications from ECB website
    """
    
    regulator = Regulators.ECB
    namespace = "ecb-regulations"
    updates_type = RegUpdateTypes.REGULATION
    regulation_links = [
        f"https://www.ecb.europa.eu/press/accounts/{year}/html/index_include.en.html"
        for year in range(2015, datetime.now().year + 1)
    ] # Reverse the list to start with the current year
    
    db_publications = ecb_scraper.load_publications_from_db(updates_type, amount_to_fetch=10) # https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Letters%20to%20MEPs
    log.info(f"Loaded {len(db_publications)} {regulator.value} {updates_type.value} items from the database")
    
        
    regulations = []
    regulations += db_publications
    
    for link in regulation_links:
        try:
            regulations += ecb_scraper.load_publications(link, updates_type=updates_type)
            log.info(f"Found {len(regulations)} {regulator.value} {updates_type.value} items")
        except Exception as e:
            log.error(f"Failed to load {regulator.value} {updates_type.value} from {link}", exc_info=e)
            continue

    for publication in regulations:
        process_publication(publication, namespace)

def ecb_load_news():
    
    # scrape https://www.ecb.europa.eu/press/stats/paysec/html/index.en.html with load_publications
    # load https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Press%20release with load_publications_from_db

    regulator = Regulators.ECB
    namespace = "ecb-news"
    updates_type = RegUpdateTypes.NEWS
    regulation_links = [
      "https://www.ecb.europa.eu/press/stats/paysec/html/index.en.html"
    ] 
    
    db_publications = ecb_scraper.load_publications_from_db(updates_type, amount_to_fetch=10) # https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Letters%20to%20MEPs
    log.info(f"Loaded {len(db_publications)} {regulator.value} {updates_type.value} items from the database")
    
        
    regulations = []
    regulations += db_publications
    
    for link in regulation_links:
        try:
            regulations += ecb_scraper.load_publications(link, updates_type=updates_type)
            log.info(f"Found {len(regulations)} {regulator.value} {updates_type.value} items")
        except Exception as e:
            log.error(f"Failed to load {regulator.value} {updates_type.value} from {link}", exc_info=e)
            continue

    for publication in regulations:
        process_publication(publication, namespace)


def process_publication(publication: RegulatorPublication, namespace: str):
    """Dummy method to imitate the real flow."""
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ecb_load_regulations()
    ecb_load_news()