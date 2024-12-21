from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
from .base_spider import JewelrySpiderBase, ScrapingConfig

class EbayJewelrySpider(JewelrySpiderBase):
    """Spider for scraping jewelry products from eBay"""
    
    @property
    def platform_name(self) -> str:
        return 'ebay'

    def __init__(self, config: ScrapingConfig = None):
        super().__init__(config)
        self.search_url = 'https://www.ebay.com/sch/i.html'

    async def search_products(self, query: str, max_items: int = 50) -> List[str]:
        """Get product URLs from search results"""
        urls = []
        page = 1
        
        while len(urls) < max_items:
            params = {
                '_nkw': query,
                '_sacat': '281',  # Jewelry category
                '_pgn': page
            }
            
            search_url = f"{self.search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            content = await self.fetch_page(search_url)
            
            if not content:
                break
                
            soup = BeautifulSoup(content, 'html.parser')
            product_links = soup.select('h3.s-item__title a')
            
            if not product_links:
                break
                
            urls.extend([link['href'] for link in product_links])
            page += 1
            
            await asyncio.sleep(self.config.request_delay)
        
        return urls[:max_items]

    async def extract_title(self, content: str) -> Optional[str]:
        """Extract product title"""
        soup = BeautifulSoup(content, 'html.parser')
        title_elem = soup.select_one('h1.x-item-title__mainTitle')
        return title_elem.get_text().strip() if title_elem else None

    async def extract_price_text(self, content: str) -> Optional[str]:
        """Extract price text"""
        soup = BeautifulSoup(content, 'html.parser')
        price_elem = soup.select_one('div.x-price-primary span.ux-textspans')
        return price_elem.get_text().strip() if price_elem else None

    async def extract_description(self, content: str) -> Optional[str]:
        """Extract product description"""
        soup = BeautifulSoup(content, 'html.parser')
        desc_elem = soup.select_one('div.x-item-description')
        if not desc_elem:
            return None
            
        # Clean description text
        desc_text = desc_elem.get_text(' ', strip=True)
        desc_text = re.sub(r'\s+', ' ', desc_text)
        return desc_text

    async def extract_images(self, content: str) -> List[str]:
        """Extract product images"""
        soup = BeautifulSoup(content, 'html.parser')
        image_elements = soup.select('div.ux-image-carousel-item img.ux-image-carousel__item')
        
        images = []
        for img in image_elements:
            src = img.get('src') or img.get('data-src')
            if src:
                # Convert to high-resolution version if available
                src = re.sub(r's-l\d+', 's-l1600', src)
                images.append(src)
                
        return images

    async def extract_specifications(self, content: str) -> Dict[str, Any]:
        """Extract product specifications"""
        soup = BeautifulSoup(content, 'html.parser')
        specs = {}
        
        # Item specifics section
        spec_table = soup.select('div.x-item-specifics div.ux-layout-section__row')
        
        for row in spec_table:
            label = row.select_one('div.ux-labels-values__labels')
            value = row.select_one('div.ux-labels-values__values')
            
            if label and value:
                key = label.get_text().strip().lower()
                val = value.get_text().strip()
                specs[key] = val
                
        return specs

    async def scrape_query(self, query: str, max_items: int = 50) -> List[Dict[str, Any]]:
        """Main method to scrape products based on search query"""
        results = []
        
        # Get product URLs from search
        product_urls = await self.search_products(query, max_items)
        
        # Scrape individual products
        for url in product_urls:
            try:
                if product := await self.scrape_product(url):
                    results.append(product.__dict__)
                await asyncio.sleep(self.config.request_delay)
            except Exception as e:
                self.logger.error(f"Error scraping product {url}: {str(e)}")
                
        return results