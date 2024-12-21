# File: /backend/scraper/middleware.py

from typing import Optional, Dict
import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from datetime import datetime
from .selenium_utils import SeleniumManager
from utils.rate_limiter import AdaptiveRateLimiter
from utils.proxy_manager import ProxyManager

class ScraperMiddleware:
    """Handle request/response processing and resource management"""
    
    def __init__(self):
        self.selenium = SeleniumManager(headless=True)
        self.rate_limiter = AdaptiveRateLimiter()
        self.proxy_manager = ProxyManager()
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None

    async def process_request(self, url: str, platform: str) -> Optional[str]:
        """Process request with rate limiting and proxy rotation"""
        await self.rate_limiter.wait(platform)
        
        try:
            proxy = await self.proxy_manager.get_proxy()
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(
                url,
                proxy=proxy.url if proxy else None,
                timeout=30
            ) as response:
                if response.status == 200:
                    self.rate_limiter.update_success_rate(True)
                    return await response.text()
                    
                if response.status == 403:  # Blocked
                    self.logger.warning(f"Access blocked for {url}")
                    if proxy:
                        self.proxy_manager.report_failure(proxy)
                    self.rate_limiter.update_success_rate(False)
                    return None

        except Exception as e:
            self.logger.error(f"Request failed for {url}: {e}")
            if proxy:
                self.proxy_manager.report_failure(proxy)
            self.rate_limiter.update_success_rate(False)
            return None

    async def process_response(self, html: str, platform: str) -> Optional[Dict]:
        """Process response and extract structured data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for anti-bot measures
            if self._is_blocked(soup, platform):
                self.logger.warning(f"Anti-bot detection on {platform}")
                return None
            
            # Extract structured data
            structured_data = self._extract_structured_data(soup)
            if structured_data:
                return structured_data
            
            return None

        except Exception as e:
            self.logger.error(f"Response processing failed: {e}")
            return None

    def _is_blocked(self, soup: BeautifulSoup, platform: str) -> bool:
        """Check if response indicates blocking"""
        if platform == 'amazon':
            return any(text in soup.get_text().lower() 
                      for text in ['robot', 'captcha', 'verify'])
        elif platform == 'ebay':
            return any(text in soup.get_text().lower() 
                      for text in ['security measure', 'verify'])
        return False

    def _extract_structured_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract structured data from page"""
        try:
            # Try JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') in ['Product', 'Offer']:
                        return data
                except json.JSONDecodeError:
                    continue
            
            return None

        except Exception as e:
            self.logger.error(f"Structured data extraction failed: {e}")
            return None

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None