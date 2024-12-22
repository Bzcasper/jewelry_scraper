from scrapy import Spider
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from typing import Dict, List, Optional, Callable
import asyncio
import logging
from datetime import datetime
from price_parser import Price
from .utils import Proxy
from .rate_limiter import RateLimiter
from .database.models import Product

class JewelrySpiderBase(Spider):
    """Base spider for jewelry scraping with enhanced capabilities"""
    
    name = 'jewelry_base'
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': True,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
    }

    def __init__(self, 
                 query: str,
                 max_items: int = 50,
                 filters: Optional[Dict] = None,
                 settings: Optional[Dict] = None):
        super().__init__()
        self.query = query
        self.max_items = max_items
        self.filters = filters or {}
        self.settings = settings or {}
        
        # Initialize counters and tracking
        self.items_scraped = 0
        self.errors = []
        self.start_time = datetime.now()
        
        # Set up components
        self.setup_logging()
        self.setup_selenium()
        self.rate_limiter = RateLimiter()
        self.progress_callback = None

    def setup_logging(self):
        """Initialize logging"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        fh = logging.FileHandler(f"logs/{self.name}_{datetime.now():%Y%m%d}.log")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def setup_selenium(self):
        """Initialize Selenium with anti-detection measures"""
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Add stealth settings
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Execute stealth script
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.progress_callback = callback

    async def scrape_with_selenium(self, url: str) -> Optional[str]:
        """Scrape page using Selenium with retry logic"""
        for attempt in range(3):
            try:
                await self.rate_limiter.wait()
                
                self.driver.get(url)
                
                # Wait for main content
                self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Scroll to load dynamic content
                self.scroll_page()
                
                # Wait for specific elements based on platform
                self.wait_for_platform_elements()
                
                return self.driver.page_source
                
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {url}: {str(e)}"
                )
                if attempt == 2:
                    self.errors.append(f"Failed to scrape {url}: {str(e)}")
                    return None
                await asyncio.sleep(attempt + 1)

    def scroll_page(self):
        """Scroll page to trigger lazy loading"""
        prev_height = 0
        for _ in range(3):
            # Scroll down
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            
            # Wait for content to load
            self.wait_for_content_load()
            
            # Check if we've reached the bottom
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            if new_height == prev_height:
                break
            prev_height = new_height

    def wait_for_content_load(self):
        """Wait for dynamic content to load"""
        try:
            # Wait for network to be idle
            self.driver.execute_script(
                "return new Promise(resolve => {"
                "  if (document.readyState === 'complete') resolve();"
                "  window.addEventListener('load', resolve);"
                "});"
            )
            
            # Additional wait for any animations
            self.wait.until(
                lambda d: d.execute_script(
                    "return document.readyState === 'complete' "
                    "&& !document.querySelector('.loading')"
                )
            )
        except TimeoutException:
            self.logger.warning("Timeout waiting for content load")

    def extract_price(self, price_str: Optional[str]) -> Dict:
        """Extract standardized price information"""
        if not price_str:
            return {'amount': None, 'currency': None}
            
        price = Price.fromstring(price_str)
        return {
            'amount': float(price.amount) if price.amount else None,
            'currency': price.currency or 'USD'
        }

    def create_product(self, data: Dict) -> Product:
        """Create standardized product object"""
        price_info = self.extract_price(data.get('price_str'))
        
        return Product(
            title=data.get('title', '').strip(),
            price_amount=price_info['amount'],
            price_currency=price_info['currency'],
            description=data.get('description', '').strip(),
            platform=self.name,
            category=data.get('category'),
            brand=data.get('brand'),
            specifications=data.get('specifications', {}),
            seller_info=data.get('seller_info', {}),
            external_id=data.get('external_id'),
            product_url=data.get('url'),
            date_scraped=datetime.now()
        )

    def update_progress(self, stats: Dict):
        """Update scraping progress"""
        if self.progress_callback:
            self.progress_callback({
                'items_scraped': self.items_scraped,
                'errors': len(self.errors),
                'duration': (datetime.now() - self.start_time).total_seconds(),
                **stats
            })

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()