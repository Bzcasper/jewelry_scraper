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
import json
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass

@dataclass
class AmazonScrapingConfig:
    """Configuration for Amazon scraping parameters"""
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    prime_only: bool = False
    min_rating: Optional[float] = None
    sort_by: str = "featured"
    department: Optional[str] = None
    shipping_options: List[str] = None

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
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
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
        params = self._build_search_params()
        self.start_urls = [f"https://www.amazon.com/s?{urlencode(params)}"]

    def _build_search_params(self) -> Dict[str, str]:
        """Build search parameters with filters"""
        params = {
            'k': self.query,
            'ref': 'nb_sb_noss',
            'page': '1'
        }

        if self.config.min_price or self.config.max_price:
            price_range = []
            if self.config.min_price:
                price_range.append(f"p_{int(self.config.min_price)}-")
            if self.config.max_price:
                price_range.append(f"-p_{int(self.config.max_price)}")
            params['rh'] = ''.join(price_range)

        if self.config.prime_only:
            params['prime'] = '1'

        if self.config.min_rating:
            params['rh'] = f"p_72%3A2661618011"  # 4 stars & up

        if self.config.sort_by:
            sort_mapping = {
                "featured": "",
                "price_low": "price-asc-rank",
                "price_high": "price-desc-rank",
                "rating": "review-rank",
                "newest": "date-desc-rank"
            }
            if sort_value := sort_mapping.get(self.config.sort_by):
                params['s'] = sort_value

        return params

    def start_requests(self):
        """Initialize requests with cookies and headers"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                cookies={'session-id': 'new'},
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                meta={
                    'handle_httpstatus_list': [404, 403, 429],
                    'max_retry_times': 5
                },
                dont_filter=True
            )

    def parse(self, response):
        """Parse search results page"""
        # Check for captcha/blocking
        if self._is_blocked(response):
            self.logger.warning("Detected blocking, rotating proxy and retrying")
            yield response.request.replace(dont_filter=True)
            return

        # Extract products
        products = response.css(".s-result-item[data-asin]")
        if not products:
            self.logger.warning("No products found, possible page structure change")
            save_html_backup(response.body.decode(), f"amazon_no_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            return

        for product in products:
            if self.items_scraped >= self.max_items:
                return

            try:
                asin = product.attrib.get('data-asin')
                if not asin or asin in self.seen_asins:
                    continue

                self.seen_asins.add(asin)
                item = self._extract_product(product)
                
                if item:
                    details_url = item['product_url']
                    if details_url:
                        yield response.follow(
                            details_url,
                            callback=self.parse_details,
                            errback=self.handle_error,
                            meta={'item': item}
                        )
            except Exception as e:
                self.errors.append(f"Error extracting product: {str(e)}")
                self.logger.error(f"Product extraction error: {str(e)}")

        # Handle pagination
        if self.items_scraped < self.max_items:
            next_page = response.css('.s-pagination-next::attr(href)').get()
            if next_page:
                yield response.follow(
                    next_page,
                    callback=self.parse,
                    errback=self.handle_error
                )

    def _extract_product(self, product) -> Optional[ProductItem]:
        """Extract product information with validation"""
        try:
            item = ProductItem()

            # Basic information
            item['asin'] = product.attrib.get('data-asin')
            item['title'] = self._clean_text(product.css("h2 .a-link-normal span::text").get())
            
            # Price handling
            price_elem = product.css(".a-price span.a-offscreen::text").get()
            if price_elem:
                price = Price.fromstring(price_elem)
                item['price'] = price.amount
                item['currency'] = price.currency

            # URLs
            item['product_url'] = f"https://www.amazon.com/dp/{item['asin']}"
            item['image_urls'] = self._extract_images(product)
            
            # Additional fields
            item['category'] = self.config.department or "jewelry"
            item['scrape_date'] = datetime.now().isoformat()
            
            # Ratings and reviews
            item['rating'] = self._extract_rating(product)
            item['review_count'] = self._extract_review_count(product)
            
            # Prime and shipping
            item['prime_eligible'] = bool(product.css('.s-prime'))
            item['shipping_info'] = self._clean_text(product.css('.s-prime::text').get())

            return item if self._validate_item(item) else None

        except Exception as e:
            self.logger.error(f"Error extracting product data: {str(e)}")
            return None

    def parse_details(self, response):
        """Parse product details page"""
        item = response.meta['item']
        
        try:
            # Extract description
            item['description'] = self._extract_description(response)
            
            # Product features
            features = response.css('#feature-bullets li span::text').getall()
            item['features'] = [self._clean_text(f) for f in features if f.strip()]
            
            # Technical details
            tech_details = {}
            for row in response.css('table#productDetails_techSpec_section_1 tr'):
                key = self._clean_text(row.css('th::text').get())
                value = self._clean_text(row.css('td::text').get())
                if key and value:
                    tech_details[key] = value
            item['technical_details'] = tech_details
            
            # Seller information
            item['seller'] = {
                'name': response.css('#merchant-info::text').get(),
                'rating': response.css('#seller-rating .a-text-bold::text').get()
            }

            self.items_scraped += 1
            yield item

        except Exception as e:
            self.errors.append(f"Error parsing details: {str(e)}")
            self.logger.error(f"Details parsing error: {str(e)}")

    def _extract_description(self, response) -> str:
        """Extract and clean product description"""
        description = response.css('#feature-bullets').xpath('string()').get()
        if not description:
            description = response.css('#productDescription').xpath('string()').get()
        return self._clean_text(description)

    def _extract_images(self, product) -> List[str]:
        """Extract all product images"""
        images = []
        main_image = product.css('.s-image::attr(src)').get()
        if main_image:
            images.append(main_image)
        variant_images = product.css('script:contains("imageGalleryData")::text').get()
        if variant_images:
            try:
                data = json.loads(variant_images)
                images.extend([img['large'] for img in data if 'large' in img])
            except json.JSONDecodeError:
                pass
        return list(set(images))  # Remove duplicates

    def _clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.strip().split())

    def _validate_item(self, item: ProductItem) -> bool:
        """Validate required item fields"""
        required_fields = ['title', 'price', 'product_url']
        return all(item.get(field) for field in required_fields)

    def _is_blocked(self, response) -> bool:
        """Check if we're being blocked by Amazon"""
        blocked_indicators = [
            "Robot Check",
            "Sorry, we just need to make sure you're not a robot",
            "Enter the characters you see below",
            "To discuss automated access to Amazon data please contact"
        ]
        page_text = ' '.join(response.css('body::text').getall()).lower()
        return any(indicator.lower() in page_text for indicator in blocked_indicators)

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.value}")
        self.errors.append(str(failure.value))

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
        self.logger.info(f"Spider closed. Report: {report}")

def run_amazon_spider(query: str, max_items: int, config: Optional[Dict] = None):
    """Run the spider with enhanced configuration"""
    try:
        process = CrawlerProcess(get_project_settings())
        scrape_config = AmazonScrapingConfig(**config) if config else AmazonScrapingConfig()
        spider = EnhancedAmazonSpider(query=query, max_items=max_items, config=scrape_config)
        process.crawl(spider)
        process.start()
        return spider.items
    except Exception as e:
        log_critical_error(f"Failed to run spider: {str(e)}")
        raise