import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from items import ProductItem
from selenium_utils import setup_driver, save_html_backup, ProxyManager
from logger import log_error, log_critical_error

class AmazonSpider(scrapy.Spider):
    name = "amazon"
    allowed_domains = ["amazon.com"]

    def __init__(self, query, max_items, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.query = query
        self.max_items = max_items
        self.start_urls = [f"https://www.amazon.com/s?k={query.replace(' ', '+')}"]

    def parse(self, response):
        products = response.css(".s-main-slot .s-result-item")[:self.max_items]
        for product in products:
            item = ProductItem()
            item['title'] = product.css("h2 .a-link-normal span::text").get()
            item['price'] = product.css(".a-price span.a-offscreen::text").get()
            item['product_url'] = response.urljoin(product.css("h2 .a-link-normal::attr(href)").get())
            item['image_urls'] = [product.css(".s-image::attr(src)").get()]
            item['category'] = getattr(self, "category", "jewelry")

            # Follow product URL for additional details
            details_url = item['product_url']
            if details_url:
                yield response.follow(details_url, self.parse_details, meta={"item": item})
            else:
                yield item

    def parse_details(self, response):
        item = response.meta['item']
        item['description'] = response.css("#feature-bullets").xpath("string()").get()
        yield item

def run_amazon_spider(query, max_items):
    process = CrawlerProcess(get_project_settings())
    spider = AmazonSpider(query=query, max_items=max_items)
    process.crawl(spider)
    process.start()
    return spider.items
