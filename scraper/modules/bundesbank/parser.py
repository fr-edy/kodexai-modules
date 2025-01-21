from models.publication import Publication # might be wrong import path
import xml.etree.ElementTree as ET
from datetime import datetime

def parse_web_articles(content) -> list[Publication]:
    """
    Parse the web articles from the text.
    """

def parse_rss_articles(content: str) -> list[Publication]:
    """
    Parse the RSS articles from the text.
    """
    root = ET.fromstring(content)
    publications = []
    
    def extract_text(element):
        if element is not None:
            return element.text
        return None
    
    items = root.findall('.//item')
    
    for item in items:
        title = extract_text(item.find('title'))
        link = extract_text(item.find('link'))
        #description = extract_text(item.find('description'))
        published_at = extract_text(item.find('pubDate'))
        related_urls = [item.find("enclosure").get("url")] if item.find("enclosure") != None else []
        # Mon, 20 Jan 2025 10:30:00 GMT parse as datetime
        published_at_datetime = datetime.strptime(published_at, '%a, %d %b %Y %H:%M:%S %Z')
        
        publications.append(Publication(web_title=title, web_url=link, published_at=published_at_datetime, related_urls=related_urls))
        
    return publications

    
    
def parse_web_articles(content) -> list[Publication]:
    """
    Parse the web articles from the text.
    """
    pass