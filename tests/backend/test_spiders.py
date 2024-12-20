import pytest
from unittest.mock import Mock, patch
import asyncio
from scraper.spiders.ebay_spider import EbayJewelrySpider
from scraper.spiders.amazon_spider import AmazonJewelrySpider
from scraper.extractors.product_extractor import ProductExtractor

@pytest.fixture
def mock_response():
    """Mock scrapy response"""
    response = Mock()
    response.url = "https://example.com"
    response.text = "<html><body></body></html>"
    return response

@pytest.fixture
def product_extractor():
    """Product extractor instance"""
    return ProductExtractor()

class TestEbaySpider:
    @pytest.mark.asyncio
    async def test_initialization(self):
        spider = EbayJewelrySpider(query="gold ring", max_items=50)
        assert spider.query == "gold ring"
        assert spider.max_items == 50
        assert "ebay.com" in spider.allowed_domains

    @pytest.mark.asyncio
    async def test_parse_product(self, mock_response):
        spider = EbayJewelrySpider(query="gold ring", max_items=50)
        mock_response.css = Mock(return_value=[
            Mock(get=Mock(return_value="Test Product")),
            Mock(get=Mock(return_value="$100.00"))
        ])
        
        async for item in spider.parse(mock_response):
            assert item['title'] == "Test Product"
            assert "$100.00" in str(item['price'])

    @pytest.mark.asyncio
    async def test_extract_price(self, product_extractor):
        price_text = "$99.99"
        result = product_extractor._extract_price(price_text)
        assert result == 99.99

class TestAmazonSpider:
    @pytest.mark.asyncio
    async def test_initialization(self):
        spider = AmazonJewelrySpider(query="silver necklace", max_items=30)
        assert spider.query == "silver necklace"
        assert spider.max_items == 30
        assert "amazon.com" in spider.allowed_domains

    @pytest.mark.asyncio
    async def test_parse_product(self, mock_response):
        spider = AmazonJewelrySpider(query="silver necklace", max_items=30)
        mock_response.css = Mock(return_value=[
            Mock(get=Mock(return_value="Test Product")),
            Mock(get=Mock(return_value="$199.99"))
        ])
        
        async for item in spider.parse(mock_response):
            assert item['title'] == "Test Product"
            assert "$199.99" in str(item['price'])