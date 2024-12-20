import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import aiohttp
import undetected_chromedriver as uc
from PIL import Image
from price_parser import Price
from scrapy import Spider
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..utils.image_processor import ImageProcessor
from ..utils.proxy_manager import ProxyManager
from ..utils.rate_limiter import RateLimiter

class JewelrySpiderBase(Spider):
    """Enhanced base spider for jewelry scraping with improved resilience"""
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 3,
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_TIMEOUT': 20,
        'SELENIUM_DRIVER_NAME': 'chrome',
        'SELENIUM_DRIVER_ARGUMENTS': [
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080'
        ],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_components()
        self.setup_selenium()
        self.initialize_tracking()

    def setup_components(self):
        """Initialize supporting components"""
        self.image_processor = ImageProcessor()
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter()
        self.logger = logging.getLogger(self.name)

    def setup_selenium(self):
        """Initialize undetected-selenium for dynamic content"""
        try:
            options = uc.ChromeOptions()
            for arg in self.custom_settings['SELENIUM_DRIVER_ARGUMENTS']:
                options.add_argument(arg)

            # Add anti-detection measures
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

        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium: {e}")
            raise

    def initialize_tracking(self):
        """Initialize tracking metrics"""
        self.stats = {
            'items_scraped': 0,
            'errors': [],
            'start_time': datetime.now(),
            'successful_requests': 0,
            'failed_requests': 0,
            'images_downloaded': 0
        }

    async def process_page(self, url: str) -> Optional[str]:
        """Process dynamic page content"""
        try:
            await self.rate_limiter.wait()
            
            self.driver.get(url)
            
            # Wait for main content
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load dynamic content
            self._scroll_page()
            
            # Wait for specific elements
            self._wait_for_elements()
            
            return self.driver.page_source

        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"Error processing page {url}: {e}")
            return None

    def _scroll_page(self):
        """Scroll page to trigger lazy loading"""
        try:
            last_height = 0
            for _ in range(3):
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                
                # Wait for content to load
                time.sleep(2)
                
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height

        except Exception as e:
            self.logger.warning(f"Error during page scroll: {e}")

    def _wait_for_elements(self):
        """Wait for critical page elements"""
        try:
            # Wait for images
            self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "img[src]")
                )
            )
            
            # Wait for prices
            self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "[class*='price']")
                )
            )

        except TimeoutException:
            self.logger.warning("Timeout waiting for page elements")

    async def extract_product_data(self, response) -> Dict:
        """Extract comprehensive product data"""
        try:
            # Get structured data
            structured_data = self._extract_structured_data(response)
            
            # Build base data
            data = {
                'url': response.url,
                'title': self._clean_text(response.css('h1::text').get()),
                'description': self._extract_description(response),
                'specifications': await self._extract_specifications(response),
                'structured_data': structured_data,
                'date_scraped': datetime.now().isoformat(),
                'platform': self.name
            }

            # Extract price
            data['price'] = self._extract_price(response, structured_data)
            
            # Extract images
            image_urls = await self._extract_image_urls(response)
            data['images'] = await self.image_processor.process_images(
                image_urls,
                str(hash(data['url']))
            )

            self.stats['items_scraped'] += 1
            return data

        except Exception as e:
            self.stats['errors'].append(str(e))
            self.logger.error(f"Error extracting product data: {e}")
            return None

    def _extract_structured_data(self, response) -> Optional[Dict]:
        """Extract and parse structured data"""
        try:
            # Try JSON-LD
            for script in response.css('script[type="application/ld+json"]::text'):
                try:
                    return json.loads(script.get())
                except json.JSONDecodeError:
                    continue

            # Try microdata
            microdata = {}
            for elem in response.css('[itemtype]'):
                prop = elem.css('[itemprop]::attr(content)').get()
                if prop:
                    key = elem.css('[itemprop]::attr(itemprop)').get()
                    microdata[key] = prop
            
            return microdata if microdata else None

        except Exception as e:
            self.logger.warning(f"Error extracting structured data: {e}")
            return None

    def _extract_price(self, response, structured_data: Optional[Dict] = None) -> Dict:
        """Extract and validate price information"""
        price_data = {'amount': None, 'currency': 'USD'}

        # Try structured data first
        if structured_data and 'offers' in structured_data:
            price_str = structured_data['offers'].get('price')
            if price_str:
                price = Price.fromstring(price_str)
                if price.amount:
                    price_data['amount'] = float(price.amount)
                    price_data['currency'] = price.currency or 'USD'
                    return price_data

        # Try common price selectors
        price_selectors = [
            '[class*="price"]::text',
            '[class*="cost"]::text',
            '[class*="amount"]::text'
        ]

        for selector in price_selectors:
            if price_elem := response.css(selector).get():
                price = Price.fromstring(price_elem)
                if price.amount:
                    price_data['amount'] = float(price.amount)
                    price_data['currency'] = price.currency or 'USD'
                    return price_data

        return price_data

    async def _extract_specifications(self, response) -> Dict:
        """Extract detailed product specifications"""
        specs = {}
        
        # Try multiple common specification selectors
        spec_selectors = [
            'table.specifications tr',
            'table.product-specs tr',
            'dl.product-details',
            '[class*="specification"]'
        ]

        for selector in spec_selectors:
            for elem in response.css(selector):
                key = self._clean_text(elem.css('th::text, dt::text').get())
                value = self._clean_text(elem.css('td::text, dd::text').get())
                if key and value:
                    specs[key.lower()] = value

        return specs

    def _clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text content"""
        if not text:
            return ''
        return ' '.join(text.strip().split())

    def closed(self, reason):
        """Handle spider closure and cleanup"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()

            # Generate report
            duration = datetime.now() - self.stats['start_time']
            report = {
                'duration': str(duration),
                'items_scraped': self.stats['items_scraped'],
                'success_rate': (
                    self.stats['successful_requests'] /
                    (self.stats['successful_requests'] + self.stats['failed_requests'])
                    if self.stats['successful_requests'] > 0 else 0
                ),
                'errors': self.stats['errors'],
                'images_downloaded': self.stats['images_downloaded']
            }

            self.logger.info(f"Spider closed. Report: {json.dumps(report, indent=2)}")

        except Exception as e:
            self.logger.error(f"Error during spider cleanup: {e}")