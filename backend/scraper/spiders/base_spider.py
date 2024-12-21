from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import aiohttp
import logging
from price_parser import Price
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ScrapingConfig:
    """Configuration for scraping settings"""
    max_concurrent_requests: int = 8
    request_delay: float = 2.0
    retry_attempts: int = 3
    timeout: int = 30
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

@dataclass
class ScrapingResult:
    """Structured container for scraped product data"""
    title: str
    price: float
    currency: str
    url: str
    platform: str
    description: Optional[str] = None
    images: List[str] = None
    specifications: Dict[str, Any] = None
    date_scraped: datetime = None

class JewelrySpiderBase(ABC):
    """Base spider with shared scraping functionality"""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = {'requests': 0, 'success': 0, 'errors': 0}

    async def __aenter__(self):
        headers = {'User-Agent': self.config.user_agent}
        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page with retry logic"""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.semaphore:
                    async with self.session.get(url, timeout=self.config.timeout) as response:
                        if response.status == 200:
                            self.stats['success'] += 1
                            return await response.text()
                        
                        if response.status == 429:  # Rate limited
                            await asyncio.sleep(self.config.request_delay * (attempt + 1))
                            continue
                            
            except Exception as e:
                self.logger.error(f"Error fetching {url} (attempt {attempt + 1}): {str(e)}")
                self.stats['errors'] += 1
                await asyncio.sleep(self.config.request_delay)
        
        return None

    @staticmethod
    def extract_price(price_text: str) -> tuple[Optional[float], str]:
        """Extract price and currency from text"""
        if not price_text:
            return None, 'USD'
            
        price = Price.fromstring(price_text)
        return price.amount, price.currency or 'USD'

    async def scrape_product(self, url: str) -> Optional[ScrapingResult]:
        """Scrape individual product with shared logic"""
        content = await self.fetch_page(url)
        if not content:
            return None

        try:
            # Extract common fields
            title = await self.extract_title(content)
            price_text = await self.extract_price_text(content)
            price_amount, currency = self.extract_price(price_text)
            
            if not all([title, price_amount]):
                return None

            return ScrapingResult(
                title=title,
                price=price_amount,
                currency=currency,
                url=url,
                platform=self.platform_name,
                description=await self.extract_description(content),
                images=await self.extract_images(content),
                specifications=await self.extract_specifications(content),
                date_scraped=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
            return None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier"""
        pass

    @abstractmethod
    async def extract_title(self, content: str) -> Optional[str]:
        """Extract product title"""
        pass

    @abstractmethod
    async def extract_price_text(self, content: str) -> Optional[str]:
        """Extract price text"""
        pass

    @abstractmethod
    async def extract_description(self, content: str) -> Optional[str]:
        """Extract product description"""
        pass

    @abstractmethod
    async def extract_images(self, content: str) -> List[str]:
        """Extract product images"""
        pass

    @abstractmethod
    async def extract_specifications(self, content: str) -> Dict[str, Any]:
        """Extract product specifications"""
        pass