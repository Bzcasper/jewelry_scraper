import pytest
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from backend.scraper.spiders.ebay_spider import EbaySpider
from backend.scraper.spiders.amazon_spider import AmazonSpider

@pytest.fixture(scope='module')
def crawler():
    process = CrawlerProcess(get_project_settings())
    return process

def test_ebay_spider(capsys, crawler):
    crawler.crawl(EbaySpider, query='gold ring', max_items=5)
    crawler.start()
    captured = capsys.readouterr()
    assert 'gold ring' in captured.out or 'gold ring' in captured.err

def test_amazon_spider(capsys, crawler):
    crawler.crawl(AmazonSpider, query='silver necklace', max_items=5)
    crawler.start()
    captured = capsys.readouterr()
    assert 'silver necklace' in captured.out or 'silver necklace' in captured.err
