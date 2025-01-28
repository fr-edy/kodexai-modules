import logging

# import mas_scraper
import ecb_scraper
from models import RegulatorPublication, Regulators, RegUpdateTypes
from datetime import datetime

log = logging.getLogger(__name__)


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
    ]  # Reverse the list to start with the current year

    # https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Letters%20to%20MEPs
    db_publications = ecb_scraper.load_publications_from_db(
        updates_type, amount_to_fetch=10
    )
    log.info(
        f"Loaded {len(db_publications)} {regulator.value} {updates_type.value} items from the database"
    )

    regulations = []
    regulations += db_publications

    for link in regulation_links:
        try:
            regulations += ecb_scraper.load_publications(
                link, updates_type=updates_type
            )
            log.info(
                f"Found {len(regulations)} {regulator.value} {updates_type.value} items"
            )
        except Exception as e:
            log.error(
                f"Failed to load {regulator.value} {updates_type.value} from {link}",
                exc_info=e,
            )
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

    db_publications = ecb_scraper.load_publications_from_db(
        updates_type, amount_to_fetch=10
    )  # https://www.ecb.europa.eu/press/pubbydate/html/index.en.html?name_of_publication=Letters%20to%20MEPs
    log.info(
        f"Loaded {len(db_publications)} {regulator.value} {updates_type.value} items from the database"
    )

    regulations = []
    regulations += db_publications

    for link in regulation_links:
        try:
            regulations += ecb_scraper.load_publications(
                link, updates_type=updates_type
            )
            log.info(
                f"Found {len(regulations)} {regulator.value} {updates_type.value} items"
            )
        except Exception as e:
            log.error(
                f"Failed to load {regulator.value} {updates_type.value} from {link}",
                exc_info=e,
            )
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
