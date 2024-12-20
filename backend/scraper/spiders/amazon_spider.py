import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import CrawlSpider
from scrapy.exceptions import DropItem
from items import ProductItem
from logger import log_error, log_critical_error
from typing import Optional, Dict, List
from datetime import datetime
from price_parser import Price
from urllib.parse import urlencode
import json
from bs4 import BeautifulSoup


@dataclass
class AmazonScrapingConfig:
    """Configuration for Amazon scraping parameters"""
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    prime_only: bool = False
    min_rating: Optional[float] = None
    sort_by: str = "featured"
    department: Optional[str] = None
    shipping_options: Optional[List[str]] = None


class EnhancedAmazonSpider(CrawlSpider):
    name = "amazon"
    allowed_domains = ["amazon.com"]
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 2.5,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
        }
    }

    def __init__(self, query: str, max_items: int, config: Optional[AmazonScrapingConfig] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.max_items = max_items
        self.config = config or AmazonScrapingConfig()
        self.items_scraped = 0
        self.start_time = datetime.now()
        self.errors = []
        self.seen_asins = set()

        # Build search URL with filters
        self.start_urls = [f"https://www.amazon.com/s?{urlencode(self._build_search_params())}"]

    def _build_search_params(self) -> Dict[str, str]:
        """Build search parameters with filters"""
        params = {'k': self.query, 'ref': 'nb_sb_noss'}

        if self.config.min_price or self.config.max_price:
            price_filter = []
            if self.config.min_price:
                price_filter.append(f"p_{int(self.config.min_price)}-")
            if self.config.max_price:
                price_filter.append(f"-p_{int(self.config.max_price)}")
            params['rh'] = ''.join(price_filter)

        if self.config.prime_only:
            params['prime'] = '1'

        if self.config.sort_by:
            sort_mapping = {
                "featured": "",
                "price_low": "price-asc-rank",
                "price_high": "price-desc-rank",
                "rating": "review-rank",
                "newest": "date-desc-rank"
            }
            params['s'] = sort_mapping.get(self.config.sort_by, "")

        return params

    def start_requests(self):
        """Initialize requests"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                dont_filter=True,
                meta={'handle_httpstatus_list': [403, 429]}
            )

    def parse(self, response):
        """Parse search results page"""
        if self._is_blocked(response):
            self.logger.warning("Blocked by Amazon, retrying with proxy.")
            yield response.request.copy()
            return

        products = response.css(".s-result-item[data-asin]")
        if not products:
            self.logger.warning("No products found, possible page structure change.")
            return

        for product in products:
            if self.items_scraped >= self.max_items:
                break

            asin = product.attrib.get('data-asin')
            if asin and asin not in self.seen_asins:
                self.seen_asins.add(asin)
                item = self._extract_product(product)
                if item:
                    details_url = item['product_url']
                    yield response.follow(details_url, callback=self.parse_details, meta={'item': item})

        next_page = response.css('.s-pagination-next::attr(href)').get()
        if next_page and self.items_scraped < self.max_items:
            yield response.follow(next_page, callback=self.parse)

    def _extract_product(self, product) -> Optional[ProductItem]:
        """Extract product information"""
        try:
            item = ProductItem()
            item['asin'] = product.attrib.get('data-asin')
            item['title'] = product.css("h2 .a-link-normal span::text").get()
            price_elem = product.css(".a-price span.a-offscreen::text").get()
            if price_elem:
                price = Price.fromstring(price_elem)
                item['price'] = price.amount
                item['currency'] = price.currency
            item['product_url'] = f"https://www.amazon.com/dp/{item['asin']}"
            item['image_urls'] = product.css('.s-image::attr(src)').getall()
            item['scrape_date'] = datetime.now().isoformat()
            return item if self._validate_item(item) else None
        except Exception as e:
            self.logger.error(f"Error extracting product: {str(e)}")
            return None

    def parse_details(self, response):
        """Parse product details"""
        item = response.meta['item']
        try:
            item['description'] = response.css('#productDescription').xpath('string()').get()
            yield item
        except Exception as e:
            self.logger.error(f"Error parsing details: {str(e)}")

    def _validate_item(self, item: ProductItem) -> bool:
        """Validate required fields"""
        return all(item.get(field) for field in ['title', 'price', 'product_url'])

    def _is_blocked(self, response) -> bool:
        """Check if blocked"""
        return "Robot Check" in response.text or "captcha" in response.text

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.value}")
        self.errors.append(failure.value)

    def closed(self, reason):
        """Log scraping summary"""
        duration = datetime.now() - self.start_time
        self.logger.info(f"Spider closed. Scraped {self.items_scraped}/{self.max_items} items in {duration}.")

