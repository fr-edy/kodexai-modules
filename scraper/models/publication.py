from dataclasses import field, dataclass
from datetime import datetime

@dataclass
class Publication:
    web_title: str
    published_at: datetime
    web_url: str
    related_urls: list[str] = field(default_factory=list)
    
    def __init__(self, web_title: str, published_at: datetime, web_url: str, related_urls: list[str] = []):
        self.web_title = web_title
        self.published_at = published_at
        self.web_url = web_url
        self.related_urls = related_urls

    def json(self) -> dict:
        return {
            "web_title": self.web_title,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "web_url": self.web_url,
            "related_urls": self.related_urls
        }