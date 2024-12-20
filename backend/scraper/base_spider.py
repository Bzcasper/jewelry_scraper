```python
from scrapy import Spider
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from price_parser import Price
from typing import Optional, Dict, List
from datetime import datetime
import json

class JewelrySpiderBase(Spider):
    """Base spider with shared functionality for jewelry scraping"""
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 3,
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_TIMEOUT': 20,
        'SELENIUM_DRIVER_NAME': 'chrome',
        'SELENIUM_DRIVER_ARGUMENTS': ['--headless', '--no-sandbox']
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_selenium()
        self.items_scraped = 0
        self.errors = []

    def setup_selenium(self):
        """Initialize Selenium for dynamic content"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def parse_price(self, price_str: Optional[str]) -> Dict:
        """Parse price string into structured format"""
        if not price_str:
            return {'amount': None, 'currency': None}
        
        price = Price.fromstring(price_str)
        return {
            'amount': float(price.amount) if price.amount else None,
            'currency': price.currency or 'USD'
        }

    def clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text content"""
        if not text:
            return ''
        return ' '.join(text.strip().split())

    def extract_structured_data(self, response) -> Optional[Dict]:
        """Extract structured data from page if available"""
        try:
            # Look for JSON-LD data
            json_ld = response.css('script[type="application/ld+json"]::text').get()
            if json_ld:
                return json.loads(json_ld)
            
            # Look for microdata
            microdata = {}
            for elem in response.css('[itemtype]'):
                prop = elem.css('[itemprop]::attr(content)').get()
                if prop:
                    microdata[elem.css('[itemprop]::attr(itemprop)').get()] = prop
            return microdata or None
        except Exception as e:
            logging.error(f"Error extracting structured data: {e}")
            return None

    def extract_specifications(self, response) -> Dict:
        """Extract product specifications"""
        specs = {}
        spec_rows = response.css('table.product-specs tr')
        for row in spec_rows:
            key = self.clean_text(row.css('th::text').get())
            value = self.clean_text(row.css('td::text').get())
            if key and value:
                specs[key] = value
        return specs

    def download_images(self, urls: List[str], product_id: str):
        """Download and store product images"""
        from PIL import Image
import requests
from pathlib import Path
import hashlib

        image_dir = Path('product_images')
        image_dir.mkdir(exist_ok=True)

        saved_images = []
        for i, url in enumerate(urls):
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    # Create unique filename
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    filename = f"{product_id}_{url_hash}_{i}.jpg"
                    filepath = image_dir / filename

                    # Save and optimize image
                    with Image.open(response.raw) as img:
                        # Convert to RGB if necessary
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        # Resize if too large
                        if max(img.size) > 1200:
                            img.thumbnail((1200, 1200))
                        # Save with optimization
                        img.save(filepath, 'JPEG', quality=85, optimize=True)
                    
                    saved_images.append(str(filepath))
            except Exception as e:
                logging.error(f"Error downloading image {url}: {e}")

        return saved_images

    def extract_common_data(self, response) -> Dict:
        """Extract common data fields from response"""
        structured_data = self.extract_structured_data(response)
        
        data = {
            'url': response.url,
            'title': self.clean_text(response.css('h1::text').get()),
            'description': self.clean_text(response.css('.description::text').get()),
            'specifications': self.extract_specifications(response),
            'structured_data': structured_data,
            'date_scraped': datetime.now().isoformat()
        }

        # Try to get price from structured data first
        if structured_data and 'offers' in structured_data:
            price_str = structured_data['offers'].get('price')
            data['price'] = self.parse_price(price_str)
        
        return data

    def closed(self, reason):
        """Cleanup when spider closes"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        
        # Log scraping summary
        logging.info(
            f"Spider closed. Items scraped: {self.items_scraped}, "
            f"Errors: {len(self.errors)}"
        )