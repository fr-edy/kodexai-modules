from models.publication import Publication # might be wrong import path
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from io import BytesIO
import pdfkit

def fix_url(url: str) -> str:
    """
    Fix the URL if it is not absolute.
    """
    if url.startswith('http'):
        return url
    return f'https://www.bundesbank.de{url}'


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

    soup = BeautifulSoup(content, 'lxml')
    publications = []
    
    # Find all articles in the collection items
    articles = soup.select('#main-content .collection__items .teasable')
    
    for article in articles:
        # Extract link and title
        link_elem = article.select_one('.teasable__link')
        if not link_elem:
            continue
            
        link = fix_url(link_elem.get('href'))
        title_elem = article.select_one('.teasable__title--marked')
        web_title = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract description and parse date
        description = article.select_one('.teasable__text p')
        if description:
            description_text = description.get_text(strip=True)
            try:
                date_str = description_text.split(':')[0].strip()
                published_at = datetime.strptime(date_str, '%d.%m.%Y')
            except (ValueError, IndexError):
                published_at = None
        else:
            published_at = None
            
        # Get related URLs
        related_urls = [fix_url(link)] if link else []
        
        if web_title and link:
            publications.append(Publication(
                web_title=web_title,
                web_url=link,
                published_at=published_at,
                related_urls=related_urls
            ))
    
    return publications

def convert_article_to_pdf(content: str) -> BytesIO:
    """
    Convert HTML content to PDF, extracting only the main content.
    Returns a BytesIO object containing the PDF.
    """
    
    # Parse the HTML and extract main content
    soup = BeautifulSoup(content, 'lxml')
    main_content = soup.select_one('.main')
    
    if not main_content:
        raise ValueError("Could not find main content in HTML")
    
    # Configure pdfkit options
    options = {
        'quiet': True,
        'encoding': 'UTF-8'
    }
    
    # Convert to PDF
    pdf = pdfkit.from_string(str(main_content), False, options=options)
    
    # Create BytesIO object and write PDF to it
    pdf_buffer = BytesIO(pdf)
    return pdf_buffer