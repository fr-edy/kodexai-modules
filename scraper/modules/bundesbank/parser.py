"""
Bundesbank Article Parser Module
Handles parsing of RSS feeds and web articles from Bundesbank website.

Author: Your Name
Date: YYYY-MM-DD
"""

import logging
from typing import Optional, List
import pdfkit
from datetime import datetime
from io import BytesIO
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from models.publication import Publication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BUNDESBANK_BASE_URL = "https://www.bundesbank.de"
DATE_FORMAT_RSS = "%a, %d %b %Y %H:%M:%S %Z"
DATE_FORMAT_WEB = "%d.%m.%Y"
