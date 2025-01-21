import base
from modules.bundesbank.parser import parse_rss_articles
from models.publication import Publication

class BundesbankScraper(base.ScrapingFramework):
    # TODO Replace logger with 'logging' library
    def __init__(self):
        super().__init__("BundesbankScraper", False)
        self.logger.info("Initialized")
        self.base = "https://www.bundesbank.de"
        
    def load_rss_link(self, rss_url:str) -> list[Publication]:
        response = self.client.get(rss_url)
        publications = parse_rss_articles(response._response.content)
        return publications
        
    

