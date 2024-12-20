import pytest from scrapy.crawler import CrawlerProcess from scrapy.utils.project import get_project_settings from scraper.spiders.ebay_spider import EbaySpider from scraper.spiders.amazon_spider import AmazonSpider

@pytest.fixture(scope='module') def crawler(): process = CrawlerProcess(get_project_settings()) yield process process.stop()

def test_ebay_spider(crawler): process = crawler process.crawl(EbaySpider, query="gold ring", max_items=10) process.start() # Assertions to verify scraped items # Example: # assert len(scraper.items) == 10 # assert all('price' in item for item in scraper.items)

def test_amazon_spider(crawler): process = crawler process.crawl(AmazonSpider, query="silver necklace", max_items=10) process.start() # Assertions to verify scraped items # Example: # assert len(scraper.items) == 10 # assert all('price' in item for item in scraper.items) 
