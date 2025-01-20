from bs4 import BeautifulSoup
from typing import Optional, Union, List


class HTMLParser:
        
    def __init__(self, data: str):
        if not data:
            raise ValueError("Empty HTML content.")
        
        self._data = data
        self._parse()
        
    def _parse(self) -> 'HTMLParser':
        self._soup = BeautifulSoup(self._data, 'html.parser')
        return self
    
    def find(self, tag: str, attrs: Optional[dict] = None) -> Optional[BeautifulSoup]:
        if self._soup is None:
            raise ValueError("HTML content not parsed. Call parse() before find().")
        return self._soup.find(tag, attrs)
        
    def find_all(self, tag: str, attrs: Optional[dict] = None) -> List[BeautifulSoup]:
        if self._soup is None:
            raise ValueError("HTML content not parsed. Call parse() before find_all().")
        return self._soup.find_all(tag, attrs)
    
    def get_text(self) -> str:
        if self._soup is None:
            raise ValueError("HTML content not parsed. Call parse() before get_text().")
        return self._soup.get_text()
    
    def get(self) -> BeautifulSoup:
        if self._soup is None:
            raise ValueError("HTML content not parsed. Call parse() before get().")
        return self._soup