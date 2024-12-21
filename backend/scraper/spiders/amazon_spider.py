# File: /backend/scraper/spiders/amazon_spider.py

from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import json
import re
from .base_spider import JewelrySpiderBase, ScrapingConfig
import logging

class AmazonJewelrySpider(JewelrySpiderBase):
    """Spider for scraping jewelry products from Amazon with anti-bot handling"""
    
    @property
    def platform_name(self) -> str:
        return 'amazon'

    def __init__(self, config: ScrapingConfig = None):
        if not config:
            config = ScrapingConfig(
                request_delay=3.0,  # More conservative delay for Amazon
                max_concurrent_requests=4,
                retry_attempts=5,
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/91.0.4472.124 Safari/537.36'
                )
            )
        super().__init__(config)
        self.search_url = 'https://www.amazon.com/s'
        self.logger = logging.getLogger('AmazonSpider')

    async def search_products(self, query: str, max_items: int = 50) -> List[str]:
        """Get product URLs from search results with pagination"""
        urls = []
        page = 1
        
        while len(urls) < max_items:
            params = {
                'k': query,
                'i': 'jewelry',
                'page': page,
                'ref': 'sr_pg_' + str(page)
            }
            
            search_url = f"{self.search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            content = await self.fetch_page(search_url)
            
            if not content:
                self.logger.warning(f"Failed to fetch search page {page}")
                break
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for anti-bot page
            if 'Robot Check' in soup.get_text():
                self.logger.warning("Hit Amazon anti-bot check")
                await asyncio.sleep(self.config.request_delay * 2)
                continue
                
            # Extract product links
            product_cards = soup.select('div[data-asin]:not([data-asin=""])')
            new_urls = []
            
            for card in product_cards:
                link = card.select_one('a.a-link-normal[href*="/dp/"]')
                if link and (href := link.get('href')):
                    # Extract ASIN and build full URL
                    asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                    if asin_match:
                        product_url = f"https://www.amazon.com/dp/{asin_match.group(1)}"
                        new_urls.append(product_url)
            
            if not new_urls:
                break
                
            urls.extend(new_urls)
            page += 1
            await asyncio.sleep(self.config.request_delay)
            
        return urls[:max_items]

    async def extract_title(self, content: str) -> Optional[str]:
        """Extract product title"""
        soup = BeautifulSoup(content, 'html.parser')
        title_elem = soup.select_one('#productTitle')
        return title_elem.get_text().strip() if title_elem else None

    async def extract_price_text(self, content: str) -> Optional[str]:
        """Extract price text handling various price element formats"""
        soup = BeautifulSoup(content, 'html.parser')
        price_selectors = [
            'span.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price[data-a-color="price"] .a-offscreen'
        ]
        
        for selector in price_selectors:
            if price_elem := soup.select_one(selector):
                return price_elem.get_text().strip()
        
        return None

    async def extract_description(self, content: str) -> Optional[str]:
        """Extract product description from multiple possible locations"""
        soup = BeautifulSoup(content, 'html.parser')
        description = []
        
        # Feature bullets
        feature_list = soup.select('#feature-bullets li:not(.aok-hidden) span')
        if feature_list:
            bullets = [item.get_text().strip() for item in feature_list]
            description.extend(bullets)
        
        # Product description
        desc_elem = soup.select_one('#productDescription')
        if desc_elem:
            description.append(desc_elem.get_text().strip())
            
        # Enhanced product description (A+ content)
        enhanced_desc = soup.select('.aplus-v2 p')
        if enhanced_desc:
            enhanced_text = [elem.get_text().strip() for elem in enhanced_desc]
            description.extend(enhanced_text)
            
        return '\n\n'.join(filter(None, description)) if description else None

    async def extract_images(self, content: str) -> List[str]:
        """Extract product images including variants"""
        soup = BeautifulSoup(content, 'html.parser')
        images = []
        
        # Try to extract from image gallery data
        scripts = soup.find_all('script', type='text/javascript')
        for script in scripts:
            if 'ImageBlockATF' in script.text:
                try:
                    # Extract JSON data
                    json_match = re.search(r'var data = ({.*?});', script.text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        if 'colorImages' in data:
                            for variant in data['colorImages'].values():
                                for img in variant:
                                    if 'large' in img:
                                        images.append(img['large'])
                except json.JSONDecodeError:
                    continue
        
        # Fallback to direct image extraction
        if not images:
            img_elements = soup.select('#altImages img[src], #imageBlock img[src]')
            images = [img['src'] for img in img_elements if 'sprite' not in img['src']]
            
            # Convert to high-resolution versions
            images = [re.sub(r'._AC_.*?\.', '._AC_SL1500.', img) for img in images]
        
        return list(dict.fromkeys(images))  # Remove duplicates

    async def extract_specifications(self, content: str) -> Dict[str, Any]:
        """Extract product specifications and details"""
        soup = BeautifulSoup(content, 'html.parser')
        specs = {}
        
        # Product details table
        details_table = soup.select('#productDetails_detailBullets_sections1 tr')
        for row in details_table:
            label = row.select_one('th')
            value = row.select_one('td')
            if label and value:
                key = label.get_text().strip().lower()
                val = value.get_text().strip()
                specs[key] = val
        
        # Technical details
        tech_section = soup.select('#technicalSpecifications_section_1 tr')
        for row in tech_section:
            label = row.select_one('.label')
            value = row.select_one('.value')
            if label and value:
                key = label.get_text().strip().lower()
                val = value.get_text().strip()
                specs[key] = val
                
        return specs

    async def scrape_query(self, query: str, max_items: int = 50) -> List[Dict[str, Any]]:
        """Main method to scrape products based on search query"""
        results = []
        
        try:
            product_urls = await self.search_products(query, max_items)
            self.logger.info(f"Found {len(product_urls)} products to scrape")
            
            for url in product_urls:
                try:
                    if product := await self.scrape_product(url):
                        results.append(product.__dict__)
                    await asyncio.sleep(self.config.request_delay)
                except Exception as e:
                    self.logger.error(f"Error scraping product {url}: {str(e)}")
                    
            self.logger.info(f"Successfully scraped {len(results)} products")
            
        except Exception as e:
            self.logger.error(f"Error during scraping query: {str(e)}")
            
        return results