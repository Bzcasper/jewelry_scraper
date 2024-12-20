import asyncio
import logging
import re
from datetime import datetime
from typing import Callable, Dict, List, Optional

from dataclasses import dataclass
from price_parser import Price
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc

from ..database.models import Product
from ..utils.proxy import Proxy
from ..utils.rate_limiter import RateLimiter
from scrapy import Spider


@dataclass
class JewelrySpiderConfig:
    """Configuration for jewelry spider scraping parameters"""
    query: str
    max_items: int = 50
    filters: Optional[Dict] = None
    settings: Optional[Dict] = None


class JewelrySpiderBase(Spider):
    """Base spider for jewelry scraping with Selenium support"""
    
    name = "jewelry_base"
    custom_settings = {
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 2,
        "COOKIES_ENABLED": True,
        "ROBOTSTXT_OBEY": True,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
    }

    def __init__(self, config: JewelrySpiderConfig):
        super().__init__()
        self.query = config.query
        self.max_items = config.max_items
        self.filters = config.filters or {}
        self.settings = config.settings or {}

        # Tracking
        self.items_scraped = 0
        self.errors = []
        self.start_time = datetime.now()

        # Setup components
        self._setup_logging()
        self._setup_selenium()
        self.rate_limiter = RateLimiter()
        self.progress_callback = None

    def _setup_logging(self):
        """Initialize logger for the spider."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)

        # File handler for logs
        fh = logging.FileHandler(f"logs/{self.name}_{datetime.now():%Y%m%d}.log")
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def _setup_selenium(self):
        """Initialize Selenium WebDriver with undetected Chrome."""
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

        # Execute stealth measures
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

    def set_progress_callback(self, callback: Callable):
        """Set a callback to track progress during scraping."""
        self.progress_callback = callback

    async def scrape_with_selenium(self, url: str) -> Optional[str]:
        """Scrape a page using Selenium with retries."""
        for attempt in range(3):
            try:
                await self.rate_limiter.wait()
                self.driver.get(url)

                # Wait for the body tag to load
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                # Scroll the page to load dynamic content
                self._scroll_page()

                return self.driver.page_source
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == 2:
                    self.errors.append(f"Failed to scrape {url}: {e}")
                    return None
                await asyncio.sleep(attempt + 1)

    def _scroll_page(self):
        """Scroll to the bottom of the page to trigger lazy loading."""
        prev_height = 0
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Allow time for content to load

            # Check if the page height has changed
            new_height = self.driver.execute_script("return document.body.scrollHeight;")
            if new_height == prev_height:
                break
            prev_height = new_height

    def extract_price(self, price_str: Optional[str]) -> Dict:
        """Extract price and currency from a string."""
        if not price_str:
            return {"amount": None, "currency": None}
        price = Price.fromstring(price_str)
        return {"amount": price.amount, "currency": price.currency}

    def create_product(self, data: Dict) -> Product:
        """Create a Product object from scraped data."""
        price_info = self.extract_price(data.get("price_str"))
        return Product(
            title=data.get("title", "").strip(),
            price_amount=price_info["amount"],
            price_currency=price_info["currency"],
            description=data.get("description", "").strip(),
            platform=self.name,
            category=data.get("category"),
            brand=data.get("brand"),
            specifications=data.get("specifications", {}),
            seller_info=data.get("seller_info", {}),
            external_id=data.get("external_id"),
            product_url=data.get("url"),
            date_scraped=datetime.now(),
        )

    def update_progress(self, stats: Dict):
        """Update the scraping progress."""
        if self.progress_callback:
            self.progress_callback({
                "items_scraped": self.items_scraped,
                "errors": len(self.errors),
                "duration": (datetime.now() - self.start_time).total_seconds(),
                **stats
            })

    def close(self):
        """Clean up resources."""
        if hasattr(self, "driver"):
            self.driver.quit()
