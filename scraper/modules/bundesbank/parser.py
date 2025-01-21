"""
Bundesbank Article Parser Module
Handles parsing of RSS feeds and web articles from Bundesbank website.

Author: Your Name
Date: YYYY-MM-DD
"""

import logging
from typing import Optional, List
from datetime import datetime
from io import BytesIO
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pdfkit
from models.publication import Publication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BUNDESBANK_BASE_URL = 'https://www.bundesbank.de'
DATE_FORMAT_RSS = '%a, %d %b %Y %H:%M:%S %Z'
DATE_FORMAT_WEB = '%d.%m.%Y'

class ParserException(Exception):
    """Custom exception for parser-related errors."""
    pass

def fix_url(url: str) -> str:
    """
    Ensure URL is absolute by adding base URL if necessary.
    
    Args:
        url (str): The URL to fix
        
    Returns:
        str: The absolute URL
    """
    return url if url.startswith('http') else f'{BUNDESBANK_BASE_URL}{url}'

def parse_rss_articles(content: str) -> List[Publication]:
    """
    Parse RSS feed content and extract articles.
    
    Args:
        content (str): Raw RSS XML content
        
    Returns:
        List[Publication]: List of parsed Publication objects
        
    Raises:
        ParserException: If RSS parsing fails
    """
    try:
        root = ET.fromstring(content)
        publications = []
        
        for item in root.findall('.//item'):
            try:
                title = item.find('title').text
                link = item.find('link').text
                published_at = item.find('pubDate').text
                
                # Get enclosure URL if available
                enclosure = item.find("enclosure")
                related_urls = [enclosure.get("url")] if enclosure is not None else []
                
                published_at_datetime = datetime.strptime(published_at, DATE_FORMAT_RSS)
                
                publications.append(Publication(
                    web_title=title,
                    web_url=link,
                    published_at=published_at_datetime,
                    related_urls=related_urls
                ))
                
            except (AttributeError, ValueError) as e:
                logger.warning(f"Failed to parse RSS item: {str(e)}")
                continue
                
        return publications
        
    except ET.ParseError as e:
        raise ParserException(f"Failed to parse RSS content: {str(e)}")

def parse_web_articles(content: str) -> List[Publication]:
    """
    Parse web page content and extract articles.
    
    Args:
        content (str): Raw HTML content
        
    Returns:
        List[Publication]: List of parsed Publication objects
        
    Raises:
        ParserException: If HTML parsing fails
    """
    try:
        soup = BeautifulSoup(content, 'lxml')
        publications = []
        
        articles = soup.select('#main-content .collection__items .teasable')
        
        for article in articles:
            try:
                # Extract required elements
                link_elem = article.select_one('.teasable__link')
                if not link_elem:
                    continue
                    
                link = fix_url(link_elem.get('href'))
                title_elem = article.select_one('.teasable__title--marked')
                web_title = title_elem.get_text(strip=True) if title_elem else None
                
                # Parse publication date
                published_at = None
                description = article.select_one('.teasable__text p')
                if description:
                    description_text = description.get_text(strip=True)
                    try:
                        date_str = description_text.split(':')[0].strip()
                        published_at = datetime.strptime(date_str, DATE_FORMAT_WEB)
                    except (ValueError, IndexError):
                        logger.warning(f"Failed to parse date from: {description_text}")
                
                if web_title and link:
                    publications.append(Publication(
                        web_title=web_title,
                        web_url=link,
                        published_at=published_at,
                        related_urls=[link]
                    ))
                    
            except Exception as e:
                logger.warning(f"Failed to parse article: {str(e)}")
                continue
                
        return publications
        
    except Exception as e:
        raise ParserException(f"Failed to parse web content: {str(e)}")

def convert_article_to_pdf(content: str) -> BytesIO:
    """
    Convert article HTML content to PDF format.
    
    Args:
        content (str): HTML content to convert
        
    Returns:
        BytesIO: PDF content as bytes buffer
        
    Raises:
        ParserException: If PDF conversion fails
    """
    try:
        soup = BeautifulSoup(content, 'lxml')
        main_content = soup.select_one('.main')
        
        if not main_content:
            raise ParserException("Main content section not found in HTML")
        
        options = {
            'quiet': True,
            'encoding': 'UTF-8',
            'enable-local-file-access': True
        }
        
        pdf = pdfkit.from_string(str(main_content), False, options=options)
        return BytesIO(pdf)
        
    except Exception as e:
        raise ParserException(f"PDF conversion failed: {str(e)}")