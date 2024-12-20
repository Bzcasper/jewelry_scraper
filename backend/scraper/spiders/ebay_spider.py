import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import DropItem
from urllib.parse import urlencode
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re
import time
from price_parser import Price
from items import ProductItem
from selenium_utils import setup_driver, save_html_backup, ProxyManager
from logger import log_error, log_critical_error


@dataclass
class ScrapeConfig:
    """Configuration for scraping parameters"""
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    condition: Optional[str] = None
    seller_rating: Optional[float] = None
    min_feedback: Optional[int] = None
    location: Optional[str] = None
    delivery_options: Optional[List[str]] = None
    sort_by: str = "Best Match"


class EnhancedEbaySpider(CrawlSpider):
    name = "ebay"
    allowed_domains = ["ebay.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 16,
        "DOWNLOAD_DELAY": 1.5,
        "COOKIES_ENABLED": False,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
            "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
            "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
        },
        "ITEM_PIPELINES": {
            "pipelines.DuplicatesPipeline": 100,
            "pipelines.PriceValidationPipeline": 200,
            "pipelines.ImagesPipeline": 300,
        },
    }

    def __init__(self, query: str, max_items: int, config: Optional[ScrapeConfig] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.max_items = max_items
        self.config = config or ScrapeConfig()
        self.items_scraped = 0
        self.start_time = datetime.now()
        self.errors = []
        self.proxy_manager = ProxyManager()

        self.start_urls = [self._build_start_url()]

    def _build_start_url(self) -> str:
        """Construct the starting URL with query parameters."""
        params = {
            "_nkw": self.query,
            "_ipg": 100,  # Items per page
            "_sop": self._get_sort_value(self.config.sort_by),
        }

        if self.config.min_price:
            params["_udlo"] = self.config.min_price
        if self.config.max_price:
            params["_udhi"] = self.config.max_price
        if self.config.condition:
            params["LH_ItemCondition"] = self._get_condition_value(self.config.condition)

        return f"https://www.ebay.com/sch/i.html?{urlencode(params)}"

    def _get_sort_value(self, sort_by: str) -> int:
        """Map sorting options to eBay's values."""
        sort_mapping = {
            "Best Match": 12,
            "Price + Shipping: Lowest First": 15,
            "Price + Shipping: Highest First": 16,
            "Time: Newly Listed": 10,
            "Time: Ending Soonest": 1,
        }
        return sort_mapping.get(sort_by, 12)

    def _get_condition_value(self, condition: str) -> Optional[int]:
        """Map item conditions to eBay's numerical values."""
        condition_mapping = {
            "New": 1000,
            "Used": 3000,
            "For Parts or Not Working": 7000,
        }
        return condition_mapping.get(condition)

    def start_requests(self):
        """Send initial requests using rotating proxies."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                dont_filter=True,
                meta={"proxy": self.proxy_manager.get_next_proxy()},
            )

    def parse(self, response):
        """Parse the search results page."""
        if response.status == 429:
            retry_after = response.headers.get("Retry-After", 60)
            time.sleep(int(retry_after))
            yield response.request.copy()
            return

        if self._is_blocked(response):
            self.log("Blocked by eBay. Retrying with new proxy.")
            yield response.request.copy()
            return

        products = response.css(".s-item")
        if not products:
            self.log("No products found. Saving backup HTML.")
            save_html_backup(response.body, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            return

        for product in products[: self.max_items - self.items_scraped]:
            try:
                item = self._extract_product(product)
                if item and item.get("product_url"):
                    yield response.follow(
                        item["product_url"],
                        callback=self.parse_details,
                        errback=self.handle_error,
                        meta={"item": item, "proxy": self.proxy_manager.get_next_proxy()},
                    )
            except Exception as e:
                self.errors.append(f"Error extracting product: {str(e)}")
                log_error(f"Product extraction error: {str(e)}")

        if self.items_scraped < self.max_items:
            next_page = response.css("a.pagination__next::attr(href)").get()
            if next_page:
                yield response.follow(next_page, callback=self.parse, meta={"proxy": self.proxy_manager.get_next_proxy()})

    def _extract_product(self, product) -> Optional[ProductItem]:
        """Extract product details."""
        try:
            item = ProductItem()
            item["title"] = product.css(".s-item__title::text").get()
            if not item["title"]:
                return None

            price_str = product.css(".s-item__price::text").get()
            price = Price.fromstring(price_str)
            if not price.amount:
                return None
            item["price"] = price.amount
            item["currency"] = price.currency

            item["product_url"] = product.css(".s-item__link::attr(href)").get()
            item["image_urls"] = product.css(".s-item__image-img::attr(src)").getall()
            item["scrape_date"] = datetime.now().isoformat()

            return item
        except Exception as e:
            self.log(f"Error extracting product: {str(e)}")
            return None

    def parse_details(self, response):
        """Parse the product details page."""
        item = response.meta.get("item")
        try:
            item["description"] = self._clean_description(response.css("#desc_wrapper").xpath("string()").get())
            yield item
        except Exception as e:
            log_error(f"Error parsing details: {str(e)}")
            self.errors.append(f"Error parsing details: {str(e)}")

    def _clean_description(self, description: Optional[str]) -> str:
        """Clean and format the product description."""
        if not description:
            return ""
        soup = BeautifulSoup(description, "html.parser")
        return re.sub(r"\s+", " ", soup.get_text()).strip()

    def _is_blocked(self, response) -> bool:
        """Check for blocking indicators."""
        blocked_keywords = ["captcha", "security measure"]
        return any(keyword in response.text.lower() for keyword in blocked_keywords)

    def handle_error(self, failure):
        """Handle request errors."""
        request = failure.request
        log_error(f"Request failed: {failure.value}")
        retries = request.meta.get("retries", 0)
        if retries < 3:
            request.meta["retries"] = retries + 1
            yield request.copy()

    def closed(self, reason):
        """Handle spider closure."""
        duration = datetime.now() - self.start_time
        log_error(f"Spider closed. Reason: {reason}. Duration: {duration}. Items scraped: {self.items_scraped}.")


def run_ebay_spider(query: str, max_items: int, config: Optional[Dict] = None):
    """Run the eBay spider."""
    process = CrawlerProcess(get_project_settings())
    scrape_config = ScrapeConfig(**config) if config else ScrapeConfig()
    process.crawl(EnhancedEbaySpider, query=query, max_items=max_items, config=scrape_config)
    process.start()
