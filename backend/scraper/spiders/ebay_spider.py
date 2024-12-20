import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import DropItem
from items import ProductItem
from selenium_utils import setup_driver, save_html_backup, ProxyManager
from logger import log_error, log_critical_error
from typing import Optional, Dict, List
from datetime import datetime
import re
from price_parser import Price
from urllib.parse import urlencode
import random
import time
from dataclasses import dataclass
from bs4 import BeautifulSoup

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
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1.5,
        'COOKIES_ENABLED': False,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
        },
        'ITEM_PIPELINES': {
            'pipelines.DuplicatesPipeline': 100,
            'pipelines.PriceValidationPipeline': 200,
            'pipelines.ImagesPipeline': 300,
        }
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
        
        # Build the start URL with filters
        params = {
            '_nkw': query,
            '_ipg': 100,  # Items per page
            '_sop': self._get_sort_value(self.config.sort_by)
        }
        
        if self.config.min_price:
            params['_udlo'] = self.config.min_price
        if self.config.max_price:
            params['_udhi'] = self.config.max_price
        if self.config.condition:
            params['LH_ItemCondition'] = self._get_condition_value(self.config.condition)
            
        self.start_urls = [f"https://www.ebay.com/sch/i.html?{urlencode(params)}"]

    def _get_sort_value(self, sort_by: str) -> int:
        """Map sort options to eBay's numerical values"""
        sort_mapping = {
            "Best Match": 12,
            "Price + Shipping: Lowest First": 15,
            "Price + Shipping: Highest First": 16,
            "Time: Newly Listed": 10,
            "Time: Ending Soonest": 1
        }
        return sort_mapping.get(sort_by, 12)

    def _get_condition_value(self, condition: str) -> int:
        """Map condition options to eBay's numerical values"""
        condition_mapping = {
            "New": 1000,
            "Used": 3000,
            "For Parts or Not Working": 7000
        }
        return condition_mapping.get(condition)

    def start_requests(self):
        """Initialize requests with rotating user agents and proxies"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                dont_filter=True,
                meta={
                    'proxy': self.proxy_manager.get_next_proxy(),
                    'max_retries': 3,
                    'dont_redirect': True,
                    'handle_httpstatus_list': [404, 403, 429]
                }
            )

    def parse(self, response):
        """Parse the search results page"""
        if response.status == 429:
            # Handle rate limiting
            retry_after = response.headers.get('Retry-After', 60)
            time.sleep(int(retry_after))
            yield response.request.copy()
            return

        # Check if we're blocked
        if self._is_blocked(response):
            self.log("Detected blocking, rotating proxy and retrying")
            yield response.request.copy()
            return

        # Extract products
        products = response.css(".s-item")
        if not products:
            self.log("No products found, possible page structure change")
            save_html_backup(response.body, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            return

        for product in products[:self.max_items - self.items_scraped]:
            try:
                item = self._extract_product(product)
                if item:
                    # Follow product URL for additional details
                    details_url = item['product_url']
                    if details_url:
                        yield response.follow(
                            details_url,
                            callback=self.parse_details,
                            errback=self.handle_error,
                            meta={
                                "item": item,
                                "proxy": self.proxy_manager.get_next_proxy()
                            }
                        )
            except Exception as e:
                self.errors.append(f"Error extracting product: {str(e)}")
                log_error(f"Product extraction error: {str(e)}")

        # Handle pagination if we need more items
        if self.items_scraped < self.max_items:
            next_page = response.css('a.pagination__next::attr(href)').get()
            if next_page:
                yield response.follow(
                    next_page,
                    callback=self.parse,
                    meta={'proxy': self.proxy_manager.get_next_proxy()}
                )

    def _extract_product(self, product) -> Optional[ProductItem]:
        """Extract product information with validation"""
        try:
            item = ProductItem()
            
            # Basic information
            item['title'] = product.css(".s-item__title::text").get()
            if not item['title']:
                return None

            # Price extraction and validation
            price_str = product.css(".s-item__price::text").get()
            price = Price.fromstring(price_str)
            if not price.amount:
                return None
            item['price'] = price.amount
            item['currency'] = price.currency

            # URL and image
            item['product_url'] = product.css(".s-item__link::attr(href)").get()
            item['image_urls'] = [url.strip() for url in product.css(".s-item__image-img::attr(src)").getall() if url]
            
            # Additional fields
            item['category'] = getattr(self, "category", "jewelry")
            item['scrape_date'] = datetime.now().isoformat()
            
            # Seller information
            item['seller'] = {
                'name': product.css(".s-item__seller-info-text::text").get(),
                'feedback_score': product.css(".s-item__seller-info-text span::text").get(),
                'positive_feedback': product.css(".s-item__seller-info-text span::text").get()
            }

            # Shipping information
            item['shipping'] = {
                'cost': product.css(".s-item__shipping::text").get(),
                'location': product.css(".s-item__location::text").get(),
                'delivery_estimate': product.css(".s-item__delivery-estimate::text").get()
            }

            return item
        except Exception as e:
            self.log(f"Error extracting product: {str(e)}")
            return None

    def parse_details(self, response):
        """Parse detailed product page with enhanced information"""
        item = response.meta['item']
        
        try:
            # Description
            item['description'] = self._clean_description(
                response.css("#desc_wrapper").xpath("string()").get()
            )

            # Specifications
            specs = {}
            for row in response.css("div.ux-labels-values__labels-content"):
                label = row.css(".ux-labels-values__labels::text").get()
                value = row.css(".ux-labels-values__values::text").get()
                if label and value:
                    specs[label.strip()] = value.strip()
            item['specifications'] = specs

            # Additional images
            additional_images = response.css("#vi_main_img_fs img::attr(src)").getall()
            if additional_images:
                item['image_urls'].extend(additional_images)

            # Review information
            item['reviews'] = {
                'rating': response.css(".reviews-star-rating::attr(title)").get(),
                'count': response.css(".reviews-total-reviews::text").get()
            }

            self.items_scraped += 1
            yield item

        except Exception as e:
            self.errors.append(f"Error parsing details: {str(e)}")
            log_error(f"Details parsing error: {str(e)}")

    def _clean_description(self, description: Optional[str]) -> str:
        """Clean and normalize product description"""
        if not description:
            return ""
        # Remove HTML tags
        soup = BeautifulSoup(description, 'html.parser')
        text = soup.get_text()
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _is_blocked(self, response) -> bool:
        """Check if we're being blocked by eBay"""
        blocked_indicators = [
            "blocking_error",
            "Security Measure",
            "blocked",
            "captcha"
        ]
        page_text = response.text.lower()
        return any(indicator in page_text for indicator in blocked_indicators)

    def handle_error(self, failure):
        """Handle request errors"""
        request = failure.request
        error_msg = f"Request failed: {failure.value}"
        self.errors.append(error_msg)
        log_error(error_msg)

        retries = request.meta.get('max_retries', 3)
        if retries > 0:
            request.meta['max_retries'] = retries - 1
            request.meta['proxy'] = self.proxy_manager.get_next_proxy()
            yield request.copy()

    def closed(self, reason):
        """Handle spider closure and generate report"""
        duration = datetime.now() - self.start_time
        report = {
            'query': self.query,
            'items_scraped': self.items_scraped,
            'duration_seconds': duration.total_seconds(),
            'errors': self.errors,
            'success_rate': self.items_scraped / self.max_items if self.max_items > 0 else 0
        }
        log_error(f"Spider closed. Report: {report}")

def run_ebay_spider(query: str, max_items: int, config: Optional[Dict] = None):
    """Run the spider with enhanced configuration"""
    try:
        process = CrawlerProcess(get_project_settings())
        scrape_config = ScrapeConfig(**config) if config else ScrapeConfig()
        spider = EnhancedEbaySpider(query=query, max_items=max_items, config=scrape_config)
        process.crawl(spider)
        process.start()
        return spider.items
    except Exception as e:
        log_critical_error(f"Failed to run spider: {str(e)}")
        raise