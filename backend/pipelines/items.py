# File: /backend/pipelines/items.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class ProductItem:
    """Base item for scraped products"""
    title: str
    price: float
    currency: str = "USD"
    url: str = ""
    platform: str = ""
    description: Optional[str] = None
    images: List[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    specifications: Dict = None
    external_id: Optional[str] = None
    date_scraped: datetime = None

    def __post_init__(self):
        self.images = self.images or []
        self.specifications = self.specifications or {}
        self.date_scraped = self.date_scraped or datetime.now()

    def to_dict(self) -> dict:
        """Convert item to dictionary"""
        return {
            'title': self.title,
            'price': self.price,
            'currency': self.currency,
            'url': self.url,
            'platform': self.platform,
            'description': self.description,
            'images': self.images,
            'category': self.category,
            'brand': self.brand,
            'specifications': self.specifications,
            'external_id': self.external_id,
            'date_scraped': self.date_scraped.isoformat() if self.date_scraped else None
        }