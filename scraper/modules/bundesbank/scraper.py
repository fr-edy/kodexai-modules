import base
from modules.bundesbank.parser import parse_rss_articles, parse_web_articles
from models.publication import Publication
from io import BytesIO
import logging

class BundesbankScraper(base.ScrapingFramework):
    """
    A scraper class for the Deutsche Bundesbank website.
    Handles RSS feeds and web article scraping.
    """

    def __init__(self):
        """
        Initialize the Bundesbank scraper with base configuration.
        Sets up logging and base URL for the Bundesbank website.
        """
        super().__init__("BundesbankScraper", False)
        # Replace print-based logger with proper logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized BundesbankScraper")
        self.base = "https://www.bundesbank.de"
        
    def load_rss_link(self, rss_url: str) -> list[Publication]:
        """
        Fetch and parse publications from an RSS feed.
        
        Args:
            rss_url (str): The URL of the RSS feed to scrape
            
        Returns:
            list[Publication]: List of parsed Publication objects
        """
        try:
            response = self.client.get(rss_url)
            publications = parse_rss_articles(response.content())
            return publications
        except Exception as e:
            self.logger.error(f"Error loading RSS feed from {rss_url}: {str(e)}")
            return []
    
    def download_file(self, file_url: str) -> BytesIO:
        """
        Download a file from the given URL.
        Handles both PDF and web article downloads.
        
        Args:
            file_url (str): URL of the file to download
            
        Returns:
            BytesIO: File content as bytes in memory
        """
        try:
            if not file_url.endswith(".pdf"):
                return self.download_article_page_as_pdf(file_url)
            
            response = self.client.get(file_url)
            return BytesIO(response.content())
        except Exception as e:
            self.logger.error(f"Error downloading file from {file_url}: {str(e)}")
            raise
        
    def load_web_link(self, web_url: str) -> list[Publication]:
        """
        Fetch and parse publications from a web page.
        
        Args:
            web_url (str): The URL of the web page to scrape
            
        Returns:
            list[Publication]: List of parsed Publication objects
        """
        try:
            response = self.client.get(web_url)
            publications = parse_web_articles(response.content())       
            return publications
        except Exception as e:
            self.logger.error(f"Error loading web page from {web_url}: {str(e)}")
            return []

    def download_article_page_as_pdf(self, article_url: str) -> BytesIO:
        """
        Download a web article and convert it to PDF format.
        
        Args:
            article_url (str): URL of the article to download
            
        Returns:
            BytesIO: PDF content as bytes in memory
        """
        try:
            response = self.client.get(article_url)
            return BytesIO(response.content())
        except Exception as e:
            self.logger.error(f"Error downloading article from {article_url}: {str(e)}")
            raise