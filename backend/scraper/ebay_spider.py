import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from items import ProductItem
from selenium_utils import setup_driver, save_html_backup, ProxyManager
from logger import log_error, log_critical_error

class EbaySpider(scrapy.Spider):
    name = "ebay"
    allowed_domains = ["ebay.com"]

    def __init__(self, query, max_items, *args, **kwargs):
        super(EbaySpider, self).__init__(*args, **kwargs)
        self.query = query
        self.max_items = max_items
        self.start_urls = [f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}"]

    def parse(self, response):
        products = response.css(".s-item")[:self.max_items]
        for product in products:
            item = ProductItem()
            item['title'] = product.css(".s-item__title::text").get()
            item['price'] = product.css(".s-item__price::text").get()
            item['product_url'] = product.css(".s-item__link::attr(href)").get()
            item['image_urls'] = [product.css(".s-item__image-img::attr(src)").get()]
            item['category'] = getattr(self, "category", "jewelry")

            # Follow product URL for additional details
            details_url = item['product_url']
            if details_url:
                yield response.follow(details_url, self.parse_details, meta={"item": item})
            else:
                yield item

    def parse_details(self, response):
        item = response.meta['item']
        item['description'] = response.css("#desc_wrapper").xpath("string()").get()
        yield item

def run_ebay_spider(query, max_items):
    process = CrawlerProcess(get_project_settings())
    spider = EbaySpider(query=query, max_items=max_items)
    process.crawl(spider)
    process.start()
    return spider.items
