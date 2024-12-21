# File: /backend/utils/validators.py

from typing import Dict, Any, List, Optional
from decimal import Decimal
import re
from datetime import datetime
from pydantic import BaseModel, validator
from price_parser import Price

class ProductData(BaseModel):
    """Product data validation model"""
    title: str
    price: float
    currency: str = "USD"
    url: str
    platform: str
    description: Optional[str] = None
    images: List[str] = []
    category: Optional[str] = None
    brand: Optional[str] = None
    specifications: Dict[str, Any] = {}
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v.strip()

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(float(v), 2)

    @validator('url')
    def validate_url(cls, v):
        if not re.match(r'https?://\S+', v):
            raise ValueError("Invalid URL format")
        return v

    @validator('platform')
    def validate_platform(cls, v):
        valid_platforms = {'ebay', 'amazon'}
        if v.lower() not in valid_platforms:
            raise ValueError("Invalid platform")
        return v.lower()

class PriceParser:
    """Parse and normalize price data"""
    
    @staticmethod
    def parse(price_str: str) -> Optional[Dict[str, Any]]:
        """Parse price string into amount and currency"""
        if not price_str:
            return None

        price = Price.fromstring(price_str)
        if not price.amount:
            return None

        return {
            'amount': float(price.amount),
            'currency': price.currency or 'USD'
        }

    @staticmethod
    def format(amount: float, currency: str = 'USD') -> str:
        """Format price for display"""
        return f"{currency} {amount:.2f}"

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text

def validate_image_url(url: str) -> bool:
    """Validate image URL format"""
    if not url:
        return False
        
    # Check URL format
    if not re.match(r'https?://\S+\.(jpg|jpeg|png|webp|gif)($|\?)', url.lower()):
        return False
        
    # Additional checks for specific platforms
    if 'ebay' in url:
        return bool(re.search(r'i\.ebayimg\.com', url))
    if 'amazon' in url:
        return bool(re.search(r'images(-\w+)?\.amazon\.com', url))
        
    return True

def transform_ebay_data(raw_data: Dict) -> Dict:
    """Transform eBay-specific data to common format"""
    return {
        'title': clean_text(raw_data.get('title', '')),
        'price': PriceParser.parse(raw_data.get('price', '')),
        'url': raw_data.get('url', ''),
        'platform': 'ebay',
        'description': clean_text(raw_data.get('description', '')),
        'images': [
            url for url in raw_data.get('images', [])
            if validate_image_url(url)
        ],
        'specifications': {
            k: clean_text(v)
            for k, v in raw_data.get('specifics', {}).items()
        }
    }

  def transform_amazon_data(raw_data: Dict) -> Dict:
        """Transform Amazon-specific data to common format"""
        return {
            'title': clean_text(raw_data.get('title', '')),
            'price': PriceParser.parse(raw_data.get('price', '')),
            'url': raw_data.get('url', ''),
            'platform': 'amazon',
            'description': clean_text(raw_data.get('description', '')),
            'images': [
                url for url in raw_data.get('images', [])
                if validate_image_url(url)
            ],
            'specifications': {
                k: clean_text(v)
                for k, v in raw_data.get('features', {}).items()
            },
            'brand': clean_text(raw_data.get('brand', '')),
            'category': clean_text(raw_data.get('category', '')),
            'is_prime': bool(raw_data.get('is_prime', False))
        }

class RequestValidator:
    """Validate and sanitize API requests"""
    
    @staticmethod
    def validate_pagination(page: int, per_page: int) -> tuple[int, int]:
        """Validate and normalize pagination parameters"""
        page = max(1, page)  # Minimum page is 1
        per_page = max(1, min(100, per_page))  # Limit items per page
        return page, per_page

    @staticmethod
    def validate_sort_params(sort_by: str, valid_fields: List[str]) -> tuple[str, bool]:
        """Validate sorting parameters"""
        # Extract direction from field name (e.g., -price for descending)
        desc = sort_by.startswith('-')
        field = sort_by[1:] if desc else sort_by

        # Validate sort field
        if field not in valid_fields:
            field = 'date_scraped'  # Default sort field
        
        return field, desc

    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Validate and parse date range"""
        try:
            start = datetime.fromisoformat(start_date) if start_date else None
            end = datetime.fromisoformat(end_date) if end_date else None
            
            if start and end and start > end:
                start, end = end, start  # Swap if wrong order
                
            return start, end
        except ValueError:
            return None, None

class ResponseFormatter:
    """Format API responses consistently"""
    
    @staticmethod
    def format_product_list(products: List[Dict], total: int, page: int, per_page: int) -> Dict:
        """Format paginated product list response"""
        return {
            'data': products,
            'meta': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1
            }
        }

    @staticmethod
    def format_error(error: str, code: str = 'ERROR', status: int = 400) -> Dict:
        """Format error response"""
        return {
            'error': {
                'message': error,
                'code': code,
                'status': status
            }
        }

    @staticmethod
    def format_success(data: Any = None, message: str = None) -> Dict:
        """Format success response"""
        response = {'success': True}
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
        return response